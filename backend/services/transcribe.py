"""Stage 1 -- Speech-to-text using OpenAI Whisper API or mock fallback.

Output format: list of word-level segments:
    [{"text": "...", "start_ms": int, "end_ms": int, "confidence": float}, ...]

Strategy:
    1. If OPENAI_API_KEY is set, use the OpenAI API (whisper-1 model).
    2. Otherwise, generate a mock transcript for development/testing.
"""

import json
import logging
import os
import subprocess
from typing import List, TypedDict

logger = logging.getLogger("autocut.transcribe")


class WordSegment(TypedDict):
    text: str
    start_ms: int
    end_ms: int
    confidence: float


def transcribe_audio(
    video_path: str,
    openai_api_key: str = "",
) -> List[WordSegment]:
    """Transcribe a video/audio file to word-level segments.

    Args:
        video_path: Path to the video file (mp4, mov, webm).
        openai_api_key: OpenAI API key. If empty, uses mock transcript.

    Returns:
        List of WordSegment dicts with word-level timestamps.
    """
    if openai_api_key:
        return _transcribe_openai(video_path, openai_api_key)
    else:
        logger.info("No OPENAI_API_KEY set, using mock transcript")
        return _transcribe_mock(video_path)


def _extract_audio(video_path: str) -> str:
    """Extract audio from video to a temporary WAV file using FFmpeg.

    Returns the path to the extracted audio file.
    """
    audio_dir = os.path.dirname(video_path)
    audio_path = os.path.join(audio_dir, "audio_extracted.wav")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",                    # no video
        "-acodec", "pcm_s16le",   # WAV format
        "-ar", "16000",           # 16kHz sample rate (Whisper optimal)
        "-ac", "1",               # mono
        audio_path,
    ]
    logger.info(f"Extracting audio: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error(f"Audio extraction failed: {result.stderr}")
        raise RuntimeError(f"Audio extraction failed: {result.stderr[-500:]}")

    return audio_path


def _transcribe_openai(video_path: str, api_key: str) -> List[WordSegment]:
    """Transcribe using OpenAI Whisper API with word-level timestamps."""
    import httpx

    # Extract audio first (OpenAI accepts various formats, but WAV is safest)
    audio_path = _extract_audio(video_path)

    try:
        # Use httpx to call OpenAI API directly (no openai SDK dependency)
        with open(audio_path, "rb") as audio_file:
            response = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": ("audio.wav", audio_file, "audio/wav")},
                data={
                    "model": "whisper-1",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                    "language": "zh",
                },
                timeout=300.0,
            )

        if response.status_code != 200:
            logger.error(f"OpenAI API error {response.status_code}: {response.text}")
            raise RuntimeError(f"OpenAI Whisper API error: {response.status_code}")

        data = response.json()
        words = data.get("words", [])

        segments: List[WordSegment] = []
        for w in words:
            segments.append(
                WordSegment(
                    text=w.get("word", ""),
                    start_ms=int(w.get("start", 0) * 1000),
                    end_ms=int(w.get("end", 0) * 1000),
                    confidence=round(w.get("confidence", 0.9), 3),
                )
            )

        logger.info(f"OpenAI transcription: {len(segments)} word segments")
        return segments

    finally:
        # Cleanup audio file
        try:
            os.remove(audio_path)
        except OSError:
            pass


def _transcribe_mock(video_path: str) -> List[WordSegment]:
    """Generate a realistic mock transcript for testing.

    Simulates a typical oral presentation with some filler words and pauses.
    """
    # Try to get video duration for realistic timing
    duration_ms = _get_duration_ms(video_path)
    if duration_ms <= 0:
        duration_ms = 60000  # Default 60 seconds

    # Mock transcript simulating a typical oral delivery
    mock_text_items = [
        ("大家好", 0.95),
        ("嗯", 0.88),
        ("今天", 0.96),
        ("我们", 0.97),
        ("来", 0.95),
        ("聊一聊", 0.94),
        ("那个", 0.85),
        ("关于", 0.96),
        ("视频", 0.97),
        ("剪辑", 0.95),
        ("的", 0.98),
        ("话题", 0.96),
        # pause
        ("就是", 0.82),
        ("很多", 0.94),
        ("创作者", 0.96),
        ("啊", 0.80),
        ("他们", 0.95),
        ("每天", 0.97),
        ("都", 0.96),
        ("需要", 0.95),
        ("录制", 0.94),
        ("大量", 0.96),
        ("的", 0.98),
        ("口播", 0.93),
        ("内容", 0.95),
        # pause
        ("然后", 0.83),
        ("但是", 0.96),
        ("在", 0.97),
        ("录制", 0.94),
        ("录制", 0.88),  # repeated word (stutter)
        ("过程中", 0.93),
        ("难免", 0.94),
        ("会", 0.97),
        ("出现", 0.96),
        ("一些", 0.95),
        ("口误", 0.94),
        # pause
        ("嗯", 0.79),
        ("比如说", 0.93),
        ("重复", 0.95),
        ("的", 0.98),
        ("词语", 0.94),
        ("或者", 0.96),
        ("是", 0.97),
        ("那个", 0.81),
        ("一些", 0.95),
        ("停顿", 0.94),
        # pause
        ("所以", 0.96),
        ("我们", 0.97),
        ("开发", 0.95),
        ("了", 0.98),
        ("这个", 0.96),
        ("工具", 0.94),
        ("来", 0.97),
        ("帮助", 0.96),
        ("大家", 0.95),
        ("自动", 0.96),
        ("处理", 0.95),
        ("这些", 0.94),
        ("问题", 0.96),
    ]

    # Distribute words across the video duration
    total_words = len(mock_text_items)
    # Average word duration
    avg_word_ms = min(400, duration_ms // (total_words + 5))
    # Inter-word gap
    gap_ms = max(50, (duration_ms - avg_word_ms * total_words) // (total_words + 1))

    segments: List[WordSegment] = []
    current_ms = 200  # Start at 200ms

    # Insert some longer pauses at specific points
    pause_after_indices = {11, 24, 35, 49}  # After certain words

    for i, (text, confidence) in enumerate(mock_text_items):
        word_duration = int(avg_word_ms * (0.8 + 0.4 * (len(text) / 3)))
        word_duration = max(150, min(word_duration, 800))

        start_ms = current_ms
        end_ms = start_ms + word_duration

        # Don't exceed video duration
        if end_ms > duration_ms - 200:
            end_ms = min(end_ms, duration_ms - 200)
            if end_ms <= start_ms:
                break

        segments.append(
            WordSegment(
                text=text,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=confidence,
            )
        )

        current_ms = end_ms + gap_ms

        # Add longer pause after certain segments
        if i in pause_after_indices:
            current_ms += 1800  # 1.8 second pause

    logger.info(f"Mock transcription: {len(segments)} word segments over {duration_ms}ms")
    return segments


def _get_duration_ms(video_path: str) -> int:
    """Get video duration using ffprobe. Returns 0 on failure."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return int(float(result.stdout.strip()) * 1000)
    except Exception as e:
        logger.warning(f"ffprobe failed: {e}")
    return 0
