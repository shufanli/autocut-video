"""Stage 2 -- Stutter / disfluency detection rule engine.

Detects three categories:
    1. Filler words (e.g. "嗯", "啊", "那个", "就是", "然后")
    2. Repeated words (consecutive identical or near-identical words)
    3. Long pauses (gaps between words exceeding threshold)

Output: list of stutter marks with type, time range, and suggested action.

Design notes (word-level vs character-level input):
    The transcription stage now returns word-level segments (e.g. "大家", "视频")
    instead of individual characters. This means:
    - Filler detection matches whole word text against the filler list
    - Repeat detection compares adjacent word texts for equality
    - Pause detection uses the gap between word[i].end_ms and word[i+1].start_ms
    All three benefit from accurate word-level timestamps from TeleSpeechASR.
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


# Extended filler word list for Chinese oral speech.
# These are words that speakers insert unconsciously. When detected as
# standalone segments, they are candidates for deletion.
CHINESE_FILLER_WORDS = [
    # Single-char fillers / interjections
    "嗯", "啊", "呃", "哦", "噢", "哈", "嘿", "唉", "哎", "呀",
    "吧", "呢", "吗", "哇", "嗯嗯",
    # 2-char filler phrases (spoken unconsciously, not carrying meaning)
    "那个", "就是", "然后", "这个", "对对", "嗯嗯",
    # 3-char common fillers
    "就是说", "怎么说", "也就是",
]


def detect_stutters(
    words: List[WordSegment],
    filler_words: Optional[List[str]] = None,
    long_pause_threshold_ms: Optional[int] = None,
) -> List[StutterMark]:
    """Run all stutter detection rules on a list of word segments.

    Args:
        words: List of word segments from transcription.
        filler_words: Custom filler word list. Defaults to config + extended list.
        long_pause_threshold_ms: Custom pause threshold. Defaults to config.

    Returns:
        List of StutterMark dicts, sorted by start_ms.
    """
    if filler_words is None:
        # Merge config filler words with our extended list (deduplicated)
        filler_words = list(set(settings.FILLER_WORDS + CHINESE_FILLER_WORDS))
    if long_pause_threshold_ms is None:
        long_pause_threshold_ms = settings.LONG_PAUSE_THRESHOLD_MS

    marks: List[StutterMark] = []

    # Rule 1: Filler words
    marks.extend(_detect_fillers(words, filler_words))

    # Rule 2: Repeated words
    marks.extend(_detect_repeats(words, filler_words))

    # Rule 3: Long pauses
    marks.extend(_detect_long_pauses(words, long_pause_threshold_ms))

    # Deduplicate: a word index should only appear in one mark.
    # Filler detection and repeat detection may overlap (e.g. "那个 那个"
    # could be flagged as both filler and repeat). Prefer the repeat mark
    # since it captures more context.
    marks = _deduplicate_marks(marks)

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
    """Detect filler words like "嗯", "啊", "那个", etc.

    A filler is only marked for deletion if it appears as a standalone word
    segment. This avoids false positives where "那个" is part of a meaningful
    phrase like "那个人很好".

    Additional heuristic: very short filler segments (< 200ms) at sentence
    boundaries are more likely true fillers.
    """
    marks: List[StutterMark] = []
    filler_set = set(filler_words)

    for i, word in enumerate(words):
        text = word["text"].strip()
        if text in filler_set:
            # Context check: if the filler is surrounded by content words
            # with very short gaps, it might be part of normal speech flow.
            # We still mark it but could adjust confidence.
            duration = word["end_ms"] - word["start_ms"]

            marks.append(
                StutterMark(
                    type="filler",
                    text=text,
                    start_ms=word["start_ms"],
                    end_ms=word["end_ms"],
                    word_indices=[i],
                    action="delete",
                    duration_ms=duration,
                )
            )

    return marks


def _detect_repeats(
    words: List[WordSegment],
    filler_words: List[str],
) -> List[StutterMark]:
    """Detect consecutive repeated words (stammering).

    Examples of patterns detected:
        "录制 录制" -> marks the second "录制" as repeat
        "这个 嗯 这个" -> marks "嗯 这个" as repeat (filler + repeated word)
        "我 我 我们" -> marks the first two "我" as repeats

    For Chinese text, we also handle partial repeats where a word appears
    as a prefix of the next word (e.g. "我 我们" is a common stutter pattern).
    """
    marks: List[StutterMark] = []
    if len(words) < 2:
        return marks

    filler_set = set(filler_words)
    used_indices: set = set()  # Track indices already marked

    i = 0
    while i < len(words) - 1:
        if i in used_indices:
            i += 1
            continue

        current_text = words[i]["text"].strip()
        if not current_text:
            i += 1
            continue

        # Pattern 1: Direct repeat "X X" -> mark second X for deletion
        next_text = words[i + 1]["text"].strip()
        if current_text == next_text and i + 1 not in used_indices:
            # Check for triple+ repeats: "X X X ..."
            repeat_end = i + 1
            while (
                repeat_end + 1 < len(words)
                and words[repeat_end + 1]["text"].strip() == current_text
                and repeat_end + 1 not in used_indices
            ):
                repeat_end += 1

            # Mark all repeated instances (keep the first one)
            for j in range(i + 1, repeat_end + 1):
                marks.append(
                    StutterMark(
                        type="repeat",
                        text=words[j]["text"].strip(),
                        start_ms=words[j]["start_ms"],
                        end_ms=words[j]["end_ms"],
                        word_indices=[j],
                        action="delete",
                        duration_ms=words[j]["end_ms"] - words[j]["start_ms"],
                    )
                )
                used_indices.add(j)

            i = repeat_end + 1
            continue

        # Pattern 2: Repeat with filler in between "X filler X"
        if i + 2 < len(words) and i + 1 not in used_indices and i + 2 not in used_indices:
            middle_text = words[i + 1]["text"].strip()
            after_text = words[i + 2]["text"].strip()
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
                used_indices.add(i + 1)
                used_indices.add(i + 2)
                i += 3
                continue

        # Pattern 3: Partial repeat / self-correction "我 我们" (keep "我们", delete "我")
        # Only for single-char words that are a prefix of the next word
        if (
            len(current_text) == 1
            and len(next_text) > 1
            and next_text.startswith(current_text)
            and i not in used_indices
        ):
            marks.append(
                StutterMark(
                    type="repeat",
                    text=current_text,
                    start_ms=words[i]["start_ms"],
                    end_ms=words[i]["end_ms"],
                    word_indices=[i],
                    action="delete",
                    duration_ms=words[i]["end_ms"] - words[i]["start_ms"],
                )
            )
            used_indices.add(i)
            i += 2
            continue

        i += 1

    return marks


def _detect_long_pauses(
    words: List[WordSegment],
    threshold_ms: int,
) -> List[StutterMark]:
    """Detect long pauses (silence gaps) between words.

    A pause is the gap between word[i].end_ms and word[i+1].start_ms.
    If the gap exceeds the threshold, we mark it for shortening.

    Note: With TeleSpeechASR segment-level timestamps, pauses between
    segments are accurately captured. Pauses within a segment (between
    tokenized words) are estimated and may be less accurate.
    """
    marks: List[StutterMark] = []
    if len(words) < 2:
        return marks

    for i in range(len(words) - 1):
        gap_start = words[i]["end_ms"]
        gap_end = words[i + 1]["start_ms"]
        gap_ms = gap_end - gap_start

        if gap_ms >= threshold_ms:
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


def _deduplicate_marks(marks: List[StutterMark]) -> List[StutterMark]:
    """Remove duplicate marks that reference the same word indices.

    When a word is flagged by both filler and repeat detection, keep the
    repeat mark (more informative) and remove the filler mark.
    """
    # Group marks by their word indices
    index_to_marks: dict = {}
    for mark in marks:
        for idx in mark["word_indices"]:
            if idx not in index_to_marks:
                index_to_marks[idx] = []
            index_to_marks[idx].append(mark)

    # Find marks to remove (filler marks that overlap with repeat marks)
    to_remove: set = set()
    for idx, idx_marks in index_to_marks.items():
        if len(idx_marks) > 1:
            has_repeat = any(m["type"] == "repeat" for m in idx_marks)
            if has_repeat:
                for m in idx_marks:
                    if m["type"] == "filler":
                        to_remove.add(id(m))

    return [m for m in marks if id(m) not in to_remove]


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
