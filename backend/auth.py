"""Authentication module — SMS code + JWT token.

MVP: mock SMS (fixed code 123456 or printed to console).
Verification codes stored in memory dict with TTL.
Rate limiting: per-IP hourly limit, per-phone lockout after N failures.
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import User

logger = logging.getLogger("autocut.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# In-memory stores (MVP — replace with Redis in production)
# ---------------------------------------------------------------------------

# {phone: {code: str, expires_at: float, created_at: float}}
_verification_codes: Dict[str, dict] = {}

# {phone: {fail_count: int, locked_until: float}}
_login_attempts: Dict[str, dict] = {}

# {ip: [(timestamp, ...)]}
_ip_sms_log: Dict[str, List[float]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_code() -> str:
    """Generate a 6-digit verification code. MVP: always 123456."""
    return "123456"


def _clean_expired_codes():
    """Remove expired verification codes."""
    now = time.time()
    expired = [p for p, v in _verification_codes.items() if v["expires_at"] < now]
    for p in expired:
        del _verification_codes[p]


def _check_ip_rate_limit(ip: str) -> bool:
    """Return True if IP is within rate limit."""
    now = time.time()
    one_hour_ago = now - 3600
    if ip in _ip_sms_log:
        _ip_sms_log[ip] = [t for t in _ip_sms_log[ip] if t > one_hour_ago]
        if len(_ip_sms_log[ip]) >= settings.IP_SMS_HOURLY_LIMIT:
            return False
    return True


def _record_ip_sms(ip: str):
    """Record an SMS send for IP rate limiting."""
    now = time.time()
    if ip not in _ip_sms_log:
        _ip_sms_log[ip] = []
    _ip_sms_log[ip].append(now)


def _check_phone_cooldown(phone: str) -> bool:
    """Return True if phone is past the cooldown period."""
    if phone in _verification_codes:
        created = _verification_codes[phone]["created_at"]
        if time.time() - created < settings.LOGIN_CODE_COOLDOWN_SEC:
            return False
    return True


def _is_locked(phone: str) -> bool:
    """Return True if phone is locked due to too many failed attempts."""
    if phone in _login_attempts:
        info = _login_attempts[phone]
        if info.get("locked_until", 0) > time.time():
            return True
        # Reset if lock has expired
        if info.get("locked_until", 0) <= time.time() and info.get("fail_count", 0) >= settings.LOGIN_MAX_FAIL_ATTEMPTS:
            _login_attempts[phone] = {"fail_count": 0, "locked_until": 0}
    return False


def _record_fail(phone: str):
    """Record a failed login attempt. Lock after N failures."""
    if phone not in _login_attempts:
        _login_attempts[phone] = {"fail_count": 0, "locked_until": 0}
    _login_attempts[phone]["fail_count"] += 1
    if _login_attempts[phone]["fail_count"] >= settings.LOGIN_MAX_FAIL_ATTEMPTS:
        _login_attempts[phone]["locked_until"] = time.time() + settings.LOGIN_LOCKOUT_MIN * 60


def _reset_fail(phone: str):
    """Reset failed attempts after successful login."""
    if phone in _login_attempts:
        del _login_attempts[phone]


def create_jwt(user_id: str, phone: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        "sub": user_id,
        "phone": phone,
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ---------------------------------------------------------------------------
# Dependency: get current user from Authorization header
# ---------------------------------------------------------------------------

def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Return the current user if a valid token is present, else None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = decode_jwt(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload["sub"]).first()
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Return the current user or raise 401."""
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SendCodeRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("请输入正确的 11 位手机号")
        return v


class SendCodeResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    phone: str
    code: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 11 or not v.startswith("1"):
            raise ValueError("请输入正确的 11 位手机号")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("验证码为 6 位数字")
        return v


class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict


class MeResponse(BaseModel):
    id: str
    phone: str
    phone_suffix: str
    free_quota_remaining: int
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/send-code", response_model=SendCodeResponse)
def send_code(body: SendCodeRequest, request: Request):
    """Send a verification code to the given phone number."""
    phone = body.phone
    ip = request.client.host if request.client else "unknown"

    # IP rate limit
    if not _check_ip_rate_limit(ip):
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")

    # Phone cooldown (60s between sends)
    if not _check_phone_cooldown(phone):
        remaining = int(
            settings.LOGIN_CODE_COOLDOWN_SEC
            - (time.time() - _verification_codes[phone]["created_at"])
        )
        raise HTTPException(
            status_code=429,
            detail=f"验证码已发送，请 {remaining} 秒后重试",
        )

    # Generate and store code
    code = _generate_code()
    now = time.time()
    _verification_codes[phone] = {
        "code": code,
        "expires_at": now + settings.LOGIN_CODE_EXPIRE_SEC,
        "created_at": now,
    }
    _record_ip_sms(ip)

    # MVP: print code to console instead of sending SMS
    logger.info(f"[MOCK SMS] Phone: {phone}, Code: {code}")
    print(f"\n{'='*40}")
    print(f"  MOCK SMS — 手机号: {phone}")
    print(f"  验证码: {code}")
    print(f"{'='*40}\n")

    return SendCodeResponse(success=True, message="验证码已发送")


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Verify code and login. Auto-create user on first login."""
    phone = body.phone
    code = body.code

    # Check lockout
    if _is_locked(phone):
        info = _login_attempts.get(phone, {})
        remaining = int(info.get("locked_until", 0) - time.time())
        raise HTTPException(
            status_code=423,
            detail=f"登录失败次数过多，请 {remaining} 秒后再试",
        )

    # Check code exists and not expired
    _clean_expired_codes()
    stored = _verification_codes.get(phone)
    if not stored:
        _record_fail(phone)
        raise HTTPException(status_code=400, detail="验证码已过期或未发送，请重新获取")

    # Verify code
    if stored["code"] != code:
        _record_fail(phone)
        fail_count = _login_attempts.get(phone, {}).get("fail_count", 0)
        remaining_attempts = settings.LOGIN_MAX_FAIL_ATTEMPTS - fail_count
        if remaining_attempts <= 0:
            raise HTTPException(status_code=423, detail=f"登录失败次数过多，请 {settings.LOGIN_LOCKOUT_MIN} 分钟后再试")
        raise HTTPException(status_code=400, detail=f"验证码错误，还剩 {remaining_attempts} 次机会")

    # Code correct — clean up
    del _verification_codes[phone]
    _reset_fail(phone)

    # Find or create user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user = User(
            phone=phone,
            free_quota_remaining=settings.FREE_QUOTA_INITIAL,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created: {user.id} ({phone})")

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate JWT
    token = create_jwt(user.id, user.phone)

    return LoginResponse(
        success=True,
        token=token,
        user={
            "id": user.id,
            "phone": user.phone,
            "phone_suffix": user.phone[-4:],
            "free_quota_remaining": user.free_quota_remaining,
        },
    )


@router.post("/logout")
def logout():
    """Logout — MVP: client-side token removal. Server-side is a no-op."""
    return {"success": True, "message": "已退出登录"}


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    """Get current user info."""
    return MeResponse(
        id=user.id,
        phone=user.phone,
        phone_suffix=user.phone[-4:],
        free_quota_remaining=user.free_quota_remaining,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )
