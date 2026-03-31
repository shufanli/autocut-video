"use client";

import { AuthGuard } from "@/components/auth-guard";
import { Upload } from "lucide-react";

export default function UploadPage() {
  return (
    <AuthGuard>
      <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-4">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 flex items-center justify-center mb-6">
          <Upload className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-2xl font-semibold text-text-primary mb-2">
          上传素材
        </h1>
        <p className="text-text-secondary text-sm text-center max-w-md">
          拖拽视频文件到此处，或点击上传。支持 MP4、MOV、WebM 格式。
        </p>
        <p className="text-xs text-text-secondary mt-6">
          完整上传功能将在下一版本上线
        </p>
      </div>
    </AuthGuard>
  );
}
