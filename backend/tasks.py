"""Tasks router — create task, upload files, reorder, delete, start processing.

MVP: files stored to local disk under UPLOAD_DIR/<task_id>/.
"""

import os
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from auth import get_current_user
from models import User, Task, TaskFile, TaskResult
from services.pipeline import start_processing, get_task_progress
from services.render import start_render, get_render_progress

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


class TaskFileSchema(BaseModel):
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


# ---------------------------------------------------------------------------
# Processing endpoints (Sprint 4)
# ---------------------------------------------------------------------------

@router.post("/{task_id}/process")
def trigger_processing(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start AI processing pipeline for a task.

    The task must be in 'uploading' status with at least one source file.
    Processing runs in a background thread.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("uploading", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态({task.status})不允许启动处理",
        )

    # Reset status to uploading for retry
    if task.status == "failed":
        task.status = "uploading"
        task.error_message = None
        db.commit()

    # Check source files exist
    source_count = (
        db.query(TaskFile)
        .filter(TaskFile.task_id == task_id, TaskFile.file_type == "source")
        .count()
    )
    if source_count == 0:
        raise HTTPException(status_code=400, detail="请先上传视频文件")

    try:
        start_processing(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail="启动处理失败，请稍后重试")

    return {
        "success": True,
        "task_id": task_id,
        "status": "processing",
        "message": "处理已开始",
    }


@router.get("/{task_id}/status")
def get_task_status(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current processing status and progress for a task.

    Returns stage info, progress percentage, and estimated remaining time.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # Base response
    response = {
        "task_id": task_id,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else "",
        "error_message": task.error_message,
    }

    # If processing, add real-time progress from in-memory tracker
    if task.status == "processing":
        progress = get_task_progress(task_id)
        if progress:
            response.update({
                "stage": progress["stage"],
                "stage_name": progress["stage_name"],
                "stage_key": progress["stage_key"],
                "progress": progress["progress"],
                "estimated_seconds": progress["estimated_seconds"],
                "total_stages": progress["total_stages"],
                "stages": progress["stages"],
                "error": progress.get("error", ""),
            })
        else:
            # No progress data yet -- just started
            response.update({
                "stage": 0,
                "stage_name": "合并素材",
                "stage_key": "merge",
                "progress": 0,
                "estimated_seconds": 120,
                "total_stages": 4,
                "stages": [
                    {"key": "merge", "name": "合并素材", "status": "active"},
                    {"key": "transcribe", "name": "语音识别", "status": "pending"},
                    {"key": "stutter", "name": "检测口误", "status": "pending"},
                    {"key": "subtitle", "name": "生成字幕", "status": "pending"},
                ],
                "error": "",
            })

    elif task.status == "preview":
        # Processing complete, all stages done
        progress = get_task_progress(task_id)
        response.update({
            "stage": 4,
            "stage_name": "完成",
            "stage_key": "done",
            "progress": 100,
            "estimated_seconds": 0,
            "total_stages": 4,
            "stages": [
                {"key": "merge", "name": "合并素材", "status": "completed"},
                {"key": "transcribe", "name": "语音识别", "status": "completed"},
                {"key": "stutter", "name": "检测口误", "status": "completed"},
                {"key": "subtitle", "name": "生成字幕", "status": "completed"},
            ],
            "error": "",
        })

    elif task.status == "rendering":
        # Real render progress from in-memory tracker
        render_prog = get_render_progress(task_id)
        progress_pct = render_prog["progress"] if render_prog else 0
        est_seconds = render_prog["estimated_seconds"] if render_prog else 120
        render_error = render_prog.get("error", "") if render_prog else ""
        response.update({
            "stage": 1,
            "stage_name": "渲染中",
            "stage_key": "rendering",
            "progress": progress_pct,
            "estimated_seconds": est_seconds,
            "total_stages": 1,
            "stages": [
                {"key": "rendering", "name": "渲染中", "status": "active"},
            ],
            "error": render_error,
        })

    elif task.status == "completed":
        # Rendering finished -- return completed state with full progress info
        response.update({
            "stage": 1,
            "stage_name": "完成",
            "stage_key": "done",
            "progress": 100,
            "estimated_seconds": 0,
            "total_stages": 1,
            "stages": [
                {"key": "rendering", "name": "渲染中", "status": "completed"},
            ],
            "error": "",
        })

    elif task.status == "failed":
        response.update({
            "stage": -1,
            "stage_name": "失败",
            "stage_key": "failed",
            "progress": 0,
            "estimated_seconds": 0,
            "total_stages": 4,
            "stages": [],
            "error": task.error_message or "处理失败",
        })

    return response


# ---------------------------------------------------------------------------
# Preview endpoints (Sprint 5)
# ---------------------------------------------------------------------------

class PreviewStutterUpdate(BaseModel):
    """A single stutter mark with updated action (delete/keep)."""
    index: int
    action: str  # "delete" or "keep"


class PreviewUpdateRequest(BaseModel):
    """Body for PUT /api/tasks/{id}/preview."""
    stutter_updates: List[PreviewStutterUpdate] = []
    subtitle_style: Optional[str] = None  # "clean-white", "black-bg", "colorful"


@router.get("/{task_id}/preview")
def get_preview_data(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get preview data for a task: transcript words, stutter marks, subtitles.

    The task must be in 'preview' (or later) status, meaning processing is done.
    Returns the full transcript, stutter marks with their current action states,
    subtitle entries, and summary statistics.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("preview", "rendering", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未处理完成(当前状态: {task.status})",
        )

    # Load results from task_results table
    results = {
        r.agent_name: r.result_json
        for r in db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
    }

    transcribe_data = results.get("transcribe", {})
    stutter_data = results.get("stutter", {})
    subtitle_data = results.get("subtitle", {})

    words = transcribe_data.get("words", [])
    marks = stutter_data.get("marks", [])
    stats = stutter_data.get("stats", {})
    subtitles = subtitle_data.get("subtitles", [])

    # Compute dynamic stats based on current mark actions
    deleted_count = sum(1 for m in marks if m.get("action") == "delete")
    deleted_duration_ms = sum(
        m.get("duration_ms", 0) for m in marks if m.get("action") == "delete"
    )

    # Get subtitle style from task preferences (default: clean-white)
    preferences = task.preferences or {}
    subtitle_style = preferences.get("subtitleStyle", "clean-white")

    return {
        "task_id": task_id,
        "status": task.status,
        "words": words,
        "stutter_marks": marks,
        "stutter_stats": {
            "total_marks": len(marks),
            "deleted_count": deleted_count,
            "deleted_duration_ms": deleted_duration_ms,
            "filler_count": stats.get("filler_count", 0),
            "repeat_count": stats.get("repeat_count", 0),
            "pause_count": stats.get("pause_count", 0),
        },
        "subtitles": subtitles,
        "subtitle_style": subtitle_style,
    }


@router.put("/{task_id}/preview")
def update_preview_data(
    task_id: str,
    body: PreviewUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save user adjustments to stutter marks and subtitle style.

    Accepts a list of stutter mark index + action updates and optional
    subtitle style change. Persists changes back to task_results and
    task preferences.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("preview",):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态({task.status})不允许修改预览数据",
        )

    # Update stutter marks if provided
    if body.stutter_updates:
        stutter_result = (
            db.query(TaskResult)
            .filter(TaskResult.task_id == task_id, TaskResult.agent_name == "stutter")
            .first()
        )
        if stutter_result and stutter_result.result_json:
            marks = stutter_result.result_json.get("marks", [])
            # Build index map for quick lookup
            update_map = {u.index: u.action for u in body.stutter_updates}
            for i, mark in enumerate(marks):
                if i in update_map:
                    mark["action"] = update_map[i]

            # Recompute stats
            deleted_count = sum(1 for m in marks if m.get("action") == "delete")
            deleted_duration_ms = sum(
                m.get("duration_ms", 0) for m in marks if m.get("action") == "delete"
            )
            stutter_result.result_json = {
                "marks": marks,
                "stats": {
                    **stutter_result.result_json.get("stats", {}),
                    "deleted_count": deleted_count,
                    "total_duration_ms": deleted_duration_ms,
                },
            }
            # Force SQLAlchemy to detect JSON mutation
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(stutter_result, "result_json")
            db.commit()

    # Update subtitle style if provided
    if body.subtitle_style:
        preferences = task.preferences or {}
        preferences["subtitleStyle"] = body.subtitle_style
        task.preferences = preferences
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(task, "preferences")
        db.commit()

    return {"success": True, "message": "预览数据已更新"}


# ---------------------------------------------------------------------------
# Render endpoint (Sprint 5 bug fix — transitions task from preview to rendering)
# ---------------------------------------------------------------------------

@router.post("/{task_id}/render")
def trigger_render(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start rendering: transition task to 'rendering' and launch FFmpeg pipeline.

    Called when the user confirms edits on the preview page.
    Changes task status and spawns a background render thread.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "preview":
        raise HTTPException(
            status_code=400,
            detail=f"当前状态({task.status})不允许启动渲染",
        )

    task.status = "rendering"
    db.commit()
    logger.info(f"Task {task_id} status changed to rendering")

    # Start actual rendering in background
    try:
        start_render(task_id)
    except Exception as e:
        logger.error(f"Failed to start render: {e}")
        # Don't revert status -- the render progress tracker will handle errors

    return {
        "success": True,
        "task_id": task_id,
        "status": "rendering",
        "message": "渲染已开始",
    }


# ---------------------------------------------------------------------------
# Render status endpoint (Sprint 6)
# ---------------------------------------------------------------------------

@router.get("/{task_id}/render-status")
def get_render_status(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get render progress for a task.

    Returns progress percentage, estimated time, and any errors.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    response = {
        "task_id": task_id,
        "status": task.status,
        "error_message": task.error_message,
    }

    if task.status == "rendering":
        progress = get_render_progress(task_id)
        if progress:
            response.update({
                "progress": progress["progress"],
                "estimated_seconds": progress["estimated_seconds"],
                "error": progress.get("error", ""),
            })
        else:
            response.update({
                "progress": 0,
                "estimated_seconds": 120,
                "error": "",
            })

    elif task.status == "completed":
        response.update({
            "progress": 100,
            "estimated_seconds": 0,
            "error": "",
        })

    elif task.status == "failed":
        response.update({
            "progress": 0,
            "estimated_seconds": 0,
            "error": task.error_message or "渲染失败",
        })

    else:
        response.update({
            "progress": 0,
            "estimated_seconds": 0,
            "error": "",
        })

    return response


# ---------------------------------------------------------------------------
# Download endpoint (Sprint 6)
# ---------------------------------------------------------------------------

@router.get("/{task_id}/download")
def download_output(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the rendered output video.

    Task must be in 'completed' status. Returns the MP4 file.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"视频尚未完成(当前状态: {task.status})",
        )

    # Check if expired
    if task.expires_at and datetime.utcnow() > task.expires_at:
        raise HTTPException(
            status_code=410,
            detail="视频已过期删除，请重新处理",
        )

    # Find the output file
    output_file = (
        db.query(TaskFile)
        .filter(TaskFile.task_id == task_id, TaskFile.file_type == "output")
        .first()
    )

    if not output_file or not os.path.exists(output_file.storage_path):
        raise HTTPException(status_code=404, detail="输出文件不存在")

    # Generate a nice filename
    download_filename = f"autocut_{task_id[:8]}.mp4"

    return FileResponse(
        path=output_file.storage_path,
        media_type="video/mp4",
        filename=download_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{download_filename}"',
        },
    )


# ---------------------------------------------------------------------------
# Result info endpoint (Sprint 6)
# ---------------------------------------------------------------------------

@router.get("/{task_id}/result")
def get_result_info(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get result information for a completed task.

    Returns video info (duration, size, resolution) and streaming URL.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in ("completed",):
        raise HTTPException(
            status_code=400,
            detail=f"视频尚未完成(当前状态: {task.status})",
        )

    # Load render result
    render_result = (
        db.query(TaskResult)
        .filter(TaskResult.task_id == task_id, TaskResult.agent_name == "render")
        .first()
    )

    render_info = render_result.result_json if render_result else {}

    # Check expiry
    expired = False
    if task.expires_at and datetime.utcnow() > task.expires_at:
        expired = True

    return {
        "task_id": task_id,
        "status": task.status,
        "duration_ms": task.output_duration_ms or render_info.get("output_duration_ms", 0),
        "file_size_bytes": task.output_file_size_bytes or render_info.get("output_size_bytes", 0),
        "resolution": render_info.get("resolution", "unknown"),
        "subtitle_style": render_info.get("subtitle_style", "clean-white"),
        "cuts_applied": render_info.get("cuts_applied", 0),
        "completed_at": task.completed_at.isoformat() if task.completed_at else "",
        "expires_at": task.expires_at.isoformat() if task.expires_at else "",
        "expired": expired,
        "video_url": f"/api/tasks/{task_id}/stream",
        "download_url": f"/api/tasks/{task_id}/download",
    }


# ---------------------------------------------------------------------------
# Stream endpoint (Sprint 6) -- serve video for HTML5 player
# ---------------------------------------------------------------------------

@router.get("/{task_id}/stream")
def stream_video(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream the rendered output video for in-browser playback.

    Similar to download but without Content-Disposition: attachment.
    """
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"视频尚未完成(当前状态: {task.status})",
        )

    # Find the output file
    output_file = (
        db.query(TaskFile)
        .filter(TaskFile.task_id == task_id, TaskFile.file_type == "output")
        .first()
    )

    if not output_file or not os.path.exists(output_file.storage_path):
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        path=output_file.storage_path,
        media_type="video/mp4",
    )


# ---------------------------------------------------------------------------
# Subtitle track endpoint (Sprint 6) -- WebVTT for HTML5 player
# ---------------------------------------------------------------------------

@router.get("/{task_id}/subtitles.vtt")
def get_subtitle_track(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Serve WebVTT subtitle track for the completed video."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="视频尚未完成")

    vtt_path = os.path.join(settings.UPLOAD_DIR, task_id, "subtitles.vtt")
    if not os.path.exists(vtt_path):
        raise HTTPException(status_code=404, detail="字幕文件不存在")

    return FileResponse(
        path=vtt_path,
        media_type="text/vtt",
        headers={"Content-Type": "text/vtt; charset=utf-8"},
    )


# ---------------------------------------------------------------------------
# Satisfaction feedback endpoint (Sprint 6)
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    rating: str  # "up" or "down"
    comment: Optional[str] = None


@router.post("/{task_id}/feedback")
def submit_feedback(
    task_id: str,
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit satisfaction feedback for a completed task."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="只能对已完成的任务提交反馈",
        )

    if body.rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="rating 必须是 'up' 或 'down'")

    # Save feedback as a task result
    existing = (
        db.query(TaskResult)
        .filter(TaskResult.task_id == task_id, TaskResult.agent_name == "feedback")
        .first()
    )

    feedback_data = {
        "rating": body.rating,
        "comment": body.comment or "",
        "submitted_at": datetime.utcnow().isoformat(),
    }

    if existing:
        existing.result_json = feedback_data
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(existing, "result_json")
    else:
        feedback_result = TaskResult(
            task_id=task_id,
            agent_name="feedback",
            result_json=feedback_data,
        )
        db.add(feedback_result)

    db.commit()

    return {"success": True, "message": "感谢您的反馈!"}
