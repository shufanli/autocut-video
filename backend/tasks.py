"""Tasks router — create task, upload files, reorder, delete, start processing.

MVP: files stored to local disk under UPLOAD_DIR/<task_id>/.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from auth import get_current_user
from models import User, Task, TaskFile

logger = logging.getLogger("autocut.tasks")

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Allowed video extensions
ALLOWED_EXTENSIONS = {"mp4", "mov", "webm"}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TaskResponse(BaseModel):
    id: str
    status: str
    preferences: Optional[dict] = None
    created_at: str
    files: list


class FileResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    sort_order: int
    uploaded_at: str


class ReorderRequest(BaseModel):
    file_ids: List[str]


class PreferencesRequest(BaseModel):
    preferences: dict


class QuotaResponse(BaseModel):
    free_quota_remaining: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _file_extension(filename: str) -> str:
    """Extract lowercase file extension without dot."""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


def _task_to_response(task: Task) -> dict:
    """Serialize a Task + its files to a dict."""
    files = sorted(task.files, key=lambda f: f.sort_order)
    return {
        "id": task.id,
        "status": task.status,
        "preferences": task.preferences,
        "created_at": task.created_at.isoformat() if task.created_at else "",
        "files": [
            {
                "id": f.id,
                "original_filename": f.original_filename or "",
                "file_size_bytes": f.file_size_bytes or 0,
                "sort_order": f.sort_order,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else "",
            }
            for f in files
            if f.file_type == "source"
        ],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=TaskResponse)
def create_task(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new task in 'uploading' status."""
    task = Task(user_id=user.id, status="uploading")
    db.add(task)
    db.commit()
    db.refresh(task)
    logger.info(f"Task created: {task.id} by user {user.id}")
    return _task_to_response(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get a task by ID (must belong to current user)."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return _task_to_response(task)


@router.post("/{task_id}/files")
async def upload_files(
    task_id: str,
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload one or more video files to a task."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "uploading":
        raise HTTPException(status_code=400, detail="任务状态不允许上传文件")

    # Ensure upload directory exists
    task_dir = os.path.join(settings.UPLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    # Get current max sort_order
    existing_files = db.query(TaskFile).filter(
        TaskFile.task_id == task_id, TaskFile.file_type == "source"
    ).all()
    max_order = max((f.sort_order for f in existing_files), default=-1)

    uploaded = []
    errors = []

    for upload_file in files:
        filename = upload_file.filename or "unknown"
        ext = _file_extension(filename)

        # Validate extension
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({
                "filename": filename,
                "error": f"不支持的文件格式，请上传 MP4/MOV/WebM",
            })
            continue

        # Read file content
        content = await upload_file.read()
        file_size = len(content)

        # Check file size warning (>500MB) — we still accept it, just flag
        size_warning = file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024

        # Save to disk
        max_order += 1
        task_file = TaskFile(
            task_id=task_id,
            file_type="source",
            storage_path=os.path.join(task_dir, f"{max_order}_{filename}"),
            original_filename=filename,
            file_size_bytes=file_size,
            sort_order=max_order,
        )

        with open(task_file.storage_path, "wb") as f:
            f.write(content)

        db.add(task_file)
        db.commit()
        db.refresh(task_file)

        uploaded.append({
            "id": task_file.id,
            "original_filename": task_file.original_filename,
            "file_size_bytes": task_file.file_size_bytes,
            "sort_order": task_file.sort_order,
            "uploaded_at": task_file.uploaded_at.isoformat() if task_file.uploaded_at else "",
            "size_warning": size_warning,
        })

    return {
        "uploaded": uploaded,
        "errors": errors,
    }


@router.put("/{task_id}/files/reorder")
def reorder_files(
    task_id: str,
    body: ReorderRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reorder files by providing an ordered list of file IDs."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    for i, file_id in enumerate(body.file_ids):
        task_file = db.query(TaskFile).filter(
            TaskFile.id == file_id, TaskFile.task_id == task_id
        ).first()
        if task_file:
            task_file.sort_order = i

    db.commit()
    return {"success": True}


@router.delete("/{task_id}/files/{file_id}")
def delete_file(
    task_id: str,
    file_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a file from a task."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_file = db.query(TaskFile).filter(
        TaskFile.id == file_id, TaskFile.task_id == task_id
    ).first()
    if not task_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # Remove from disk
    if task_file.storage_path and os.path.exists(task_file.storage_path):
        try:
            os.remove(task_file.storage_path)
        except OSError:
            pass

    db.delete(task_file)
    db.commit()
    return {"success": True}


@router.put("/{task_id}/preferences")
def update_preferences(
    task_id: str,
    body: PreferencesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update task preferences (subtitle style, position, etc.)."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.preferences = body.preferences
    db.commit()
    return {"success": True, "preferences": task.preferences}


@router.get("/{task_id}/quota", response_model=QuotaResponse)
def get_quota(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's remaining free quota."""
    return QuotaResponse(free_quota_remaining=user.free_quota_remaining)


# Standalone quota endpoint (no task needed)
@router.get("", response_model=list)
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all tasks for the current user."""
    tasks = db.query(Task).filter(Task.user_id == user.id).order_by(Task.created_at.desc()).all()
    return [_task_to_response(t) for t in tasks]
