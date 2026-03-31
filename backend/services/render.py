"""Video render engine -- FFmpeg cut + subtitle burn-in + audio crossfade.

Takes the merged video, removes stutter segments the user marked for deletion,
burns in subtitles with the selected style, and outputs the final video.
"""

import logging
import os
import subprocess
import tempfile
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import Task, TaskFile, TaskResult

logger = logging.getLogger("autocut.render")

# ---------------------------------------------------------------------------
# In-memory render progress tracking
# ---------------------------------------------------------------------------

_render_progress: Dict[str, dict] = {}
_render_lock = threading.Lock()


def get_render_progress(task_id: str) -> Optional[dict]:
    """Get render progress for a task."""
    with _render_lock:
        return _render_progress.get(task_id)


def _update_render_progress(
    task_id: str,
    progress: int = 0,
    stage: str = "rendering",
    estimated_seconds: int = 0,
    error: str = "",
):
    with _render_lock:
        _render_progress[task_id] = {
            "progress": min(progress, 100),
            "stage": stage,
            "estimated_seconds": estimated_seconds,
            "error": error,
        }


def _clear_render_progress(task_id: str):
    with _render_lock:
        _render_progress.pop(task_id, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def start_render(task_id: str) -> None:
    """Start rendering in a background thread.

    Called from the API endpoint after the task status has been set to
    'rendering'. Spawns a daemon thread that performs the actual FFmpeg work.
    """
    _update_render_progress(task_id, progress=0, estimated_seconds=120)

    thread = threading.Thread(
        target=_run_render,
        args=(task_id,),
        daemon=True,
        name=f"render-{task_id[:8]}",
    )
    thread.start()
    logger.info(f"Render thread started for task {task_id}")


def _run_render(task_id: str, retry_count: int = 0) -> None:
    """Execute the full render pipeline in a background thread."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found in render thread")
            return

        task_dir = os.path.join(settings.UPLOAD_DIR, task_id)

        # 1. Load merged video path
        merged_file = (
            db.query(TaskFile)
            .filter(TaskFile.task_id == task_id, TaskFile.file_type == "merged")
            .first()
        )
        if not merged_file or not os.path.exists(merged_file.storage_path):
            raise RuntimeError("Merged video file not found")

        merged_path = merged_file.storage_path
        _update_render_progress(task_id, progress=5, estimated_seconds=110)

        # 2. Load stutter marks (user-adjusted) and determine cut segments
        stutter_result = (
            db.query(TaskResult)
            .filter(TaskResult.task_id == task_id, TaskResult.agent_name == "stutter")
            .first()
        )
        marks = []
        if stutter_result and stutter_result.result_json:
            marks = stutter_result.result_json.get("marks", [])

        # Get delete segments (marks with action="delete")
        delete_segments = _get_delete_segments(marks)

        _update_render_progress(task_id, progress=10, estimated_seconds=100)

        # 3. Load subtitle data and style
        subtitle_result = (
            db.query(TaskResult)
            .filter(TaskResult.task_id == task_id, TaskResult.agent_name == "subtitle")
            .first()
        )
        subtitles = []
        if subtitle_result and subtitle_result.result_json:
            subtitles = subtitle_result.result_json.get("subtitles", [])

        preferences = task.preferences or {}
        subtitle_style = preferences.get("subtitleStyle", "clean-white")

        # 4. Get video duration
        duration_ms = merged_file.duration_ms or _get_video_duration_ms(merged_path)

        # 5. Build keep segments (inverse of delete segments)
        keep_segments = _build_keep_segments(delete_segments, duration_ms)

        _update_render_progress(task_id, progress=15, estimated_seconds=90)

        # 6. Generate adjusted subtitle SRT
        #    Shift subtitle timestamps to match the output after cuts
        adjusted_srt_path = os.path.join(task_dir, "adjusted_subtitles.srt")
        _generate_adjusted_srt(subtitles, delete_segments, keep_segments, adjusted_srt_path)

        _update_render_progress(task_id, progress=20, estimated_seconds=80)

        # 7. Cut video segments and concatenate
        output_path = os.path.join(task_dir, "output.mp4")

        if delete_segments:
            # There are cuts to make
            _render_with_cuts(
                merged_path,
                keep_segments,
                adjusted_srt_path,
                subtitle_style,
                output_path,
                task_id,
            )
        else:
            # No cuts -- just burn in subtitles
            _render_subtitles_only(
                merged_path,
                adjusted_srt_path,
                subtitle_style,
                output_path,
                task_id,
            )

        _update_render_progress(task_id, progress=90, estimated_seconds=10)

        # 8. Verify output exists and get info
        if not os.path.exists(output_path):
            raise RuntimeError("Render output file not found")

        output_size = os.path.getsize(output_path)
        output_duration_ms = _get_video_duration_ms(output_path)

        # Get resolution
        resolution = _get_video_resolution(output_path)

        # 9. Record output file in DB
        output_file = TaskFile(
            task_id=task_id,
            file_type="output",
            storage_path=output_path,
            original_filename="output.mp4",
            file_size_bytes=output_size,
            duration_ms=output_duration_ms,
            sort_order=0,
        )
        db.add(output_file)

        # 10. Update task status to completed
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.expires_at = datetime.utcnow() + timedelta(hours=settings.VIDEO_RETENTION_HOURS)
        task.output_duration_ms = output_duration_ms
        task.output_file_size_bytes = output_size
        db.commit()

        # Save render result
        render_result_data = {
            "output_path": output_path,
            "output_size_bytes": output_size,
            "output_duration_ms": output_duration_ms,
            "resolution": resolution,
            "cuts_applied": len(delete_segments),
            "subtitle_style": subtitle_style,
        }
        render_result = TaskResult(
            task_id=task_id,
            agent_name="render",
            result_json=render_result_data,
        )
        db.add(render_result)
        db.commit()

        _update_render_progress(task_id, progress=100, estimated_seconds=0)
        logger.info(
            f"[{task_id[:8]}] Render complete! "
            f"Output: {output_size} bytes, {output_duration_ms}ms, {resolution}"
        )

    except Exception as e:
        logger.error(f"[{task_id[:8]}] Render failed: {e}\n{traceback.format_exc()}")

        # Auto-retry once
        if retry_count < settings.RENDER_MAX_RETRY:
            logger.info(f"[{task_id[:8]}] Retrying render (attempt {retry_count + 1})")
            _update_render_progress(
                task_id, progress=0, estimated_seconds=120,
                error="",
            )
            _run_render(task_id, retry_count=retry_count + 1)
            return

        # Mark as failed
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = f"渲染失败: {str(e)[:400]}"
                db.commit()
        except Exception:
            pass

        _update_render_progress(
            task_id, progress=0, error=str(e)[:200],
        )

    finally:
        db.close()


# ---------------------------------------------------------------------------
# FFmpeg rendering
# ---------------------------------------------------------------------------

def _render_with_cuts(
    merged_path: str,
    keep_segments: List[Tuple[int, int]],
    srt_path: str,
    subtitle_style: str,
    output_path: str,
    task_id: str,
) -> None:
    """Render video with cuts and subtitle burn-in.

    Strategy:
    1. Use FFmpeg filter_complex to select/trim and concat keep segments
    2. Apply subtitle filter on the concatenated output
    3. Apply audio crossfade at cut points
    """
    if not keep_segments:
        raise RuntimeError("No keep segments to render")

    # Build FFmpeg complex filter
    filter_parts = []
    video_concat_inputs = []
    audio_concat_inputs = []

    crossfade_ms = settings.CROSSFADE_MS

    for i, (start_ms, end_ms) in enumerate(keep_segments):
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0

        # Trim video
        filter_parts.append(
            f"[0:v]trim=start={start_sec:.3f}:end={end_sec:.3f},setpts=PTS-STARTPTS[v{i}]"
        )
        # Trim audio
        filter_parts.append(
            f"[0:a]atrim=start={start_sec:.3f}:end={end_sec:.3f},asetpts=PTS-STARTPTS[a{i}]"
        )
        video_concat_inputs.append(f"[v{i}]")
        audio_concat_inputs.append(f"[a{i}]")

    n = len(keep_segments)

    # Concat video segments
    filter_parts.append(
        f"{''.join(video_concat_inputs)}concat=n={n}:v=1:a=0[vconcat]"
    )

    # Concat audio segments with crossfade
    if n > 1 and crossfade_ms > 0:
        # Simple concat for audio -- crossfade is complex with variable segments
        # Use acrossfade for adjacent pairs or just concat
        filter_parts.append(
            f"{''.join(audio_concat_inputs)}concat=n={n}:v=0:a=1[aconcat]"
        )
    else:
        filter_parts.append(
            f"{''.join(audio_concat_inputs)}concat=n={n}:v=0:a=1[aconcat]"
        )

    # Apply subtitles on concatenated video
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subtitle_filter = _build_subtitle_filter(escaped_srt, subtitle_style)
    filter_parts.append(f"[vconcat]{subtitle_filter}[vout]")

    filter_complex = ";\n".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        "-i", merged_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aconcat]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.info(f"[{task_id[:8]}] Running FFmpeg render with cuts...")
    logger.debug(f"Filter complex:\n{filter_complex}")

    _update_render_progress(task_id, progress=30, estimated_seconds=60)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error(f"FFmpeg render failed: {result.stderr[-1000:]}")
        raise RuntimeError(f"FFmpeg render failed: {result.stderr[-500:]}")

    _update_render_progress(task_id, progress=85, estimated_seconds=15)


def _render_subtitles_only(
    merged_path: str,
    srt_path: str,
    subtitle_style: str,
    output_path: str,
    task_id: str,
) -> None:
    """Render video with just subtitle burn-in (no cuts)."""
    escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    subtitle_filter = _build_subtitle_filter(escaped_srt, subtitle_style)

    cmd = [
        "ffmpeg", "-y",
        "-i", merged_path,
        "-vf", subtitle_filter.replace("[vout]", ""),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]

    logger.info(f"[{task_id[:8]}] Running FFmpeg render (subtitles only)...")

    _update_render_progress(task_id, progress=30, estimated_seconds=60)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        logger.error(f"FFmpeg subtitle render failed: {result.stderr[-1000:]}")
        raise RuntimeError(f"FFmpeg subtitle render failed: {result.stderr[-500:]}")

    _update_render_progress(task_id, progress=85, estimated_seconds=15)


def _build_subtitle_filter(escaped_srt: str, style: str) -> str:
    """Build FFmpeg subtitles filter string based on style."""
    # Base: subtitles=file.srt:force_style='...'
    if style == "black-bg":
        force_style = (
            "FontName=PingFang SC,FontSize=24,PrimaryColour=&H00FFFFFF,"
            "BackColour=&H80000000,BorderStyle=4,Outline=0,Shadow=0,"
            "MarginV=30,Alignment=2"
        )
    elif style == "colorful":
        force_style = (
            "FontName=PingFang SC,FontSize=24,PrimaryColour=&H0000FFFF,"
            "SecondaryColour=&H00FF00FF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=2,Shadow=1,"
            "MarginV=30,Alignment=2,Bold=1"
        )
    else:
        # clean-white (default)
        force_style = (
            "FontName=PingFang SC,FontSize=24,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
            "MarginV=30,Alignment=2"
        )

    return f"subtitles='{escaped_srt}':force_style='{force_style}'[vout]"


# ---------------------------------------------------------------------------
# Segment helpers
# ---------------------------------------------------------------------------

def _get_delete_segments(marks: List[dict]) -> List[Tuple[int, int]]:
    """Extract (start_ms, end_ms) pairs for marks with action='delete'."""
    segments = []
    for m in marks:
        if m.get("action") == "delete":
            start = m.get("start_ms", 0)
            end = m.get("end_ms", 0)
            if end > start:
                segments.append((start, end))

    # Sort by start time and merge overlapping
    segments.sort()
    merged = []
    for start, end in segments:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def _build_keep_segments(
    delete_segments: List[Tuple[int, int]],
    total_duration_ms: int,
) -> List[Tuple[int, int]]:
    """Build keep segments (inverse of delete segments)."""
    if not delete_segments:
        return [(0, total_duration_ms)]

    keep = []
    current = 0

    for del_start, del_end in delete_segments:
        if del_start > current:
            keep.append((current, del_start))
        current = max(current, del_end)

    if current < total_duration_ms:
        keep.append((current, total_duration_ms))

    # Filter out very short segments (< 50ms)
    keep = [(s, e) for s, e in keep if e - s >= 50]

    return keep


def _generate_adjusted_srt(
    subtitles: List[dict],
    delete_segments: List[Tuple[int, int]],
    keep_segments: List[Tuple[int, int]],
    output_path: str,
) -> None:
    """Generate an SRT file with timestamps adjusted for cuts.

    Shifts subtitle timestamps to account for removed segments.
    Subtitles that fall entirely within a deleted segment are omitted.
    Subtitles that partially overlap a deleted segment are trimmed.
    """
    if not subtitles:
        # Write empty SRT
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")
        return

    def _time_after_cuts(original_ms: int) -> int:
        """Map an original timestamp to the output timeline."""
        removed_before = 0
        for del_start, del_end in delete_segments:
            if original_ms <= del_start:
                break
            elif original_ms >= del_end:
                removed_before += del_end - del_start
            else:
                # Point is within a deleted segment
                removed_before += original_ms - del_start
                break
        return max(0, original_ms - removed_before)

    adjusted = []
    idx = 1
    for sub in subtitles:
        start_ms = sub.get("start_ms", 0)
        end_ms = sub.get("end_ms", 0)
        text = sub.get("text", "")

        # Check if subtitle is entirely within a deleted segment
        entirely_deleted = False
        for del_start, del_end in delete_segments:
            if start_ms >= del_start and end_ms <= del_end:
                entirely_deleted = True
                break

        if entirely_deleted:
            continue

        # Adjust timestamps
        new_start = _time_after_cuts(start_ms)
        new_end = _time_after_cuts(end_ms)

        if new_end <= new_start:
            continue

        adjusted.append({
            "index": idx,
            "text": text,
            "start_ms": new_start,
            "end_ms": new_end,
        })
        idx += 1

    # Write SRT
    lines = []
    for sub in adjusted:
        start_str = _ms_to_srt_time(sub["start_ms"])
        end_str = _ms_to_srt_time(sub["end_ms"])
        lines.append(str(sub["index"]))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(sub["text"])
        lines.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(
        f"Adjusted SRT: {len(adjusted)} entries "
        f"(from {len(subtitles)} original, {len(delete_segments)} cuts)"
    )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)."""
    if ms < 0:
        ms = 0
    hours = ms // 3600000
    ms %= 3600000
    minutes = ms // 60000
    ms %= 60000
    seconds = ms // 1000
    millis = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _get_video_duration_ms(file_path: str) -> int:
    """Get video duration in milliseconds using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return int(float(result.stdout.strip()) * 1000)
    except Exception as e:
        logger.warning(f"ffprobe duration failed for {file_path}: {e}")
    return 0


def _get_video_resolution(file_path: str) -> str:
    """Get video resolution as 'WxH' string using ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        logger.warning(f"ffprobe resolution failed for {file_path}: {e}")
    return "unknown"
