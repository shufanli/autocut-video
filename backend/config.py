"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """All configurable parameters per PRD 17.x."""

    # --- 17.1 Business Config ---
    FREE_QUOTA_INITIAL: int = 3
    PRICE_PER_VIDEO_CENTS: int = 990
    PRICE_MONTHLY_CENTS: int = 9900
    PRICE_YEARLY_CENTS: int = 79900
    MONTHLY_QUOTA: int = 30
    YEARLY_QUOTA: int = 400
    OVERAGE_PRICE_CENTS: int = 690
    PRICE_UNLIMITED_YEARLY_CENTS: int = 149900
    UNLIMITED_DAILY_LIMIT: int = 10
    VIDEO_RETENTION_HOURS: int = 24
    HISTORY_PAGE_SIZE: int = 20

    # --- 17.2 Processing Engine Config ---
    MAX_FILE_SIZE_MB: int = 500
    MAX_TOTAL_DURATION_MIN: int = 30
    SUPPORTED_FORMATS: List[str] = ["mp4", "mov", "webm"]
    MAX_RESOLUTION: str = "1080p"
    FILLER_WORDS: List[str] = ["嗯", "啊", "那个", "就是", "然后"]
    LONG_PAUSE_THRESHOLD_MS: int = 1500
    PAUSE_SHORTEN_TARGET_MS: int = 500
    MAX_EFFECTS_PER_MINUTE: int = 3
    BGM_DEFAULT_VOLUME: float = 0.15
    CROSSFADE_MS: int = 50
    WHISPER_LOW_CONFIDENCE_THRESHOLD: float = 0.6
    WHISPER_LOW_CONFIDENCE_WARN_RATIO: float = 0.3

    # --- 17.3 System Config ---
    PROCESSING_TIMEOUT_MIN: int = 15
    RENDER_MAX_RETRY: int = 1
    MAX_CONCURRENT_TASKS: int = 3
    MAX_QUEUED_TASKS: int = 20
    LOGIN_CODE_EXPIRE_SEC: int = 300
    LOGIN_CODE_COOLDOWN_SEC: int = 60
    LOGIN_MAX_FAIL_ATTEMPTS: int = 3
    LOGIN_LOCKOUT_MIN: int = 2
    LLM_PROVIDER: str = "claude"
    LLM_MODEL: str = "claude-haiku"
    LLM_TIMEOUT_SEC: int = 30
    WHISPER_MODEL: str = "large-v3"
    DEVICE_FINGERPRINT_MAX_ACCOUNTS: int = 2
    IP_SMS_HOURLY_LIMIT: int = 50
    PHONE_SMS_DAILY_LIMIT: int = 5
    CONTENT_MODERATION_PROVIDER: str = "aliyun"

    # --- 17.4 Copy Config ---
    HOMEPAGE_TITLE: str = "口播视频，AI 一键出片"
    HOMEPAGE_SUBTITLE: str = "上传素材 → AI 去口误、加字幕 → 几分钟出成品，每处修改可逐条审核"
    SATISFACTION_ENABLED: bool = True
    DEMO_ASSET_TYPE: str = "static_image"

    # --- JWT ---
    JWT_SECRET: str = "autocut-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 72

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./autocut.db"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://autocut.allinai.asia"]

    # --- Upload storage ---
    UPLOAD_DIR: str = "./uploads"

    # --- OpenAI / Whisper API ---
    OPENAI_API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
