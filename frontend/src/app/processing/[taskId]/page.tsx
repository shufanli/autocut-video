"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { Loader2, XCircle, RotateCcw } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { ProgressSteps, StageInfo } from "@/components/progress-steps";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/toast";

const POLL_INTERVAL_MS = 2000; // Poll every 2 seconds
const TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes

interface TaskStatus {
  task_id: string;
  status: string;
  stage: number;
  stage_name: string;
  stage_key: string;
  progress: number;
  estimated_seconds: number;
  total_stages: number;
  stages: StageInfo[];
  error: string;
  error_message: string | null;
}

export default function ProcessingPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const taskId = params.taskId as string;
  const isRenderMode = searchParams.get("mode") === "render";
  const { token } = useAuth();
  const { showToast } = useToast();

  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isTimedOut, setIsTimedOut] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Track if we've ever seen "rendering" status during this page session.
  // Initialize from URL param so we show the correct UI before the first poll.
  const sawRenderingRef = useRef(isRenderMode);

  const startTimeRef = useRef<number>(Date.now());
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Use refs for router/showToast to keep fetchStatus stable across renders.
  // This prevents useEffect from recreating the interval when these change
  // reference (which can happen on re-renders in Next.js App Router),
  // which was causing the redirect-on-complete logic to be interrupted.
  const routerRef = useRef(router);
  routerRef.current = router;
  const showToastRef = useRef(showToast);
  showToastRef.current = showToast;

  // Guard: once we detect a terminal state and schedule a redirect,
  // stop all further polling immediately so no new intervals can restart it.
  const redirectingRef = useRef(false);

  // Helper: stop polling definitively
  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Poll for status updates.
  // Only token and taskId are true dependencies; router and showToast are
  // accessed via stable refs so they do not cause fetchStatus to be recreated.
  const fetchStatus = useCallback(async () => {
    // If we already detected a terminal state, do nothing
    if (redirectingRef.current) return;
    if (!token || !taskId) return;

    try {
      const res = await fetch(`/api/tasks/${taskId}/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        if (res.status === 404) {
          redirectingRef.current = true;
          stopPolling();
          showToastRef.current("任务不存在", "error");
          routerRef.current.push("/upload");
          return;
        }
        return;
      }

      const data: TaskStatus = await res.json();
      setStatus(data);

      // Track if we've ever seen rendering status
      if (data.status === "rendering") {
        sawRenderingRef.current = true;
      }

      // Check for completion -- redirect to preview (only from initial processing)
      if (data.status === "preview") {
        redirectingRef.current = true;
        stopPolling();
        // Brief delay to show "complete" state before redirect
        setTimeout(() => {
          routerRef.current.push(`/preview/${taskId}`);
        }, 1500);
        return;
      }

      // Rendering complete -- redirect to result/download page
      if (data.status === "completed") {
        redirectingRef.current = true;
        stopPolling();
        setTimeout(() => {
          routerRef.current.push(`/result/${taskId}`);
        }, 1500);
        return;
      }

      // Check for failure
      if (data.status === "failed") {
        redirectingRef.current = true;
        stopPolling();
        return;
      }

      // Check timeout
      if (Date.now() - startTimeRef.current > TIMEOUT_MS) {
        setIsTimedOut(true);
        redirectingRef.current = true;
        stopPolling();
        return;
      }
    } catch {
      // Network error -- keep polling
    }
  }, [token, taskId, stopPolling]);

  // Start polling on mount.
  // Because fetchStatus now only depends on token/taskId (stable values),
  // this effect will not re-run spuriously and recreate the interval.
  useEffect(() => {
    // Reset redirect guard when deps change (e.g. navigating to a new task)
    redirectingRef.current = false;

    fetchStatus(); // Initial fetch
    pollRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [fetchStatus]);

  // Handle retry -- works for both processing and rendering failures
  const handleRetry = useCallback(async () => {
    if (!token || !taskId) return;
    setIsRetrying(true);
    setIsTimedOut(false);

    // Determine retry endpoint based on the error context
    // If the last known status was rendering/failed-during-render, retry render
    // Otherwise retry process
    const wasRendering =
      status?.error_message?.includes("渲染") ||
      status?.stage_key === "rendering";
    const retryEndpoint = wasRendering
      ? `/api/tasks/${taskId}/render`
      : `/api/tasks/${taskId}/process`;

    try {
      const res = await fetch(retryEndpoint, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (res.ok) {
        startTimeRef.current = Date.now();
        redirectingRef.current = false; // Allow polling again after retry
        setStatus(null);
        // Restart polling
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
        showToastRef.current(wasRendering ? "重新渲染已开始" : "已重新开始处理", "success");
      } else {
        const data = await res.json().catch(() => ({}));
        showToastRef.current(data.detail || "重试失败", "error");
      }
    } catch {
      showToastRef.current("网络错误，请稍后重试", "error");
    } finally {
      setIsRetrying(false);
    }
  }, [token, taskId, fetchStatus, status]);

  // Handle cancel
  const handleCancelConfirm = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    router.push("/upload");
  }, [router]);

  // Default stages for initial render
  // Backend has 4 stages but the acceptance criteria specifies 3 visual stages:
  // "合并素材 -> 语音识别 -> 检测口误&生成字幕"
  // So we merge stutter + subtitle into one visual stage.
  const defaultDisplayStages: StageInfo[] = [
    { key: "merge", name: "合并素材", status: "active" },
    { key: "transcribe", name: "语音识别", status: "pending" },
    { key: "stutter_subtitle", name: "检测口误&生成字幕", status: "pending" },
  ];

  // Transform 4 backend stages into 3 display stages
  const stages = _mergeStages(status?.stages || null) || defaultDisplayStages;
  const stageName = status?.stage_name || "合并素材";
  // If stage_key is "subtitle", display combined name
  const displayStageName =
    status?.stage_key === "subtitle" || status?.stage_key === "stutter"
      ? "检测口误&生成字幕"
      : stageName;
  const estimatedSeconds = status?.estimated_seconds ?? 120;
  const isFailed = status?.status === "failed";
  const isComplete = status?.status === "preview" || status?.status === "completed";
  const isRendering = status?.status === "rendering";
  // "wasRendering" is true if we ever saw rendering status OR the completed status came from a render
  const wasRendering = sawRenderingRef.current || isRendering;

  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="max-w-2xl mx-auto">
          {/* Page header */}
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold text-text-primary">
              {isTimedOut
                ? "处理超时"
                : isFailed
                ? (status?.error_message?.includes("渲染") ? "渲染失败" : "处理失败")
                : isComplete
                ? (wasRendering ? "渲染完成" : "处理完成")
                : (isRendering || wasRendering)
                ? "正在渲染您的视频"
                : "正在处理您的视频"}
            </h1>
            {!isTimedOut && !isFailed && !isComplete && (
              <p className="text-sm text-text-secondary mt-2">
                {(isRendering || wasRendering)
                  ? "正在根据您的编辑生成最终视频，请耐心等待"
                  : "AI 正在分析和处理您的视频，请耐心等待"}
              </p>
            )}
          </div>

          {/* Progress card */}
          <div className="bg-white border border-border rounded-lg p-6 sm:p-8 shadow-sm">
            {/* Timeout state */}
            {isTimedOut && (
              <div className="text-center py-8">
                <XCircle className="w-16 h-16 text-warning mx-auto mb-4" />
                <p className="text-lg font-semibold text-text-primary mb-2">
                  处理超时
                </p>
                <p className="text-sm text-text-secondary mb-6">
                  处理时间超过 15 分钟，请重试
                </p>
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="
                    px-6 py-3 rounded-md text-sm font-medium
                    bg-primary text-white hover:bg-primary-hover
                    transition-colors duration-150
                    disabled:opacity-50 disabled:cursor-not-allowed
                    flex items-center gap-2 mx-auto
                  "
                >
                  {isRetrying ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      重试中...
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-4 h-4" />
                      重试
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Failed state */}
            {isFailed && !isTimedOut && (
              <div className="text-center py-8">
                <XCircle className="w-16 h-16 text-danger mx-auto mb-4" />
                <p className="text-lg font-semibold text-text-primary mb-2">
                  {status?.error_message?.includes("渲染") ? "渲染失败" : "处理失败"}
                </p>
                <p className="text-sm text-text-secondary mb-6">
                  {status?.error_message?.includes("渲染")
                    ? "渲染失败，请重试"
                    : status?.error_message || status?.error || "处理过程中出现错误，请重试"}
                </p>
                <div className="flex items-center justify-center gap-4">
                  <button
                    onClick={() => router.push("/upload")}
                    className="
                      px-6 py-3 rounded-md text-sm font-medium
                      border border-border text-gray-700
                      hover:bg-surface transition-colors duration-150
                    "
                  >
                    返回上传页
                  </button>
                  <button
                    onClick={handleRetry}
                    disabled={isRetrying}
                    className="
                      px-6 py-3 rounded-md text-sm font-medium
                      bg-primary text-white hover:bg-primary-hover
                      transition-colors duration-150
                      disabled:opacity-50 disabled:cursor-not-allowed
                      flex items-center gap-2
                    "
                  >
                    {isRetrying ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        重试中...
                      </>
                    ) : (
                      <>
                        <RotateCcw className="w-4 h-4" />
                        重试
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Normal processing state (or complete) -- show when NOT in render mode */}
            {!isTimedOut && !isFailed && !isRendering && !wasRendering && (
              <>
                <ProgressSteps
                  stages={stages}
                  currentStageName={displayStageName}
                  estimatedSeconds={estimatedSeconds}
                />

                {/* Processing animation */}
                {!isComplete && (
                  <div className="mt-8 flex justify-center">
                    <div className="w-full max-w-md">
                      {/* Overall progress bar */}
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                          style={{
                            width: `${_computeOverallProgress(stages, status?.progress || 0)}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Cancel button */}
                {!isComplete && (
                  <div className="mt-8 text-center">
                    <button
                      onClick={() => setShowCancelConfirm(true)}
                      className="
                        text-sm text-text-secondary hover:text-text-primary
                        transition-colors duration-150
                      "
                    >
                      取消处理
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Rendering state -- single progress bar */}
            {!isTimedOut && !isFailed && !isComplete && (isRendering || wasRendering) && (
              <div className="py-6">
                <div className="text-center mb-6">
                  <Loader2 className="w-12 h-12 text-primary animate-spin mx-auto mb-4" />
                  <p className="text-lg font-semibold text-text-primary">
                    正在渲染中...
                  </p>
                  {estimatedSeconds > 0 && (
                    <p className="text-sm text-text-secondary mt-1">
                      预计剩余时间：
                      {estimatedSeconds >= 60
                        ? `${Math.ceil(estimatedSeconds / 60)} 分钟`
                        : `${estimatedSeconds} 秒`}
                    </p>
                  )}
                </div>

                {/* Render progress bar */}
                <div className="w-full max-w-md mx-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-text-secondary">渲染进度</span>
                    <span className="text-sm font-semibold text-primary">
                      {status?.progress ?? 0}%
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${status?.progress ?? 0}%` }}
                    />
                  </div>
                </div>

                {/* Cancel button */}
                <div className="mt-8 text-center">
                  <button
                    onClick={() => setShowCancelConfirm(true)}
                    className="
                      text-sm text-text-secondary hover:text-text-primary
                      transition-colors duration-150
                    "
                  >
                    取消处理
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cancel confirmation modal */}
      {showCancelConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setShowCancelConfirm(false)}
          />
          {/* Dialog */}
          <div className="relative bg-white rounded-lg shadow-lg max-w-sm w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-2">
              确认取消处理？
            </h3>
            <p className="text-sm text-text-secondary mb-6">
              取消后处理进度将丢失，您需要重新开始处理。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowCancelConfirm(false)}
                className="
                  px-4 py-2 rounded-md text-sm font-medium
                  border border-border text-gray-700
                  hover:bg-surface transition-colors duration-150
                "
              >
                继续处理
              </button>
              <button
                onClick={handleCancelConfirm}
                className="
                  px-4 py-2 rounded-md text-sm font-medium
                  bg-danger text-white hover:bg-red-700
                  transition-colors duration-150
                "
              >
                确认取消
              </button>
            </div>
          </div>
        </div>
      )}
    </AuthGuard>
  );
}

/**
 * Merge 4 backend stages into 3 display stages.
 * Combines "stutter" and "subtitle" into "检测口误&生成字幕".
 */
function _mergeStages(backendStages: StageInfo[] | null): StageInfo[] | null {
  if (!backendStages || backendStages.length === 0) return null;

  const merged: StageInfo[] = [];
  for (const stage of backendStages) {
    if (stage.key === "merge" || stage.key === "transcribe") {
      merged.push(stage);
    } else if (stage.key === "stutter") {
      // Find subtitle stage
      const subtitleStage = backendStages.find((s) => s.key === "subtitle");
      // Determine combined status: if both completed -> completed
      // If stutter is active or subtitle is active -> active
      // Otherwise pending
      let combinedStatus: "completed" | "active" | "pending" = "pending";
      if (
        stage.status === "completed" &&
        subtitleStage?.status === "completed"
      ) {
        combinedStatus = "completed";
      } else if (
        stage.status === "active" ||
        stage.status === "completed" ||
        subtitleStage?.status === "active"
      ) {
        combinedStatus =
          stage.status === "completed" && subtitleStage?.status !== "completed"
            ? "active"
            : stage.status === "active"
            ? "active"
            : "pending";
      }
      merged.push({
        key: "stutter_subtitle",
        name: "检测口误&生成字幕",
        status: combinedStatus,
      });
    }
    // Skip "subtitle" -- already merged above
  }

  return merged.length > 0 ? merged : null;
}

/**
 * Compute overall progress percentage across all stages.
 * Each stage has equal weight. Completed stages = 100%, active = current progress.
 */
function _computeOverallProgress(stages: StageInfo[], stageProgress: number): number {
  if (!stages || stages.length === 0) return 0;
  const totalStages = stages.length;
  const completedCount = stages.filter((s) => s.status === "completed").length;
  const activeStage = stages.find((s) => s.status === "active");

  let overall = (completedCount / totalStages) * 100;
  if (activeStage) {
    overall += (stageProgress / 100 / totalStages) * 100;
  }

  // If all completed
  if (completedCount === totalStages) return 100;

  return Math.min(Math.round(overall), 99); // Never show 100 until truly done
}
