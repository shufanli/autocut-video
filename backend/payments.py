"""Payments router -- create payment orders, query status, mock callback.

MVP: mock payment flow (auto-completes after frontend "confirms").
Supports per-video payment at 9.9 yuan (990 cents).
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from auth import get_current_user
from models import User, Task, Payment

logger = logging.getLogger("autocut.payments")

router = APIRouter(prefix="/api/payments", tags=["payments"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CreatePaymentRequest(BaseModel):
    task_id: str
    payment_channel: str  # "alipay" or "wechat"


class CreatePaymentResponse(BaseModel):
    payment_id: str
    amount_cents: int
    amount_display: str
    payment_channel: str
    payment_status: str
    qr_code_url: str  # MVP: mock URL


class PaymentStatusResponse(BaseModel):
    payment_id: str
    payment_status: str
    task_id: str
    paid_at: Optional[str] = None


class MockPayRequest(BaseModel):
    """Mock payment confirmation -- simulates user completing payment."""
    pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/create", response_model=CreatePaymentResponse)
def create_payment(
    body: CreatePaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new payment order for a completed task.

    Validates:
    - Task exists and belongs to user
    - Task is completed
    - No existing successful payment for this task
    """
    # Validate payment channel
    if body.payment_channel not in ("alipay", "wechat"):
        raise HTTPException(status_code=400, detail="不支持的支付方式")

    # Validate task
    task = db.query(Task).filter(
        Task.id == body.task_id, Task.user_id == user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成(当前状态: {task.status})",
        )

    # Check if there's already a successful payment for this task
    existing_success = db.query(Payment).filter(
        Payment.task_id == body.task_id,
        Payment.user_id == user.id,
        Payment.payment_status == "success",
    ).first()
    if existing_success:
        raise HTTPException(status_code=400, detail="该任务已支付")

    # Cancel any pending payments for this task
    pending_payments = db.query(Payment).filter(
        Payment.task_id == body.task_id,
        Payment.user_id == user.id,
        Payment.payment_status == "pending",
    ).all()
    for pp in pending_payments:
        pp.payment_status = "failed"
    db.commit()

    # Create new payment
    amount_cents = settings.PRICE_PER_VIDEO_CENTS  # 990 = 9.9 yuan
    payment = Payment(
        user_id=user.id,
        task_id=body.task_id,
        payment_type="per_video",
        amount_cents=amount_cents,
        payment_channel=body.payment_channel,
        payment_status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    logger.info(
        f"Payment created: {payment.id} for task {body.task_id} "
        f"by user {user.id}, channel={body.payment_channel}, amount={amount_cents}"
    )

    # MVP: generate mock QR code URL
    qr_url = f"/api/payments/{payment.id}/mock-qr"

    return CreatePaymentResponse(
        payment_id=payment.id,
        amount_cents=amount_cents,
        amount_display=f"{amount_cents / 100:.1f}",
        payment_channel=body.payment_channel,
        payment_status="pending",
        qr_code_url=qr_url,
    )


@router.get("/{payment_id}/status", response_model=PaymentStatusResponse)
def get_payment_status(
    payment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Query the current status of a payment.

    Frontend polls this endpoint to detect payment completion.
    """
    payment = db.query(Payment).filter(
        Payment.id == payment_id, Payment.user_id == user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="支付订单不存在")

    return PaymentStatusResponse(
        payment_id=payment.id,
        payment_status=payment.payment_status,
        task_id=payment.task_id or "",
        paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
    )


@router.post("/{payment_id}/mock-pay")
def mock_pay(
    payment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """MVP mock payment -- simulates successful payment.

    In production this would be replaced by real payment gateway callbacks.
    """
    payment = db.query(Payment).filter(
        Payment.id == payment_id, Payment.user_id == user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="支付订单不存在")

    if payment.payment_status == "success":
        return {"success": True, "message": "已支付", "payment_status": "success"}

    if payment.payment_status != "pending":
        raise HTTPException(status_code=400, detail="订单状态异常，请重新创建订单")

    # Mark as paid
    payment.payment_status = "success"
    payment.paid_at = datetime.utcnow()
    db.commit()

    logger.info(f"Mock payment completed: {payment_id}")

    return {
        "success": True,
        "message": "支付成功",
        "payment_status": "success",
    }


@router.post("/{payment_id}/cancel")
def cancel_payment(
    payment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending payment."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id, Payment.user_id == user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="支付订单不存在")

    if payment.payment_status != "pending":
        raise HTTPException(status_code=400, detail="只能取消待支付的订单")

    payment.payment_status = "failed"
    db.commit()

    return {"success": True, "message": "订单已取消"}


@router.post("/callback/{channel}")
def payment_callback(
    channel: str,
    db: Session = Depends(get_db),
):
    """Payment callback from external payment provider.

    MVP: placeholder endpoint. In production, would verify signature,
    update payment status, and trigger download authorization.
    """
    if channel not in ("alipay", "wechat"):
        raise HTTPException(status_code=400, detail="Unknown channel")

    # MVP: no real callback processing
    logger.info(f"Payment callback received from {channel} (MVP: no-op)")

    return {"success": True}


# ---------------------------------------------------------------------------
# Quota check + download authorization
# ---------------------------------------------------------------------------

@router.get("/check-download/{task_id}")
def check_download_auth(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether the user can download a task's output.

    Returns:
    - can_download: True if user has free quota OR has paid for this task
    - reason: "free_quota" or "paid" or "needs_payment"
    - free_quota_remaining: current free quota count
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成(当前状态: {task.status})",
        )

    # Check if already paid for this task
    paid = db.query(Payment).filter(
        Payment.task_id == task_id,
        Payment.user_id == user.id,
        Payment.payment_status == "success",
    ).first()
    if paid:
        return {
            "can_download": True,
            "reason": "paid",
            "free_quota_remaining": user.free_quota_remaining,
        }

    # Check free quota
    if user.free_quota_remaining > 0:
        return {
            "can_download": True,
            "reason": "free_quota",
            "free_quota_remaining": user.free_quota_remaining,
        }

    # Needs payment
    return {
        "can_download": False,
        "reason": "needs_payment",
        "free_quota_remaining": 0,
        "price_cents": settings.PRICE_PER_VIDEO_CENTS,
        "price_display": f"{settings.PRICE_PER_VIDEO_CENTS / 100:.1f}",
    }


@router.post("/use-quota/{task_id}")
def use_free_quota(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deduct one free quota for a task download.

    Called when user clicks download and has free quota.
    Prevents double-deduction by checking if already deducted.
    """
    task = db.query(Task).filter(
        Task.id == task_id, Task.user_id == user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成(当前状态: {task.status})",
        )

    # Check if already paid (no quota deduction needed)
    paid = db.query(Payment).filter(
        Payment.task_id == task_id,
        Payment.user_id == user.id,
        Payment.payment_status == "success",
    ).first()
    if paid:
        return {
            "success": True,
            "message": "已付费，无需扣减额度",
            "free_quota_remaining": user.free_quota_remaining,
            "deducted": False,
        }

    # Check if quota already used for this task (prevent double deduction)
    # We track this via a "quota_used" payment record
    quota_record = db.query(Payment).filter(
        Payment.task_id == task_id,
        Payment.user_id == user.id,
        Payment.payment_type == "per_video",
        Payment.amount_cents == 0,
        Payment.payment_status == "success",
    ).first()
    if quota_record:
        return {
            "success": True,
            "message": "已使用免费额度",
            "free_quota_remaining": user.free_quota_remaining,
            "deducted": False,
        }

    # Check quota
    if user.free_quota_remaining <= 0:
        raise HTTPException(status_code=402, detail="免费额度已用完，请付费下载")

    # Deduct quota
    user.free_quota_remaining -= 1
    db.commit()

    # Record the quota usage
    quota_payment = Payment(
        user_id=user.id,
        task_id=task_id,
        payment_type="per_video",
        amount_cents=0,  # Free quota usage
        payment_channel="alipay",  # Placeholder
        payment_status="success",
        paid_at=datetime.utcnow(),
    )
    db.add(quota_payment)
    db.commit()

    logger.info(
        f"Free quota used: user {user.id}, task {task_id}, "
        f"remaining={user.free_quota_remaining}"
    )

    return {
        "success": True,
        "message": "免费额度已扣减",
        "free_quota_remaining": user.free_quota_remaining,
        "deducted": True,
    }
