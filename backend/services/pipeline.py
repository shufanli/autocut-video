"""Processing pipeline orchestrator.

Runs four stages in sequence in a background thread:
    Stage 0: Merge source videos (FFmpeg concat)
    Stage 1: Transcribe audio (Whisper API or mock)
    Stage 2: Detect stutters (rule engine)
    Stage 3: Generate subtitles

Progress is tracked via an in-memory dict that the status API reads.
"""

import logging
import os
import threading
import time
import traceback
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import Task, TaskFile, TaskResult
from services.merge import merge_videos, get_video_duration_ms
from services.transcribe import transcribe_audio
from services.stutter import detect_stutters, compute_stutter_stats
from services.subtitle import generate_subtitles, save_srt

logger = logging.getLogger("autocut.pipeline")

# ---------------------------------------------------------------------------
# In-memory progress tracking
# ---------------------------------------------------------------------------

# {task_id: {stage, stage_name, progress, estimated_seconds, started_at, error}}
_task_progress: Dict[str, dict] = {}
_progress_lock = threading.Lock()

STAGES = [
    {"key": "merge", "name": "合并素材", "weight": 15},
    {"key": "transcribe", "name": "语音识别", "weight": 45},
    {"key": "stutter", "name": "检测口误", "weight": 20},
    {"key": "subtitle", "name": "生成字幕", "weight": 20},
]


def get_task_progress(task_id: str) -> Optional[dict]:
    """Get the current processing progress for a task.

    Returns None if the task is not being processed.
    """
    with _progress_lock:
        return _task_progress.get(task_id, None)


def _update_progress(
    task_id: str,
    stage: int,
    progress: int = 0,
    estimated_seconds: int = 0,
    error: str = "",
):
    """Update in-memory progress for a task."""
    with _progress_lock:
        stage_name = STAGES[stage]["name"] if stage < len(STAGES) else "完成"
        _task_progress[task_id] = {
            "stage": stage,
            "stage_name": stage_name,
            "stage_key": STAGES[stage]["key"] if stage < len(STAGES) else "done",
            "progress": progress,
            "estimated_seconds": estimated_seconds,
            "error": error,
            "total_stages": len(STAGES),
            "stages": [
                {
                    "key": s["key"],
                    "name": s["name"],
                    "status": (
                        "completed" if i < stage
                        else "active" if i == stage
                        else "pending"
                    ),
                }
                for i, s in enumerate(STAGES)
            ],
        }


def _clear_progress(task_id: str):
    """Remove progress tracking for a task (after completion or failure)."""
    with _progress_lock:
        _task_progress.pop(task_id, None)


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def start_processing(task_id: str) -> None:
    """Start the processing pipeline for a task in a background thread.

    This is called by the API endpoint. It validates the task state,
    marks it as 'processing', and spawns a daemon thread for the pipeline.
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        if task.status not in ("uploading",):
            raise ValueError(f"Task is in invalid state for processing: {task.status}")

        # Check that the task has at least one source file
        source_files = (
            db.query(TaskFile)
            .filter(TaskFile.task_id == task_id, TaskFile.file_type == "source")
            .order_by(TaskFile.sort_order)
            .all()
        )
        if not source_files:
            raise ValueError("No source files uploaded")

        # Update task status
        task.status = "processing"
        db.commit()

        # Initialize progress
        _update_progress(task_id, stage=0, progress=0, estimated_seconds=120)

        # Spawn background thread
        thread = threading.Thread(
            target=_run_pipeline,
            args=(task_id,),
            daemon=True,
            name=f"pipeline-{task_id[:8]}",
        )
        thread.start()
        logger.info(f"Pipeline started for task {task_id}")

    finally:
        db.close()


def _run_pipeline(task_id: str) -> None:
    """Execute the full pipeline (runs in a background thread)."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found in pipeline thread")
            return

        task_dir = os.path.join(settings.UPLOAD_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

        # Get source files in order
        source_files = (
            db.query(TaskFile)
            .filter(TaskFile.task_id == task_id, TaskFile.file_type == "source")
            .order_by(TaskFile.sort_order)
            .all()
        )
        source_paths = [f.storage_path for f in source_files]

        # ---- Stage 0: Merge ----
        logger.info(f"[{task_id[:8]}] Stage 0: Merging {len(source_paths)} files")
        _update_progress(task_id, stage=0, progress=10, estimated_seconds=100)

        merged_path = os.path.join(task_dir, "merged.mp4")
        merge_videos(source_paths, merged_path)

        # Record merged file in DB
        duration_ms = get_video_duration_ms(merged_path)
        merged_file = TaskFile(
            task_id=task_id,
            file_type="merged",
            storage_path=merged_path,
            original_filename="merged.mp4",
            file_size_bytes=os.path.getsize(merged_path) if os.path.exists(merged_path) else 0,
            duration_ms=duration_ms,
            sort_order=0,
        )
        db.add(merged_file)
        task.total_duration_ms = duration_ms
        db.commit()

        _update_progress(task_id, stage=0, progress=100, estimated_seconds=90)

        # ---- Stage 1: Transcribe ----
        logger.info(f"[{task_id[:8]}] Stage 1: Transcribing audio")
        _update_progress(task_id, stage=1, progress=10, estimated_seconds=80)

        words = transcribe_audio(
            merged_path,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        # Save transcription result
        _save_result(db, task_id, "transcribe", {"words": [dict(w) for w in words]})
        _update_progress(task_id, stage=1, progress=100, estimated_seconds=40)

        # ---- Stage 2: Stutter detection ----
        logger.info(f"[{task_id[:8]}] Stage 2: Detecting stutters")
        _update_progress(task_id, stage=2, progress=10, estimated_seconds=30)

        stutter_marks = detect_stutters(words)
        stutter_stats = compute_stutter_stats(stutter_marks)

        _save_result(db, task_id, "stutter", {
            "marks": [dict(m) for m in stutter_marks],
            "stats": stutter_stats,
        })
        _update_progress(task_id, stage=2, progress=100, estimated_seconds=15)

        # ---- Stage 3: Subtitle generation ----
        logger.info(f"[{task_id[:8]}] Stage 3: Generating subtitles")
        _update_progress(task_id, stage=3, progress=10, estimated_seconds=10)

        subtitles = generate_subtitles(words)
        srt_path = os.path.join(task_dir, "subtitles.srt")
        save_srt(subtitles, srt_path)

        _save_result(db, task_id, "subtitle", {
            "subtitles": [dict(s) for s in subtitles],
            "srt_path": srt_path,
        })
        _update_progress(task_id, stage=3, progress=100, estimated_seconds=0)

        # ---- Pipeline complete ----
        task.status = "preview"
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"[{task_id[:8]}] Pipeline complete! Status -> preview")

        # Keep progress available for a bit so the frontend can see "complete"
        _update_progress(task_id, stage=len(STAGES), progress=100, estimated_seconds=0)

    except Exception as e:
        logger.error(f"[{task_id[:8]}] Pipeline failed: {e}\n{traceback.format_exc()}")
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass

        _update_progress(
            task_id,
            stage=_task_progress.get(task_id, {}).get("stage", 0),
            progress=0,
            error=str(e)[:200],
        )

    finally:
        db.close()


def _save_result(db: Session, task_id: str, agent_name: str, result_json: dict):
    """Save a processing result to the task_results table."""
    result = TaskResult(
        task_id=task_id,
        agent_name=agent_name,
        result_json=result_json,
    )
    db.add(result)
    db.commit()
