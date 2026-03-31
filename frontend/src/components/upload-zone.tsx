"use client";

import { useRef, useState, useCallback } from "react";
import { Upload } from "lucide-react";

const ALLOWED_TYPES = [
  "video/mp4",
  "video/quicktime", // .mov
  "video/webm",
];

const ALLOWED_EXTENSIONS = ["mp4", "mov", "webm"];

interface UploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

function getExtension(filename: string): string {
  const parts = filename.split(".");
  return parts.length > 1 ? parts.pop()!.toLowerCase() : "";
}

function isValidVideoFile(file: File): boolean {
  // Check by MIME type first
  if (ALLOWED_TYPES.includes(file.type)) return true;
  // Fallback: check by extension
  const ext = getExtension(file.name);
  return ALLOWED_EXTENSIONS.includes(ext);
}

export function UploadZone({ onFilesSelected, disabled }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      const files = Array.from(fileList);
      onFilesSelected(files);
    },
    [onFilesSelected]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled) setIsDragOver(true);
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      if (disabled) return;
      handleFiles(e.dataTransfer.files);
    },
    [disabled, handleFiles]
  );

  const handleClick = useCallback(() => {
    if (disabled) return;
    inputRef.current?.click();
  }, [disabled]);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files);
      // Reset input so re-selecting the same file works
      if (inputRef.current) inputRef.current.value = "";
    },
    [handleFiles]
  );

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") handleClick();
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        relative rounded-xl border-2 border-dashed p-12
        flex flex-col items-center justify-center gap-4
        cursor-pointer transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
        ${
          disabled
            ? "border-gray-200 bg-gray-50 cursor-not-allowed opacity-60"
            : isDragOver
            ? "border-primary bg-[#EFF6FF]"
            : "border-[#E5E7EB] bg-white hover:border-gray-300 hover:bg-gray-50/50"
        }
      `}
    >
      <div
        className={`w-12 h-12 rounded-xl flex items-center justify-center ${
          isDragOver ? "bg-blue-100" : "bg-blue-50"
        }`}
      >
        <Upload
          className={`w-6 h-6 ${
            isDragOver ? "text-primary" : "text-primary/70"
          }`}
        />
      </div>

      <div className="text-center">
        <p className="text-base font-medium text-text-primary">
          {isDragOver ? "松开鼠标上传文件" : "拖拽视频文件到此处，或点击上传"}
        </p>
        <p className="text-sm text-text-secondary mt-1">
          支持 MP4、MOV、WebM 格式
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
        className="hidden"
        onChange={handleInputChange}
      />
    </div>
  );
}

// Export the validation helper for use in the upload page
export { isValidVideoFile, ALLOWED_EXTENSIONS };
