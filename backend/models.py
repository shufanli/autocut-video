"""SQLAlchemy ORM models — 6 tables per PRD 13.1."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship

from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    phone = Column(String(11), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, default=datetime.utcnow)
    free_quota_remaining = Column(Integer, default=3)
    subscription_plan = Column(
        Enum("free", "monthly", "yearly", name="subscription_plan_enum"),
        default="free",
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    monthly_quota_remaining = Column(Integer, default=0)
    default_preferences = Column(JSON, nullable=True)

    tasks = relationship("Task", back_populates="user")
    payments = relationship("Payment", back_populates="user")


# ---------------------------------------------------------------------------
# tasks
# ---------------------------------------------------------------------------
class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum(
            "uploading",
            "processing",
            "preview",
            "rendering",
            "completed",
            "failed",
            "expired",
            name="task_status_enum",
        ),
        default="uploading",
    )
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    is_degraded = Column(Boolean, default=False)
    total_duration_ms = Column(Integer, nullable=True)
    output_duration_ms = Column(Integer, nullable=True)
    output_file_size_bytes = Column(BigInteger, nullable=True)

    user = relationship("User", back_populates="tasks")
    files = relationship("TaskFile", back_populates="task")
    results = relationship("TaskResult", back_populates="task")


# ---------------------------------------------------------------------------
# task_files
# ---------------------------------------------------------------------------
class TaskFile(Base):
    __tablename__ = "task_files"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    file_type = Column(
        Enum("source", "merged", "output", name="file_type_enum"),
        default="source",
    )
    storage_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size_bytes = Column(BigInteger, default=0)
    duration_ms = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="files")


# ---------------------------------------------------------------------------
# task_results
# ---------------------------------------------------------------------------
class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="results")


# ---------------------------------------------------------------------------
# payments
# ---------------------------------------------------------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    payment_type = Column(
        Enum("per_video", "monthly", "yearly", name="payment_type_enum"),
    )
    amount_cents = Column(Integer, nullable=False)
    payment_channel = Column(
        Enum("alipay", "wechat", name="payment_channel_enum"),
    )
    payment_status = Column(
        Enum("pending", "success", "failed", "refunded", name="payment_status_enum"),
        default="pending",
    )
    external_order_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")


# ---------------------------------------------------------------------------
# events (analytics)
# ---------------------------------------------------------------------------
class Event(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True)
    session_id = Column(String(64), nullable=True)
    event_name = Column(String(100), nullable=False)
    event_params = Column(JSON, nullable=True)
    page_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
