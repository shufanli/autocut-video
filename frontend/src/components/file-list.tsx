"use client";

import { useMemo } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Trash2, CheckCircle, Loader2 } from "lucide-react";

export interface UploadedFile {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  sort_order: number;
  /** Upload progress 0-100, or -1 for complete */
  progress: number;
  /** Whether upload encountered an error */
  error?: string;
}

interface FileListProps {
  files: UploadedFile[];
  onReorder: (files: UploadedFile[]) => void;
  onDelete: (fileId: string) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

// ---------------------------------------------------------------------------
// Sortable File Item
// ---------------------------------------------------------------------------

function SortableFileItem({
  file,
  onDelete,
}: {
  file: UploadedFile;
  onDelete: (id: string) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: file.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
    opacity: isDragging ? 0.85 : 1,
  };

  const isComplete = file.progress === -1;
  const isUploading = file.progress >= 0 && file.progress < 100;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        flex items-center gap-3 px-4 py-3 bg-white border rounded-lg
        transition-shadow duration-200
        ${isDragging ? "shadow-md border-primary/30" : "border-[#E5E7EB]"}
        ${file.error ? "border-red-300 bg-red-50/30" : ""}
      `}
    >
      {/* Drag handle */}
      <button
        className="flex-shrink-0 cursor-grab active:cursor-grabbing touch-none text-gray-400 hover:text-gray-600 p-1 -ml-1"
        {...attributes}
        {...listeners}
        aria-label="拖拽排序"
      >
        <GripVertical className="w-5 h-5" />
      </button>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-text-primary truncate">
            {file.original_filename}
          </p>
          {isComplete && (
            <CheckCircle className="w-4 h-4 text-success flex-shrink-0" />
          )}
          {isUploading && (
            <Loader2 className="w-4 h-4 text-primary animate-spin flex-shrink-0" />
          )}
        </div>
        <p className="text-xs text-text-secondary mt-0.5">
          {formatFileSize(file.file_size_bytes)}
          {file.error && (
            <span className="text-red-500 ml-2">{file.error}</span>
          )}
        </p>

        {/* Progress bar */}
        {isUploading && (
          <div className="mt-2 w-full h-1.5 bg-[#E5E7EB] rounded-sm overflow-hidden">
            <div
              className="h-full bg-primary rounded-sm transition-[width] duration-300 ease"
              style={{ width: `${file.progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Delete button */}
      <button
        onClick={() => onDelete(file.id)}
        className="flex-shrink-0 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-colors"
        aria-label={`删除 ${file.original_filename}`}
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// FileList
// ---------------------------------------------------------------------------

export function FileList({ files, onReorder, onDelete }: FileListProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const fileIds = useMemo(() => files.map((f) => f.id), [files]);

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = files.findIndex((f) => f.id === active.id);
    const newIndex = files.findIndex((f) => f.id === over.id);

    if (oldIndex !== -1 && newIndex !== -1) {
      const newFiles = arrayMove(files, oldIndex, newIndex);
      onReorder(newFiles);
    }
  }

  if (files.length === 0) return null;

  return (
    <div className="space-y-2 mt-4">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={fileIds} strategy={verticalListSortingStrategy}>
          {files.map((file) => (
            <SortableFileItem
              key={file.id}
              file={file}
              onDelete={onDelete}
            />
          ))}
        </SortableContext>
      </DndContext>
    </div>
  );
}
