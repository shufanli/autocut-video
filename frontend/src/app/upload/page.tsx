"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";
import { UploadZone, isValidVideoFile } from "@/components/upload-zone";
import { FileList, UploadedFile } from "@/components/file-list";
import { PreferencePanel, Preferences } from "@/components/preference-panel";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/toast";

interface UploadedFileResponse {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  sort_order: number;
  uploaded_at: string;
  size_warning: boolean;
}

interface UploadError {
  filename: string;
  error: string;
}

export default function UploadPage() {
  const router = useRouter();
  const { token, user } = useAuth();
  const { showToast } = useToast();

  const [taskId, setTaskId] = useState<string | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [preferences, setPreferences] = useState<Preferences>({
    mode: "auto",
    subtitleStyle: "clean-white",
    subtitlePosition: "bottom",
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [quota, setQuota] = useState<number | null>(null);

  // Track if a task creation is in progress to avoid duplicates
  const creatingTask = useRef(false);

  // Fetch quota on mount
  useEffect(() => {
    if (!token) return;
    fetch("/api/quota", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setQuota(data.free_quota_remaining);
      })
      .catch(() => {});
  }, [token]);

  // Use the user's quota from auth context as fallback
  useEffect(() => {
    if (quota === null && user) {
      setQuota(user.free_quota_remaining);
    }
  }, [user, quota]);

  // ---------------------------------------------------------------------------
  // Create task (lazy — only when first file is added)
  // ---------------------------------------------------------------------------
  const ensureTask = useCallback(async (): Promise<string | null> => {
    if (taskId) return taskId;
    if (creatingTask.current) return null;
    creatingTask.current = true;

    try {
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
      if (!res.ok) {
        showToast("创建任务失败，请稍后重试", "error");
        return null;
      }
      const data = await res.json();
      setTaskId(data.id);
      return data.id;
    } catch {
      showToast("网络错误，请检查网络连接", "error");
      return null;
    } finally {
      creatingTask.current = false;
    }
  }, [taskId, token, showToast]);

  // ---------------------------------------------------------------------------
  // Upload files
  // ---------------------------------------------------------------------------
  const handleFilesSelected = useCallback(
    async (selectedFiles: File[]) => {
      // Validate files
      const valid: File[] = [];
      for (const file of selectedFiles) {
        if (!isValidVideoFile(file)) {
          showToast(
            `不支持的文件格式，请上传 MP4/MOV/WebM`,
            "error"
          );
          continue;
        }
        valid.push(file);
      }

      if (valid.length === 0) return;

      // Ensure we have a task
      const currentTaskId = await ensureTask();
      if (!currentTaskId) return;

      // Add placeholder files to the list with progress 0
      const placeholders: UploadedFile[] = valid.map((file, i) => ({
        id: `temp-${Date.now()}-${i}`,
        original_filename: file.name,
        file_size_bytes: file.size,
        sort_order: files.length + i,
        progress: 0,
      }));

      setFiles((prev) => [...prev, ...placeholders]);

      // Upload each file individually for progress tracking
      for (let i = 0; i < valid.length; i++) {
        const file = valid[i];
        const placeholderId = placeholders[i].id;

        try {
          // Use XMLHttpRequest for progress tracking
          const result = await uploadFileWithProgress(
            currentTaskId,
            file,
            token!,
            (progress) => {
              setFiles((prev) =>
                prev.map((f) =>
                  f.id === placeholderId ? { ...f, progress } : f
                )
              );
            }
          );

          if (result.uploaded && result.uploaded.length > 0) {
            const uploaded = result.uploaded[0];
            // Replace placeholder with real file data
            setFiles((prev) =>
              prev.map((f) =>
                f.id === placeholderId
                  ? {
                      ...f,
                      id: uploaded.id,
                      original_filename: uploaded.original_filename,
                      file_size_bytes: uploaded.file_size_bytes,
                      sort_order: uploaded.sort_order,
                      progress: -1, // -1 = complete
                    }
                  : f
              )
            );

            if (uploaded.size_warning) {
              showToast(
                `${file.name} 文件较大(>${500}MB)，上传可能较慢`,
                "info"
              );
            }
          }

          if (result.errors && result.errors.length > 0) {
            for (const err of result.errors) {
              showToast(err.error, "error");
            }
            // Remove failed placeholder
            setFiles((prev) => prev.filter((f) => f.id !== placeholderId));
          }
        } catch {
          showToast(`上传 ${file.name} 失败，请重试`, "error");
          // Mark error on the file
          setFiles((prev) =>
            prev.map((f) =>
              f.id === placeholderId
                ? { ...f, progress: -1, error: "上传失败" }
                : f
            )
          );
        }
      }
    },
    [ensureTask, files.length, token, showToast]
  );

  // ---------------------------------------------------------------------------
  // Reorder files
  // ---------------------------------------------------------------------------
  const handleReorder = useCallback(
    async (newFiles: UploadedFile[]) => {
      setFiles(newFiles);

      if (!taskId || !token) return;

      // Only reorder server-confirmed files (non-temp IDs)
      const realFileIds = newFiles
        .filter((f) => !f.id.startsWith("temp-"))
        .map((f) => f.id);

      try {
        await fetch(`/api/tasks/${taskId}/files/reorder`, {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ file_ids: realFileIds }),
        });
      } catch {
        // Reorder failed silently — local order is still updated
      }
    },
    [taskId, token]
  );

  // ---------------------------------------------------------------------------
  // Delete file
  // ---------------------------------------------------------------------------
  const handleDelete = useCallback(
    async (fileId: string) => {
      setFiles((prev) => prev.filter((f) => f.id !== fileId));

      if (!taskId || !token || fileId.startsWith("temp-")) return;

      try {
        await fetch(`/api/tasks/${taskId}/files/${fileId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch {
        showToast("删除文件失败", "error");
      }
    },
    [taskId, token, showToast]
  );

  // ---------------------------------------------------------------------------
  // Start processing
  // ---------------------------------------------------------------------------
  const handleStartProcessing = useCallback(async () => {
    if (!taskId || !token || files.length === 0) return;
    setIsProcessing(true);

    try {
      // Save preferences first
      await fetch(`/api/tasks/${taskId}/preferences`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ preferences }),
      });

      // Trigger backend processing pipeline
      const processRes = await fetch(`/api/tasks/${taskId}/process`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!processRes.ok) {
        const errData = await processRes.json().catch(() => ({}));
        throw new Error(errData.detail || "启动处理失败");
      }

      // Navigate to processing page
      router.push(`/processing/${taskId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "启动处理失败，请重试";
      showToast(message, "error");
      setIsProcessing(false);
    }
  }, [taskId, token, files.length, preferences, router, showToast]);

  // ---------------------------------------------------------------------------
  // Check if all files are done uploading
  // ---------------------------------------------------------------------------
  const completedFiles = files.filter(
    (f) => f.progress === -1 && !f.error
  );
  const hasFiles = completedFiles.length > 0;
  const isUploading = files.some((f) => f.progress >= 0 && f.progress < 100);
  const canProcess = hasFiles && !isUploading && !isProcessing;

  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="max-w-5xl mx-auto">
          {/* Page header */}
          <div className="mb-6 lg:mb-8">
            <h1 className="text-2xl font-bold text-text-primary">上传素材</h1>
            <p className="text-sm text-text-secondary mt-1">
              上传口播视频素材，AI 会自动去口误、加字幕
            </p>
          </div>

          {/* Main content: two-column on desktop */}
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Left column: upload zone + file list */}
            <div className="flex-1 lg:w-[60%]">
              <UploadZone
                onFilesSelected={handleFilesSelected}
                disabled={isProcessing}
              />

              <FileList
                files={files}
                onReorder={handleReorder}
                onDelete={handleDelete}
              />
            </div>

            {/* Right column: preferences */}
            <div className="lg:w-[40%]">
              <PreferencePanel
                preferences={preferences}
                onChange={setPreferences}
              />
            </div>
          </div>

          {/* Bottom: process button + quota */}
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <button
              onClick={handleStartProcessing}
              disabled={!canProcess}
              className={`
                w-full sm:w-auto px-8 py-3 rounded-md text-base font-medium
                transition-colors duration-150
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${
                  canProcess
                    ? "bg-primary text-white hover:bg-primary-hover"
                    : "bg-gray-200 text-gray-400 cursor-not-allowed"
                }
              `}
            >
              {isProcessing ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  处理中...
                </span>
              ) : (
                "开始处理"
              )}
            </button>

            {quota !== null && (
              <p className="text-sm text-text-secondary">
                您还有{" "}
                <span className="font-semibold text-primary">{quota}</span>{" "}
                条免费额度
              </p>
            )}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}

// ---------------------------------------------------------------------------
// Helper: upload file with XHR for progress tracking
// ---------------------------------------------------------------------------

function uploadFileWithProgress(
  taskId: string,
  file: File,
  token: string,
  onProgress: (percent: number) => void
): Promise<{ uploaded: UploadedFileResponse[]; errors: UploadError[] }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("files", file);

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Invalid response"));
        }
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () => reject(new Error("Network error")));
    xhr.addEventListener("abort", () => reject(new Error("Upload aborted")));

    xhr.open("POST", `/api/tasks/${taskId}/files`);
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.send(formData);
  });
}
