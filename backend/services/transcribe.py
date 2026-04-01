"""Stage 1 -- Speech-to-text using SiliconFlow / OpenAI Whisper API or mock fallback.

Output format: list of word-level segments:
    [{"text": "...", "start_ms": int, "end_ms": int, "confidence": float}, ...]

Strategy (priority order):
    1. If SILICONFLOW_API_KEY is set, use SiliconFlow API (OpenAI-compatible).
       - Preferred model: TeleAI/TeleSpeechASR (returns segment-level timestamps).
       - Fallback: FunAudioLLM/SenseVoiceSmall (text-only, no timestamps).
    2. If OPENAI_API_KEY is set, use the OpenAI API (whisper-1 model with word timestamps).
    3. Otherwise, generate a mock transcript for development/testing.

Timestamp quality hierarchy:
    - word-level (OpenAI whisper-1 with timestamp_granularities[]=word): best
    - segment-level (TeleSpeechASR): good -- segments are split into Chinese
      words using a regex-based tokenizer that respects word boundaries
    - text-only (SenseVoiceSmall): poor -- timestamps are synthesized uniformly

For Chinese, segment text is split into meaningful word units (2-4 chars)
instead of individual characters, giving much better timestamp accuracy
for stutter detection and subtitle generation.
"""

import logging
import math
import os
import re
import subprocess
from typing import List, TypedDict

logger = logging.getLogger("autocut.transcribe")


class WordSegment(TypedDict):
    text: str
    start_ms: int
    end_ms: int
    confidence: float


# ---------------------------------------------------------------------------
# Chinese word segmentation (regex-based, no external dependency)
# ---------------------------------------------------------------------------

# Common Chinese words that should be kept as atomic units for tokenization.
# Ordered longest-first for greedy matching in the forward maximum match algorithm.
_CHINESE_WORD_DICT: set = set()
_CHINESE_MAX_WORD_LEN = 1

def _init_word_dict():
    """Initialize the Chinese word dictionary for tokenization."""
    global _CHINESE_WORD_DICT, _CHINESE_MAX_WORD_LEN
    words = [
        # 4-char common phrases
        "也就是说", "不知不觉", "了不起的", "越来越多",
        # 3-char fillers / common words
        "比如说", "也就是", "怎么说", "聊一聊", "想一想", "看一看", "说一说",
        "试一试", "等一下", "差不多", "不一定", "所以说", "对不对", "创作者",
        "过程中", "不知道",
        # 2-char words -- high frequency in spoken Chinese
        # Fillers / conjunctions
        "那个", "就是", "然后", "因为", "所以", "但是", "不过", "或者",
        "可以", "这个", "那么", "什么", "怎么", "如果", "虽然", "已经",
        "可能", "应该", "其实", "本来", "确实", "大概", "一般", "特别",
        "非常", "真的", "简单", "复杂", "基本", "比较", "稍微",
        # Pronouns
        "我们", "你们", "他们", "她们", "大家", "自己", "别人",
        # Numbers / quantifiers
        "一个", "一些", "一起", "一样", "一直", "一定",
        # Time
        "现在", "以前", "之后", "以后", "今天", "明天", "昨天",
        # Domain words (video editing)
        "视频", "剪辑", "内容", "创作", "素材", "字幕", "口播",
        "录制", "处理", "自动", "口误", "工具", "帮助", "问题",
        # Common verbs / nouns
        "时候", "地方", "开始", "结束", "继续", "需要", "觉得",
        "知道", "喜欢", "使用", "方法", "过程", "结果", "效果",
        "大量", "关于", "话题", "很多", "每天", "难免",
        "出现", "重复", "词语", "停顿", "开发", "这些",
        "成功", "失败", "生活", "工作", "学习", "发展", "研究",
        "经验", "技术", "能力", "机会", "选择", "感觉", "认为",
        "以为", "觉得", "希望", "支持", "反正", "而且", "不是",
        "没有", "不会", "不能", "不要", "还是", "只是", "只有",
        "就是", "可是", "于是", "所有", "任何", "每个", "这样",
        "那样", "怎样", "多少", "为什么", "哪里", "什么样",
        "别的", "这种", "那种", "各种", "有时", "最后", "首先",
        "同时", "当时", "平时", "及时", "随时",
        "东西", "事情", "朋友", "世界", "社会", "国家",
        "看到", "听到", "想到", "做到", "得到", "找到",
        "这么", "那么", "怎么", "多么",
    ]
    _CHINESE_WORD_DICT = set(words)
    _CHINESE_MAX_WORD_LEN = max(len(w) for w in words) if words else 1

_init_word_dict()

# Pattern for non-CJK tokens
_NON_CJK_PATTERN = re.compile(
    r"[a-zA-Z]+(?:'[a-zA-Z]+)?"  # English word
    r"|[0-9]+(?:\.[0-9]+)?"       # number
)


def _segment_chinese_text(text: str) -> List[str]:
    """Split Chinese text into word-like units using forward maximum matching.

    Uses a dictionary-based approach (forward maximum match) which is the
    standard baseline for Chinese word segmentation. Known words in the
    dictionary are matched greedily (longest match first). Unknown sequences
    fall back to single-character tokens.

    This is much better than character-level splitting for timestamp
    distribution because Chinese words are typically 2-4 characters.

    Examples:
        "大家好今天我们来聊一聊" -> ["大家", "好", "今天", "我们", "来", "聊一聊"]
        "视频剪辑的话题" -> ["视频", "剪辑", "的", "话题"]
        "嗯就是然后那个" -> ["嗯", "就是", "然后", "那个"]
    """
    text = text.strip()
    if not text:
        return []

    tokens: List[str] = []
    i = 0
    n = len(text)

    while i < n:
        char = text[i]

        # Skip whitespace
        if char.isspace():
            i += 1
            continue

        # Handle non-CJK characters (English, numbers, punctuation)
        if not ('\u4e00' <= char <= '\u9fff'):
            m = _NON_CJK_PATTERN.match(text, i)
            if m:
                tokens.append(m.group())
                i = m.end()
            else:
                # Skip punctuation -- it should not be a separate word segment.
                # Chinese and ASCII punctuation: ，。！？、；：""''（）【】…—·,.!?;:
                i += 1
            continue

        # Forward maximum matching for CJK characters
        matched = False
        max_len = min(_CHINESE_MAX_WORD_LEN, n - i)
        for length in range(max_len, 1, -1):
            candidate = text[i:i + length]
            if candidate in _CHINESE_WORD_DICT:
                tokens.append(candidate)
                i += length
                matched = True
                break

        if not matched:
            # Single CJK character (not part of any known word)
            tokens.append(char)
            i += 1

    return tokens


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transcribe_audio(
    video_path: str,
    openai_api_key: str = "",
    siliconflow_api_key: str = "",
    siliconflow_model: str = "TeleAI/TeleSpeechASR",
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1/audio/transcriptions",
) -> List[WordSegment]:
    """Transcribe a video/audio file to word-level segments.

    Args:
        video_path: Path to the video file (mp4, mov, webm).
        openai_api_key: OpenAI API key. If empty, falls back to mock.
        siliconflow_api_key: SiliconFlow API key. Takes priority over OpenAI.
        siliconflow_model: Model name for SiliconFlow.
            Recommended: "TeleAI/TeleSpeechASR" (has timestamps).
        siliconflow_base_url: SiliconFlow transcription endpoint URL.

    Returns:
        List of WordSegment dicts with word-level timestamps.
    """
    if siliconflow_api_key:
        logger.info(f"Using SiliconFlow API for transcription (model={siliconflow_model})")
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
    """Transcribe using an OpenAI-compatible Whisper API with best available timestamps.

    Works with both OpenAI and SiliconFlow APIs. Automatically picks the best
    timestamp granularity available from the response.

    Args:
        video_path: Path to the video file.
        api_key: API key for authentication.
        api_url: Full URL to the transcriptions endpoint.
        model: Model name.
        provider: Provider name for logging.
    """
    import httpx

    # Extract audio first
    audio_path = _extract_audio(video_path)

    try:
        with open(audio_path, "rb") as audio_file:
            # Build request -- always request verbose_json for timestamps
            data = {
                "model": model,
                "response_format": "verbose_json",
                "language": "zh",
                # Request word-level timestamps. Supported by OpenAI whisper-1.
                # SiliconFlow models may ignore this but it doesn't cause errors.
                "timestamp_granularities[]": "word",
            }

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
        logger.info(
            f"{provider} API response keys: {list(resp_data.keys())}, "
            f"text length: {len(resp_data.get('text', ''))}"
        )

        # Strategy 1: Word-level timestamps (best quality, OpenAI whisper-1)
        words = resp_data.get("words", [])
        if words:
            segments = _parse_word_level(words)
            logger.info(
                f"{provider}: {len(segments)} word-level segments (best quality)"
            )
            return segments

        # Strategy 2: Segment-level timestamps (TeleSpeechASR, local whisper)
        # Split segment text into Chinese words for better granularity
        api_segments = resp_data.get("segments", [])
        if api_segments:
            segments = _parse_segment_level(api_segments)
            logger.info(
                f"{provider}: {len(segments)} word segments from "
                f"{len(api_segments)} API segments (word-tokenized)"
            )
            # Log a sample for debugging
            if segments:
                sample = segments[:5]
                logger.info(
                    f"  Sample: {[(s['text'], s['start_ms'], s['end_ms']) for s in sample]}"
                )
            return segments

        # Strategy 3: Text-only fallback (SenseVoiceSmall)
        full_text = resp_data.get("text", "")
        if full_text:
            logger.warning(
                f"{provider} returned text only (no timestamps). "
                f"Consider switching to TeleAI/TeleSpeechASR for timestamp support. "
                f"Synthesizing segments from text."
            )
            duration_ms = _get_duration_ms(video_path)
            segments = _synthesize_segments_from_text(full_text, duration_ms)
            logger.info(
                f"{provider}: {len(segments)} synthesized segments (low quality)"
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
    """Parse OpenAI-style word-level timestamp data.

    OpenAI whisper-1 with timestamp_granularities[]=word returns:
        {"words": [{"word": "hello", "start": 0.0, "end": 0.5}, ...]}
    """
    segments: List[WordSegment] = []
    for w in words:
        text = w.get("word", "").strip()
        if not text:
            continue
        segments.append(
            WordSegment(
                text=text,
                start_ms=int(w.get("start", 0) * 1000),
                end_ms=int(w.get("end", 0) * 1000),
                confidence=round(w.get("confidence", 0.9), 3),
            )
        )
    return segments


def _parse_segment_level(api_segments: list) -> List[WordSegment]:
    """Parse segment-level timestamps and split into word-level units.

    SiliconFlow TeleSpeechASR and similar models return segments like:
        [{"start": 0.0, "end": 2.5, "text": "大家好今天我们来聊一聊"}]

    Instead of the old approach (splitting by individual character and
    distributing time evenly), we now:
    1. Tokenize the text into meaningful Chinese word units (2-4 chars)
    2. Distribute time proportionally to word length
    3. This gives much better timestamps for stutter detection and subtitles

    If a segment contains only a single short word, it is kept as-is with
    the segment's original timestamps -- this is the best case.
    """
    segments: List[WordSegment] = []

    for seg in api_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start_s = seg.get("start", 0.0)
        end_s = seg.get("end", 0.0)
        confidence = seg.get("confidence", seg.get("avg_logprob", 0.0))

        # Normalize confidence
        if confidence is None:
            confidence = 0.9
        if confidence < 0:
            confidence = min(1.0, max(0.0, math.exp(confidence)))
        if confidence <= 0:
            confidence = 0.9

        start_ms = int(start_s * 1000)
        end_ms = int(end_s * 1000)
        total_ms = max(1, end_ms - start_ms)

        # Tokenize into Chinese words
        words = _segment_chinese_text(text)
        if not words:
            continue

        # If the segment is already a single word, use exact timestamps
        if len(words) == 1:
            segments.append(
                WordSegment(
                    text=words[0],
                    start_ms=start_ms,
                    end_ms=end_ms,
                    confidence=round(confidence, 3),
                )
            )
            continue

        # Distribute time proportionally to character count of each word.
        # Chinese words with more characters typically take longer to speak.
        total_chars = sum(len(w) for w in words)
        if total_chars == 0:
            continue

        current_ms = start_ms
        for i, word in enumerate(words):
            # Proportional duration based on character count
            word_chars = len(word)
            word_duration = int(total_ms * word_chars / total_chars)

            # Ensure minimum duration of 50ms per word
            word_duration = max(50, word_duration)

            w_start = current_ms
            w_end = min(w_start + word_duration, end_ms)

            # Last word gets the remaining time to avoid rounding gaps
            if i == len(words) - 1:
                w_end = end_ms

            segments.append(
                WordSegment(
                    text=word,
                    start_ms=w_start,
                    end_ms=w_end,
                    confidence=round(confidence, 3),
                )
            )
            current_ms = w_end

    return segments


def _synthesize_segments_from_text(text: str, duration_ms: int) -> List[WordSegment]:
    """Create synthetic segments from plain text when no timestamps are available.

    Uses word-level tokenization instead of character-level for better grouping.
    """
    if duration_ms <= 0:
        duration_ms = 60000

    words = _segment_chinese_text(text)
    if not words:
        return []

    # Reserve 200ms margin at start and end
    usable_ms = duration_ms - 400
    if usable_ms <= 0:
        usable_ms = duration_ms

    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        return []

    segments: List[WordSegment] = []
    current_ms = 200

    for i, word in enumerate(words):
        word_chars = len(word)
        word_duration = int(usable_ms * word_chars / total_chars)
        word_duration = max(80, word_duration)

        start_ms = current_ms
        end_ms = start_ms + word_duration
        if end_ms > duration_ms - 200:
            break

        segments.append(
            WordSegment(
                text=word,
                start_ms=start_ms,
                end_ms=end_ms,
                confidence=0.5,  # low confidence for synthesized timestamps
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
