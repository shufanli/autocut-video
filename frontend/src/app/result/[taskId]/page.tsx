"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  CheckCircle,
  Download,
  Upload,
  Loader2,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  Clock,
  HardDrive,
  Monitor,
  Scissors,
  RotateCcw,
} from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/toast";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ResultInfo {
  task_id: string;
  status: string;
  duration_ms: number;
  file_size_bytes: number;
  resolution: string;
  subtitle_style: string;
  cuts_applied: number;
  completed_at: string;
  expires_at: string;
  expired: boolean;
  video_url: string;
  download_url: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDuration(ms: number): string {
  if (ms <= 0) return "0:00";
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function formatFileSize(bytes: number): string {
  if (bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ResultPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.taskId as string;
  const { token } = useAuth();
  const { showToast } = useToast();

  const [resultInfo, setResultInfo] = useState<ResultInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);

  // Fetch result info
  useEffect(() => {
    if (!token || !taskId) return;

    const fetchResult = async () => {
      try {
        const res = await fetch(`/api/tasks/${taskId}/result`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          if (res.status === 404) {
            showToast("任务不存在", "error");
            router.push("/upload");
            return;
          }
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || "加载结果失败");
        }

        const data: ResultInfo = await res.json();
        setResultInfo(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : "加载失败";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [token, taskId, router, showToast]);

  // Handle download
  const handleDownload = useCallback(async () => {
    if (!token || !taskId) return;
    setIsDownloading(true);

    try {
      const res = await fetch(`/api/tasks/${taskId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "下载失败");
      }

      // Create blob and trigger download
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `autocut_${taskId.slice(0, 8)}.mp4`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast("视频开始下载", "success");
    } catch (err) {
      const message = err instanceof Error ? err.message : "下载失败";
      showToast(message, "error");
    } finally {
      setIsDownloading(false);
    }
  }, [token, taskId, showToast]);

  // Handle feedback
  const handleFeedback = useCallback(
    async (rating: "up" | "down") => {
      if (!token || !taskId || feedbackSubmitted) return;

      setFeedback(rating);

      try {
        const res = await fetch(`/api/tasks/${taskId}/feedback`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ rating }),
        });

        if (res.ok) {
          setFeedbackSubmitted(true);
          showToast("感谢您的反馈!", "success");
        }
      } catch {
        // Feedback submission failure is not critical
      }
    },
    [token, taskId, feedbackSubmitted, showToast],
  );

  // Handle render retry (if task is failed)
  const handleRetry = useCallback(async () => {
    if (!token || !taskId) return;
    setIsRetrying(true);

    try {
      const res = await fetch(`/api/tasks/${taskId}/render`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (res.ok) {
        showToast("重新渲染已开始", "success");
        router.push(`/processing/${taskId}`);
      } else {
        const data = await res.json().catch(() => ({}));
        showToast(data.detail || "重试失败", "error");
      }
    } catch {
      showToast("网络错误，请稍后重试", "error");
    } finally {
      setIsRetrying(false);
    }
  }, [token, taskId, router, showToast]);

  // Loading state
  if (loading) {
    return (
      <AuthGuard>
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-sm text-text-secondary">加载视频信息...</p>
          </div>
        </div>
      </AuthGuard>
    );
  }

  // Error / render failed state
  if (error) {
    return (
      <AuthGuard>
        <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
          <div className="text-center max-w-md">
            <AlertCircle className="w-12 h-12 text-danger mx-auto mb-3" />
            <p className="text-lg font-semibold text-text-primary mb-2">
              {error.includes("渲染失败") ? "渲染失败" : "加载失败"}
            </p>
            <p className="text-sm text-text-secondary mb-6">{error}</p>
            <div className="flex items-center justify-center gap-4">
              <button
                onClick={() => router.push("/upload")}
                className="px-6 py-3 rounded-md text-sm font-medium border border-border text-gray-700 hover:bg-surface transition-colors duration-150"
              >
                返回上传页
              </button>
              {error.includes("渲染失败") && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="px-6 py-3 rounded-md text-sm font-medium bg-primary text-white hover:bg-primary-hover transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isRetrying ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      重试中...
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-4 h-4" />
                      重试渲染
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </AuthGuard>
    );
  }

  if (!resultInfo) return null;

  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="max-w-3xl mx-auto">
          {/* Success header */}
          <div className="text-center mb-8">
            <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-text-primary">
              视频已完成!
            </h1>
            <p className="text-sm text-text-secondary mt-2">
              您的视频已处理完毕，可以预览和下载
            </p>
          </div>

          {/* Video player card */}
          <div className="bg-white border border-border rounded-lg shadow-sm overflow-hidden mb-6">
            {/* Video player */}
            <div className="bg-black aspect-video relative">
              <video
                ref={videoRef}
                className="w-full h-full"
                controls
                preload="metadata"
                playsInline
                src={`/api/tasks/${taskId}/stream`}
                crossOrigin="anonymous"
              >
                <track
                  kind="subtitles"
                  src={`/api/tasks/${taskId}/subtitles.vtt`}
                  srcLang="zh"
                  label="中文字幕"
                  default
                />
                <p className="text-white text-center p-4">
                  您的浏览器不支持视频播放
                </p>
              </video>
            </div>

            {/* Video info */}
            <div className="p-4 sm:p-6">
              {/* Info grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-text-secondary flex-shrink-0" />
                  <div>
                    <p className="text-xs text-text-secondary">时长</p>
                    <p className="text-sm font-semibold text-text-primary font-mono">
                      {formatDuration(resultInfo.duration_ms)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <HardDrive className="w-4 h-4 text-text-secondary flex-shrink-0" />
                  <div>
                    <p className="text-xs text-text-secondary">文件大小</p>
                    <p className="text-sm font-semibold text-text-primary font-mono">
                      {formatFileSize(resultInfo.file_size_bytes)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-text-secondary flex-shrink-0" />
                  <div>
                    <p className="text-xs text-text-secondary">分辨率</p>
                    <p className="text-sm font-semibold text-text-primary font-mono">
                      {resultInfo.resolution !== "unknown"
                        ? resultInfo.resolution
                        : "--"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-text-secondary flex-shrink-0" />
                  <div>
                    <p className="text-xs text-text-secondary">口误剪切</p>
                    <p className="text-sm font-semibold text-text-primary font-mono">
                      {resultInfo.cuts_applied} 处
                    </p>
                  </div>
                </div>
              </div>

              {/* Download button */}
              <button
                onClick={handleDownload}
                disabled={isDownloading || resultInfo.expired}
                className="
                  w-full py-3 rounded-md text-base font-medium
                  bg-primary text-white hover:bg-primary-hover
                  transition-colors duration-150
                  disabled:opacity-50 disabled:cursor-not-allowed
                  flex items-center justify-center gap-2
                "
              >
                {isDownloading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    下载中...
                  </>
                ) : resultInfo.expired ? (
                  <>
                    <AlertCircle className="w-5 h-5" />
                    视频已过期
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5" />
                    下载视频
                  </>
                )}
              </button>

              {/* Expiry warning */}
              {!resultInfo.expired && (
                <p className="text-xs text-text-secondary text-center mt-3">
                  视频将在 24 小时后自动删除，请及时下载
                </p>
              )}
              {resultInfo.expired && (
                <p className="text-xs text-danger text-center mt-3">
                  视频已过期删除，请重新处理
                </p>
              )}
            </div>
          </div>

          {/* Satisfaction feedback */}
          <div className="bg-white border border-border rounded-lg shadow-sm p-4 sm:p-6 mb-6">
            <p className="text-sm font-medium text-text-primary text-center mb-4">
              {feedbackSubmitted
                ? "感谢您的反馈!"
                : "对处理结果满意吗?"}
            </p>
            <div className="flex items-center justify-center gap-6">
              <button
                onClick={() => handleFeedback("up")}
                disabled={feedbackSubmitted}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium
                  transition-all duration-200
                  ${
                    feedback === "up"
                      ? "bg-green-100 text-green-700 border border-green-300"
                      : "border border-border text-text-secondary hover:bg-surface hover:text-text-primary"
                  }
                  ${feedbackSubmitted && feedback !== "up" ? "opacity-40" : ""}
                  disabled:cursor-not-allowed
                `}
              >
                <ThumbsUp
                  className={`w-5 h-5 ${
                    feedback === "up" ? "fill-green-600 text-green-600" : ""
                  }`}
                />
                满意
              </button>
              <button
                onClick={() => handleFeedback("down")}
                disabled={feedbackSubmitted}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium
                  transition-all duration-200
                  ${
                    feedback === "down"
                      ? "bg-red-100 text-red-700 border border-red-300"
                      : "border border-border text-text-secondary hover:bg-surface hover:text-text-primary"
                  }
                  ${feedbackSubmitted && feedback !== "down" ? "opacity-40" : ""}
                  disabled:cursor-not-allowed
                `}
              >
                <ThumbsDown
                  className={`w-5 h-5 ${
                    feedback === "down" ? "fill-red-600 text-red-600" : ""
                  }`}
                />
                不满意
              </button>
            </div>
          </div>

          {/* New video button */}
          <div className="text-center">
            <button
              onClick={() => router.push("/upload")}
              className="
                px-8 py-3 rounded-md text-sm font-medium
                border border-border text-gray-700
                hover:bg-surface transition-colors duration-150
                inline-flex items-center gap-2
              "
            >
              <Upload className="w-4 h-4" />
              处理新视频
            </button>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
