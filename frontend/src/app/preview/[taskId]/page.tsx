"use client";

import { useParams } from "next/navigation";
import { CheckCircle } from "lucide-react";
import { AuthGuard } from "@/components/auth-guard";

/**
 * Preview page placeholder -- full implementation in Sprint 5.
 * This page exists so that the auto-redirect from processing works.
 */
export default function PreviewPage() {
  const params = useParams();
  const taskId = params.taskId as string;

  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8 py-6 lg:py-10">
        <div className="max-w-3xl mx-auto text-center">
          <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-text-primary mb-2">
            处理完成
          </h1>
          <p className="text-sm text-text-secondary mb-6">
            视频处理已完成，预览功能将在后续版本中提供。
          </p>
          <p className="text-xs text-text-secondary font-mono">
            任务 ID: {taskId}
          </p>
        </div>
      </div>
    </AuthGuard>
  );
}
