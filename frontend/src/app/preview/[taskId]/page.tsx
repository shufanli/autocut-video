"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  Loader2,
  RotateCcw,
  ChevronRight,
  Scissors,
  AlertCircle,
} from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/toast";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WordSegment {
  text: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
}

interface StutterMark {
  type: "filler" | "repeat" | "pause";
  text: string;
  start_ms: number;
  end_ms: number;
  word_indices: number[];
  action: "delete" | "keep";
  duration_ms: number;
}

interface StutterStats {
  total_marks: number;
  deleted_count: number;
  deleted_duration_ms: number;
  filler_count: number;
  repeat_count: number;
  pause_count: number;
}

interface SubtitleEntry {
  index: number;
  text: string;
  start_ms: number;
  end_ms: number;
  word_indices: number[];
}

interface PreviewData {
  task_id: string;
  status: string;
  words: WordSegment[];
  stutter_marks: StutterMark[];
  stutter_stats: StutterStats;
  subtitles: SubtitleEntry[];
  subtitle_style: string;
}

type SubtitleStyle = "clean-white" | "black-bg" | "colorful";

const SUBTITLE_STYLES: { key: SubtitleStyle; name: string; description: string }[] = [
  { key: "clean-white", name: "简洁白字", description: "白色字体，底部阴影" },
  { key: "black-bg", name: "黑底白字", description: "半透明黑色背景条" },
  { key: "colorful", name: "彩色高亮", description: "渐变色高亮文字" },
];

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PreviewPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.taskId as string;
  const { token } = useAuth();
  const { showToast } = useToast();

  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subtitleStyle, setSubtitleStyle] = useState<SubtitleStyle>("clean-white");
  const [isSaving, setIsSaving] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  // Local stutter marks state for interactive toggling
  const [marks, setMarks] = useState<StutterMark[]>([]);

  // Fetch preview data on mount
  useEffect(() => {
    if (!token || !taskId) return;

    const fetchPreview = async () => {
      try {
        const res = await fetch(`/api/tasks/${taskId}/preview`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          if (res.status === 404) {
            showToast("任务不存在", "error");
            router.push("/upload");
            return;
          }
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || "加载预览数据失败");
        }

        const data: PreviewData = await res.json();
        setPreviewData(data);
        setMarks(data.stutter_marks);
        setSubtitleStyle(data.subtitle_style as SubtitleStyle);
      } catch (err) {
        const message = err instanceof Error ? err.message : "加载失败";
        setError(message);
        showToast(message, "error");
      } finally {
        setLoading(false);
      }
    };

    fetchPreview();
  }, [token, taskId, router, showToast]);

  // Toggle a stutter mark between delete/keep
  const toggleMark = useCallback((markIndex: number) => {
    setMarks((prev) =>
      prev.map((m, i) =>
        i === markIndex
          ? { ...m, action: m.action === "delete" ? "keep" : "delete" }
          : m
      )
    );
  }, []);

  // Compute live stats from current marks state
  const liveStats = useMemo(() => {
    const deletedCount = marks.filter((m) => m.action === "delete").length;
    const deletedDurationMs = marks
      .filter((m) => m.action === "delete")
      .reduce((sum, m) => sum + m.duration_ms, 0);
    return {
      total_marks: marks.length,
      deleted_count: deletedCount,
      deleted_duration_ms: deletedDurationMs,
    };
  }, [marks]);

  // Build a word-index to stutter-mark-index map for quick lookup
  const wordToMarkIndex = useMemo(() => {
    const map = new Map<number, number>();
    marks.forEach((mark, markIdx) => {
      for (const wi of mark.word_indices) {
        map.set(wi, markIdx);
      }
    });
    return map;
  }, [marks]);

  // Save adjustments to server
  const saveAdjustments = useCallback(async () => {
    if (!token || !taskId) return;
    setIsSaving(true);

    try {
      const stutterUpdates = marks.map((m, i) => ({
        index: i,
        action: m.action,
      }));

      const res = await fetch(`/api/tasks/${taskId}/preview`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          stutter_updates: stutterUpdates,
          subtitle_style: subtitleStyle,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "保存失败");
      }

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "保存失败";
      showToast(message, "error");
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [token, taskId, marks, subtitleStyle, showToast]);

  // Confirm and start rendering
  const handleConfirmRender = useCallback(async () => {
    setIsConfirming(true);

    // Save adjustments first
    const saved = await saveAdjustments();
    if (!saved) {
      setIsConfirming(false);
      return;
    }

    // Navigate to rendering page (Sprint 6 will implement the actual rendering)
    // For now, navigate to processing page as the rendering placeholder
    router.push(`/processing/${taskId}`);
  }, [saveAdjustments, router, taskId]);

  // Reprocess: go back to upload page
  const handleReprocess = useCallback(() => {
    router.push("/upload");
  }, [router]);

  // Loading state
  if (loading) {
    return (
      <AuthGuard>
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-sm text-text-secondary">加载预览数据...</p>
          </div>
        </div>
      </AuthGuard>
    );
  }

  // Error state
  if (error || !previewData) {
    return (
      <AuthGuard>
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-danger mx-auto mb-3" />
            <p className="text-lg font-semibold text-text-primary mb-2">
              加载失败
            </p>
            <p className="text-sm text-text-secondary mb-4">
              {error || "无法加载预览数据"}
            </p>
            <button
              onClick={() => router.push("/upload")}
              className="px-6 py-2 rounded-md text-sm font-medium bg-primary text-white hover:bg-primary-hover transition-colors duration-150"
            >
              返回上传页
            </button>
          </div>
        </div>
      </AuthGuard>
    );
  }

  const words = previewData.words;

  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="max-w-5xl mx-auto">
          {/* Page header */}
          <div className="mb-6 lg:mb-8">
            <h1 className="text-2xl font-bold text-text-primary">预览与审核</h1>
            <p className="text-sm text-text-secondary mt-1">
              审核口误标记，调整字幕样式，确认后开始渲染
            </p>
          </div>

          {/* Main content: two-column on desktop */}
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Left column: transcript with stutter marks */}
            <div className="flex-1 lg:w-[60%]">
              <TranscriptPanel
                words={words}
                marks={marks}
                wordToMarkIndex={wordToMarkIndex}
                onToggleMark={toggleMark}
              />
            </div>

            {/* Right column: subtitle style settings */}
            <div className="lg:w-[40%]">
              <SubtitleStylePanel
                currentStyle={subtitleStyle}
                onStyleChange={setSubtitleStyle}
              />
            </div>
          </div>

          {/* Bottom stats */}
          <div className="mt-6">
            <StutterStatsBar stats={liveStats} />
          </div>

          {/* Bottom action bar */}
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-border">
            <button
              onClick={handleReprocess}
              className="w-full sm:w-auto px-6 py-3 rounded-md text-sm font-medium border border-border text-gray-700 hover:bg-surface transition-colors duration-150"
            >
              <span className="flex items-center justify-center gap-2">
                <RotateCcw className="w-4 h-4" />
                重新处理
              </span>
            </button>

            <button
              onClick={handleConfirmRender}
              disabled={isConfirming || isSaving}
              className="w-full sm:w-auto px-8 py-3 rounded-md text-base font-medium bg-primary text-white hover:bg-primary-hover transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isConfirming || isSaving ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {isSaving ? "保存中..." : "跳转中..."}
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  确认，开始渲染
                  <ChevronRight className="w-4 h-4" />
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}


// ---------------------------------------------------------------------------
// Transcript Panel
// ---------------------------------------------------------------------------

function TranscriptPanel({
  words,
  marks,
  wordToMarkIndex,
  onToggleMark,
}: {
  words: WordSegment[];
  marks: StutterMark[];
  wordToMarkIndex: Map<number, number>;
  onToggleMark: (markIndex: number) => void;
}) {
  // Build a set of word indices that belong to "pause" type marks
  // Pauses have no word_indices, so we render them between words
  const pauseMarks = marks
    .map((m, idx) => ({ ...m, markIndex: idx }))
    .filter((m) => m.type === "pause");

  // Build pause-after map: after which word index should we insert a pause mark?
  // A pause starts at word[i].end_ms, so it comes after word i
  const pauseAfterWord = new Map<number, { mark: StutterMark; markIndex: number }>();
  for (const pm of pauseMarks) {
    // Find the word whose end_ms matches the pause start_ms
    for (let i = 0; i < words.length; i++) {
      if (words[i].end_ms === pm.start_ms || (words[i].end_ms <= pm.start_ms && (i + 1 >= words.length || words[i + 1].start_ms >= pm.end_ms))) {
        pauseAfterWord.set(i, { mark: pm, markIndex: pm.markIndex });
        break;
      }
    }
  }

  return (
    <div className="bg-white border border-border rounded-lg p-4 sm:p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Scissors className="w-5 h-5 text-primary" />
        <h2 className="text-lg font-semibold text-text-primary">文字稿</h2>
      </div>

      <p className="text-xs text-text-secondary mb-4">
        点击红色标记可切换&ldquo;删除/保留&rdquo;状态
      </p>

      <div className="text-base leading-relaxed">
        {words.map((word, wordIdx) => {
          const markIdx = wordToMarkIndex.get(wordIdx);
          const mark = markIdx !== undefined ? marks[markIdx] : null;
          const isStutter = mark !== null;
          const isDeleted = isStutter && mark.action === "delete";
          const isKept = isStutter && mark.action === "keep";

          // For repeat marks with multiple word_indices, only render the
          // stutter styling on the first word index to avoid duplicate highlights
          const isFirstWordInMark =
            mark && mark.word_indices.length > 0
              ? mark.word_indices[0] === wordIdx
              : true;

          // For multi-word marks, render all words in the mark as one clickable group
          // Only add click handler on the first word's wrapper
          const showAsStutter = isStutter && isFirstWordInMark;
          const multiWordTexts =
            mark && isFirstWordInMark && mark.word_indices.length > 1
              ? mark.word_indices.map((wi) => words[wi]?.text || "").join("")
              : null;

          // Skip rendering if this word is part of a multi-word mark but not the first
          if (isStutter && !isFirstWordInMark && mark.word_indices.length > 1) {
            // Check pause after this word even if we skip rendering the word text
            const pauseInfo = pauseAfterWord.get(wordIdx);
            if (pauseInfo) {
              return (
                <PauseMark
                  key={`pause-${wordIdx}`}
                  mark={pauseInfo.mark}
                  markIndex={pauseInfo.markIndex}
                  onToggle={onToggleMark}
                />
              );
            }
            return null;
          }

          const displayText = multiWordTexts || word.text;
          const pauseInfo = pauseAfterWord.get(wordIdx);

          return (
            <span key={wordIdx}>
              {showAsStutter ? (
                <StutterWordMark
                  text={displayText}
                  isDeleted={isDeleted}
                  isKept={isKept}
                  type={mark.type}
                  onClick={() => onToggleMark(markIdx!)}
                />
              ) : (
                <span className="text-text-primary">{word.text}</span>
              )}
              {pauseInfo && (
                <PauseMark
                  mark={pauseInfo.mark}
                  markIndex={pauseInfo.markIndex}
                  onToggle={onToggleMark}
                />
              )}
            </span>
          );
        })}
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Stutter Word Mark (inline clickable)
// ---------------------------------------------------------------------------

function StutterWordMark({
  text,
  isDeleted,
  isKept,
  type,
  onClick,
}: {
  text: string;
  isDeleted: boolean;
  isKept: boolean;
  type: string;
  onClick: () => void;
}) {
  if (isDeleted) {
    return (
      <span
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && onClick()}
        title={`口误类型: ${typeLabel(type)} (点击保留)`}
        className="inline-block cursor-pointer bg-red-100 text-red-600 line-through rounded-sm px-0.5 transition-all duration-200 hover:bg-red-200"
      >
        {text}
      </span>
    );
  }

  if (isKept) {
    return (
      <span
        onClick={onClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && onClick()}
        title={`已保留 (点击删除)`}
        className="inline-block cursor-pointer border-l-2 border-green-500 pl-0.5 text-text-primary rounded-sm transition-all duration-200 hover:bg-green-50"
      >
        {text}
      </span>
    );
  }

  return <span className="text-text-primary">{text}</span>;
}


// ---------------------------------------------------------------------------
// Pause Mark (between words)
// ---------------------------------------------------------------------------

function PauseMark({
  mark,
  markIndex,
  onToggle,
}: {
  mark: StutterMark;
  markIndex: number;
  onToggle: (index: number) => void;
}) {
  const isDeleted = mark.action === "delete";
  const durationSec = (mark.duration_ms / 1000).toFixed(1);

  return (
    <span
      onClick={() => onToggle(markIndex)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onToggle(markIndex)}
      title={isDeleted ? "长停顿将被删除 (点击保留)" : "长停顿已保留 (点击删除)"}
      className={`inline-block cursor-pointer mx-1 px-1.5 py-0.5 rounded text-xs font-mono transition-all duration-200 ${
        isDeleted
          ? "bg-red-100 text-red-500 line-through hover:bg-red-200"
          : "bg-green-50 text-green-600 border-l-2 border-green-500 hover:bg-green-100"
      }`}
    >
      [停顿 {durationSec}s]
    </span>
  );
}


// ---------------------------------------------------------------------------
// Subtitle Style Panel
// ---------------------------------------------------------------------------

function SubtitleStylePanel({
  currentStyle,
  onStyleChange,
}: {
  currentStyle: SubtitleStyle;
  onStyleChange: (style: SubtitleStyle) => void;
}) {
  return (
    <div className="bg-white border border-border rounded-lg p-4 sm:p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-text-primary mb-4">字幕样式</h2>

      {/* Style preview */}
      <div className="mb-4 rounded-lg overflow-hidden">
        <SubtitlePreview style={currentStyle} />
      </div>

      {/* Style selector */}
      <div className="space-y-3">
        {SUBTITLE_STYLES.map((style) => (
          <button
            key={style.key}
            onClick={() => onStyleChange(style.key)}
            className={`w-full text-left px-4 py-3 rounded-lg border transition-all duration-200 ${
              currentStyle === style.key
                ? "border-primary bg-blue-50 ring-1 ring-primary"
                : "border-border hover:border-gray-300 hover:bg-surface"
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">
                  {style.name}
                </p>
                <p className="text-xs text-text-secondary mt-0.5">
                  {style.description}
                </p>
              </div>
              {currentStyle === style.key && (
                <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-3 h-3 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={3}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Subtitle Preview (visual mockup)
// ---------------------------------------------------------------------------

function SubtitlePreview({ style }: { style: SubtitleStyle }) {
  const sampleText = "AI 自动识别并生成字幕";

  return (
    <div className="relative bg-gray-800 rounded-lg aspect-video flex items-end justify-center pb-6 px-4">
      {/* Simulated video background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-700 to-gray-900 rounded-lg" />

      {/* Play button overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
          <div className="w-0 h-0 border-l-[16px] border-l-white/80 border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent ml-1" />
        </div>
      </div>

      {/* Subtitle text */}
      <div className="relative z-10">
        {style === "clean-white" && (
          <p
            className="text-white text-sm sm:text-base font-medium text-center"
            style={{ textShadow: "0 2px 4px rgba(0,0,0,0.8)" }}
          >
            {sampleText}
          </p>
        )}
        {style === "black-bg" && (
          <p className="text-white text-sm sm:text-base font-medium text-center bg-black/70 px-4 py-1.5 rounded">
            {sampleText}
          </p>
        )}
        {style === "colorful" && (
          <p
            className="text-sm sm:text-base font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-yellow-300 via-pink-400 to-purple-400"
            style={{ textShadow: "none" }}
          >
            {sampleText}
          </p>
        )}
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Stutter Stats Bar
// ---------------------------------------------------------------------------

function StutterStatsBar({
  stats,
}: {
  stats: { total_marks: number; deleted_count: number; deleted_duration_ms: number };
}) {
  const deletedSeconds = (stats.deleted_duration_ms / 1000).toFixed(1);

  return (
    <div className="bg-surface border border-border rounded-lg px-4 py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <Scissors className="w-4 h-4 text-text-secondary" />
        <span className="text-sm text-text-secondary">
          共检测到{" "}
          <span className="font-semibold text-text-primary">
            {stats.total_marks}
          </span>{" "}
          处口误，预计缩短{" "}
          <span className="font-semibold text-text-primary">
            {deletedSeconds}
          </span>{" "}
          秒
        </span>
      </div>
      <div className="text-xs text-text-secondary">
        当前删除 {stats.deleted_count} 处 / 共 {stats.total_marks} 处
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function typeLabel(type: string): string {
  switch (type) {
    case "filler":
      return "填充词";
    case "repeat":
      return "重复";
    case "pause":
      return "长停顿";
    default:
      return type;
  }
}
