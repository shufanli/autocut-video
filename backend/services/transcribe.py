"""Stage 1 -- Speech-to-text using SiliconFlow / OpenAI Whisper API or mock fallback.

Output format: list of word-level segments:
    [{"text": "...", "start_ms": int, "end_ms": int, "confidence": float}, ...]

Strategy (priority order):
    1. If SILICONFLOW_API_KEY is set, use SiliconFlow API (OpenAI-compatible).
    2. If OPENAI_API_KEY is set, use the OpenAI API (whisper-1 model).
    3. Otherwise, generate a mock transcript for development/testing.
"""

import logging
import math
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
    siliconflow_api_key: str = "",
    siliconflow_model: str = "FunAudioLLM/SenseVoiceSmall",
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1/audio/transcriptions",
) -> List[WordSegment]:
    """Transcribe a video/audio file to word-level segments.

    Args:
        video_path: Path to the video file (mp4, mov, webm).
        openai_api_key: OpenAI API key. If empty, falls back to mock.
        siliconflow_api_key: SiliconFlow API key. Takes priority over OpenAI.
        siliconflow_model: Model name for SiliconFlow (e.g. FunAudioLLM/SenseVoiceSmall).
        siliconflow_base_url: SiliconFlow transcription endpoint URL.

    Returns:
        List of WordSegment dicts with word-level timestamps.
    """
    if siliconflow_api_key:
        logger.info("Using SiliconFlow API for transcription")
        return _transcribe_whisper_api(
            video_path,
            api_key=siliconflow_api_key,
            api_url=siliconflow_base_url,
            model=siliconflow_model,
            provider="SiliconFlow",
        )
    elif openai_api_key:
        logger.info("Using OpenAI API for transcription")
        return _transcribe_whisper_api(
            video_path,
            api_key=openai_api_key,
            api_url="https://api.openai.com/v1/audio/transcriptions",
            model="whisper-1",
            provider="OpenAI",
        )
    else:
        logger.info("No API key set, using mock transcript")
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


def _transcribe_whisper_api(
    video_path: str,
    api_key: str,
    api_url: str,
    model: str,
    provider: str,
) -> List[WordSegment]:
    """Transcribe using an OpenAI-compatible Whisper API with word-level timestamps.

    Works with both OpenAI and SiliconFlow APIs since SiliconFlow is OpenAI-compatible.

    Args:
        video_path: Path to the video file.
        api_key: API key for authentication.
        api_url: Full URL to the transcriptions endpoint.
        model: Model name (e.g. 'whisper-1' for OpenAI, 'FunAudioLLM/SenseVoiceSmall' for SiliconFlow).
        provider: Provider name for logging (e.g. 'OpenAI', 'SiliconFlow').
    """
    import httpx

    # Extract audio first
    audio_path = _extract_audio(video_path)

    try:
        with open(audio_path, "rb") as audio_file:
            # Build request data -- SiliconFlow accepts the same format as OpenAI
            data = {
                "model": model,
                "response_format": "verbose_json",
                "language": "zh",
            }

            # timestamp_granularities is supported by OpenAI; SiliconFlow may
            # or may not support it depending on the model. We include it for
            # OpenAI and try with SiliconFlow -- if the response lacks word-level
            # timestamps we fall back to segment-level parsing.
            if provider == "OpenAI":
                data["timestamp_granularities[]"] = "word"

            logger.info(
                f"Calling {provider} API: url={api_url}, model={model}"
            )

            response = httpx.post(
                api_url,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": ("audio.wav", audio_file, "audio/wav")},
                data=data,
                timeout=300.0,
            )

        if response.status_code != 200:
            logger.error(
                f"{provider} API error {response.status_code}: {response.text}"
            )
            raise RuntimeError(
                f"{provider} Whisper API error: {response.status_code} - {response.text[:500]}"
            )

        resp_data = response.json()
        logger.info(f"{provider} API response keys: {list(resp_data.keys())}")

        # Try word-level timestamps first (OpenAI format)
        words = resp_data.get("words", [])
        if words:
            segments = _parse_word_level(words)
            logger.info(
                f"{provider} transcription: {len(segments)} word-level segments"
            )
            return segments

        # Fall back to segment-level timestamps (common in SiliconFlow responses)
        api_segments = resp_data.get("segments", [])
        if api_segments:
            segments = _parse_segment_level(api_segments)
            logger.info(
                f"{provider} transcription: {len(segments)} segments from segment-level data"
            )
            return segments

        # Last resort: just use the full text with estimated timestamps
        full_text = resp_data.get("text", "")
        if full_text:
            logger.warning(
                f"{provider} returned text only (no timestamps), synthesizing segments"
            )
            duration_ms = _get_duration_ms(video_path)
            segments = _synthesize_segments_from_text(full_text, duration_ms)
            logger.info(
                f"{provider} transcription: {len(segments)} synthesized segments"
            )
            return segments

        logger.error(f"{provider} returned empty response: {resp_data}")
        raise RuntimeError(f"{provider} returned empty transcription result")

    finally:
        # Cleanup audio file
        try:
            os.remove(audio_path)
        except OSError:
            pass


def _parse_word_level(words: list) -> List[WordSegment]:
    """Parse OpenAI-style word-level timestamp data."""
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
    return segments


def _parse_segment_level(api_segments: list) -> List[WordSegment]:
    """Parse segment-level timestamp data and split into character-level segments.

    SiliconFlow and some Whisper implementations return segments like:
    [{"start": 0.0, "end": 2.5, "text": "..."}]

    We split segment text into individual characters (for Chinese) or words
    (for other languages) and distribute timestamps evenly.
    """
    segments: List[WordSegment] = []

    for seg in api_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start_s = seg.get("start", 0.0)
        end_s = seg.get("end", 0.0)
        confidence = seg.get("confidence", seg.get("avg_logprob", 0.0))

        # Normalize confidence: avg_logprob is typically negative (-0.x),
        # convert to 0..1 range
        if confidence < 0:
            # log prob to probability: roughly exp(logprob)
            confidence = min(1.0, max(0.0, math.exp(confidence)))

        # If confidence is missing or zero, default to 0.9
        if confidence <= 0:
            confidence = 0.9

        start_ms = int(start_s * 1000)
        end_ms = int(end_s * 1000)
        total_ms = end_ms - start_ms

        # Split Chinese text into individual characters for word-level granularity
        # For short segments, keep as-is
        chars = list(text)
        if len(chars) == 0:
            continue

        char_duration = max(1, total_ms // len(chars))

        for i, char in enumerate(chars):
            if char.strip() == "":
                continue
            c_start = start_ms + i * char_duration
            c_end = min(c_start + char_duration, end_ms)
            segments.append(
                WordSegment(
                    text=char,
                    start_ms=c_start,
                    end_ms=c_end,
                    confidence=round(confidence, 3),
                )
            )

    return segments


def _synthesize_segments_from_text(text: str, duration_ms: int) -> List[WordSegment]:
    """Create synthetic segments from plain text when no timestamps are available."""
    if duration_ms <= 0:
        duration_ms = 60000

    chars = [c for c in text if c.strip()]
    if not chars:
        return []

    char_duration = max(1, duration_ms // (len(chars) + 1))
    segments: List[WordSegment] = []
    current_ms = 200

    for char in chars:
        start_ms = current_ms
        end_ms = start_ms + char_duration
        if end_ms > duration_ms - 200:
            break
        segments.append(
            WordSegment(
                text=char,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=0.85,
            )
        )
        current_ms = end_ms

    return segments


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
