"""Stage 2 -- Stutter / disfluency detection rule engine.

Detects three categories:
    1. Filler words (e.g. "嗯", "啊", "那个", "就是", "然后")
    2. Repeated words (consecutive identical or near-identical words)
    3. Long pauses (gaps between words exceeding threshold)

Output: list of stutter marks with type, time range, and suggested action.
"""

import logging
from typing import List, Optional, TypedDict, Literal

from config import settings

logger = logging.getLogger("autocut.stutter")


class StutterMark(TypedDict):
    type: Literal["filler", "repeat", "pause"]
    text: str
    start_ms: int
    end_ms: int
    word_indices: List[int]  # indices into the word segments list
    action: Literal["delete", "keep"]  # default suggestion
    duration_ms: int


class WordSegment(TypedDict):
    text: str
    start_ms: int
    end_ms: int
    confidence: float


def detect_stutters(
    words: List[WordSegment],
    filler_words: Optional[List[str]] = None,
    long_pause_threshold_ms: Optional[int] = None,
) -> List[StutterMark]:
    """Run all stutter detection rules on a list of word segments.

    Args:
        words: List of word segments from transcription.
        filler_words: Custom filler word list. Defaults to config.
        long_pause_threshold_ms: Custom pause threshold. Defaults to config.

    Returns:
        List of StutterMark dicts, sorted by start_ms.
    """
    if filler_words is None:
        filler_words = settings.FILLER_WORDS
    if long_pause_threshold_ms is None:
        long_pause_threshold_ms = settings.LONG_PAUSE_THRESHOLD_MS

    marks: List[StutterMark] = []

    # Rule 1: Filler words
    marks.extend(_detect_fillers(words, filler_words))

    # Rule 2: Repeated words
    marks.extend(_detect_repeats(words))

    # Rule 3: Long pauses
    marks.extend(_detect_long_pauses(words, long_pause_threshold_ms))

    # Sort by start_ms
    marks.sort(key=lambda m: m["start_ms"])

    logger.info(
        f"Stutter detection: {len(marks)} marks "
        f"(fillers={sum(1 for m in marks if m['type'] == 'filler')}, "
        f"repeats={sum(1 for m in marks if m['type'] == 'repeat')}, "
        f"pauses={sum(1 for m in marks if m['type'] == 'pause')})"
    )

    return marks


def _detect_fillers(
    words: List[WordSegment],
    filler_words: List[str],
) -> List[StutterMark]:
    """Detect filler words like "嗯", "啊", "那个", etc."""
    marks: List[StutterMark] = []
    filler_set = set(filler_words)

    for i, word in enumerate(words):
        text = word["text"].strip()
        if text in filler_set:
            marks.append(
                StutterMark(
                    type="filler",
                    text=text,
                    start_ms=word["start_ms"],
                    end_ms=word["end_ms"],
                    word_indices=[i],
                    action="delete",
                    duration_ms=word["end_ms"] - word["start_ms"],
                )
            )

    return marks


def _detect_repeats(words: List[WordSegment]) -> List[StutterMark]:
    """Detect consecutive repeated words (stammering).

    E.g. "录制 录制" -> marks the second occurrence as repeat.
    Also handles near-consecutive repeats with a filler word in between.
    """
    marks: List[StutterMark] = []
    if len(words) < 2:
        return marks

    i = 0
    while i < len(words) - 1:
        current_text = words[i]["text"].strip()
        if not current_text:
            i += 1
            continue

        # Check immediate next word
        next_text = words[i + 1]["text"].strip()
        if current_text == next_text:
            # Found repeat -- mark the second (duplicate) word for deletion
            marks.append(
                StutterMark(
                    type="repeat",
                    text=next_text,
                    start_ms=words[i + 1]["start_ms"],
                    end_ms=words[i + 1]["end_ms"],
                    word_indices=[i + 1],
                    action="delete",
                    duration_ms=words[i + 1]["end_ms"] - words[i + 1]["start_ms"],
                )
            )
            i += 2  # Skip the repeated word
            continue

        # Check repeat with one filler word in between
        # e.g. "这个 嗯 这个" -- the filler + second copy should both be marked
        if i + 2 < len(words):
            middle_text = words[i + 1]["text"].strip()
            after_text = words[i + 2]["text"].strip()
            filler_set = set(settings.FILLER_WORDS)
            if current_text == after_text and middle_text in filler_set:
                # Mark both the filler and the repeated word
                marks.append(
                    StutterMark(
                        type="repeat",
                        text=f"{middle_text} {after_text}",
                        start_ms=words[i + 1]["start_ms"],
                        end_ms=words[i + 2]["end_ms"],
                        word_indices=[i + 1, i + 2],
                        action="delete",
                        duration_ms=words[i + 2]["end_ms"] - words[i + 1]["start_ms"],
                    )
                )
                i += 3
                continue

        i += 1

    return marks


def _detect_long_pauses(
    words: List[WordSegment],
    threshold_ms: int,
) -> List[StutterMark]:
    """Detect long pauses (silence gaps) between words.

    A pause is the gap between word[i].end_ms and word[i+1].start_ms.
    If the gap exceeds the threshold, we mark it.
    """
    marks: List[StutterMark] = []
    if len(words) < 2:
        return marks

    for i in range(len(words) - 1):
        gap_start = words[i]["end_ms"]
        gap_end = words[i + 1]["start_ms"]
        gap_ms = gap_end - gap_start

        if gap_ms >= threshold_ms:
            # Target: shorten to PAUSE_SHORTEN_TARGET_MS
            marks.append(
                StutterMark(
                    type="pause",
                    text=f"[停顿 {gap_ms / 1000:.1f}s]",
                    start_ms=gap_start,
                    end_ms=gap_end,
                    word_indices=[],  # Pauses are between words
                    action="delete",
                    duration_ms=gap_ms,
                )
            )

    return marks


def compute_stutter_stats(marks: List[StutterMark]) -> dict:
    """Compute summary statistics for stutter marks.

    Returns:
        {
            "total_marks": int,
            "filler_count": int,
            "repeat_count": int,
            "pause_count": int,
            "total_duration_ms": int,  # total time that would be saved if all deleted
            "deleted_count": int,      # marks with action="delete"
        }
    """
    filler_count = sum(1 for m in marks if m["type"] == "filler")
    repeat_count = sum(1 for m in marks if m["type"] == "repeat")
    pause_count = sum(1 for m in marks if m["type"] == "pause")
    total_duration_ms = sum(m["duration_ms"] for m in marks if m["action"] == "delete")
    deleted_count = sum(1 for m in marks if m["action"] == "delete")

    return {
        "total_marks": len(marks),
        "filler_count": filler_count,
        "repeat_count": repeat_count,
        "pause_count": pause_count,
        "total_duration_ms": total_duration_ms,
        "deleted_count": deleted_count,
    }
