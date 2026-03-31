"""Stage 3 -- Subtitle generation from word-level timestamps.

Groups words into subtitle lines and generates SRT format output.
Each subtitle line is capped at a maximum character count and duration.
"""

import logging
import os
from typing import List, TypedDict

logger = logging.getLogger("autocut.subtitle")

MAX_CHARS_PER_LINE = 18  # Max Chinese characters per subtitle line
MAX_DURATION_MS = 5000   # Max duration for a single subtitle (5s)
MIN_DURATION_MS = 500    # Min duration for a single subtitle


class WordSegment(TypedDict):
    text: str
    start_ms: int
    end_ms: int
    confidence: float


class SubtitleEntry(TypedDict):
    index: int
    text: str
    start_ms: int
    end_ms: int
    word_indices: List[int]  # indices into the original word segments


def generate_subtitles(words: List[WordSegment]) -> List[SubtitleEntry]:
    """Group word segments into subtitle entries.

    Each subtitle contains up to MAX_CHARS_PER_LINE characters and spans
    no more than MAX_DURATION_MS milliseconds.

    Args:
        words: List of word-level segments from transcription.

    Returns:
        List of SubtitleEntry dicts.
    """
    if not words:
        return []

    subtitles: List[SubtitleEntry] = []
    current_text = ""
    current_start_ms = words[0]["start_ms"]
    current_word_indices: List[int] = []

    for i, word in enumerate(words):
        text = word["text"].strip()
        if not text:
            continue

        tentative_text = current_text + text
        tentative_end = word["end_ms"]
        tentative_duration = tentative_end - current_start_ms

        # Check if adding this word exceeds limits
        should_break = (
            len(tentative_text) > MAX_CHARS_PER_LINE
            or tentative_duration > MAX_DURATION_MS
        )

        if should_break and current_text:
            # Flush current subtitle
            subtitles.append(
                SubtitleEntry(
                    index=len(subtitles) + 1,
                    text=current_text,
                    start_ms=current_start_ms,
                    end_ms=words[current_word_indices[-1]]["end_ms"],
                    word_indices=list(current_word_indices),
                )
            )
            # Start new subtitle with current word
            current_text = text
            current_start_ms = word["start_ms"]
            current_word_indices = [i]
        else:
            current_text = tentative_text
            current_word_indices.append(i)

    # Flush remaining
    if current_text and current_word_indices:
        subtitles.append(
            SubtitleEntry(
                index=len(subtitles) + 1,
                text=current_text,
                start_ms=current_start_ms,
                end_ms=words[current_word_indices[-1]]["end_ms"],
                word_indices=list(current_word_indices),
            )
        )

    logger.info(f"Generated {len(subtitles)} subtitle entries from {len(words)} words")
    return subtitles


def subtitles_to_srt(subtitles: List[SubtitleEntry]) -> str:
    """Convert subtitle entries to SRT format string.

    Args:
        subtitles: List of SubtitleEntry dicts.

    Returns:
        SRT formatted string.
    """
    lines: List[str] = []
    for sub in subtitles:
        start_str = _ms_to_srt_time(sub["start_ms"])
        end_str = _ms_to_srt_time(sub["end_ms"])
        lines.append(str(sub["index"]))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(sub["text"])
        lines.append("")  # blank line separator

    return "\n".join(lines)


def save_srt(subtitles: List[SubtitleEntry], output_path: str) -> str:
    """Save subtitles as an SRT file.

    Args:
        subtitles: List of SubtitleEntry dicts.
        output_path: Absolute path for the .srt file.

    Returns:
        The output_path.
    """
    srt_content = subtitles_to_srt(subtitles)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    logger.info(f"SRT saved to {output_path}")
    return output_path


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
