"""Stage 0 -- Merge multiple video files using FFmpeg concat.

If there is only one source file, skip concat and just copy/symlink it
as the merged output.
"""

import os
import logging
import subprocess
import tempfile
from typing import List

logger = logging.getLogger("autocut.merge")


def merge_videos(source_paths: List[str], output_path: str) -> str:
    """Merge one or more video files into a single output file.

    Args:
        source_paths: Ordered list of absolute paths to source video files.
        output_path: Absolute path for the merged output file (e.g. .../merged.mp4).

    Returns:
        The output_path on success.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    if not source_paths:
        raise RuntimeError("No source files to merge")

    # Single file -- just copy it (no re-encoding needed)
    if len(source_paths) == 1:
        src = source_paths[0]
        if not os.path.exists(src):
            raise RuntimeError(f"Source file not found: {src}")
        # Use FFmpeg copy to normalize container to mp4
        cmd = [
            "ffmpeg", "-y",
            "-i", src,
            "-c", "copy",
            output_path,
        ]
        logger.info(f"Single file copy: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error(f"FFmpeg copy failed: {result.stderr}")
            raise RuntimeError(f"FFmpeg copy failed: {result.stderr[-500:]}")
        return output_path

    # Multiple files -- use concat demuxer
    # Create a temporary concat list file
    concat_dir = os.path.dirname(output_path)
    concat_list_path = os.path.join(concat_dir, "concat_list.txt")

    with open(concat_list_path, "w") as f:
        for src in source_paths:
            if not os.path.exists(src):
                raise RuntimeError(f"Source file not found: {src}")
            # FFmpeg concat requires escaped single quotes in paths
            escaped = src.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_path,
    ]
    logger.info(f"Concat merge: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Cleanup concat list
    try:
        os.remove(concat_list_path)
    except OSError:
        pass

    if result.returncode != 0:
        logger.error(f"FFmpeg concat failed: {result.stderr}")
        raise RuntimeError(f"FFmpeg concat failed: {result.stderr[-500:]}")

    return output_path


def get_video_duration_ms(file_path: str) -> int:
    """Get video duration in milliseconds using ffprobe.

    Returns 0 if ffprobe fails.
    """
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
            seconds = float(result.stdout.strip())
            return int(seconds * 1000)
    except Exception as e:
        logger.warning(f"ffprobe failed for {file_path}: {e}")
    return 0
