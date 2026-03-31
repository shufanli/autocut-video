"use client";

import { useState } from "react";
import { CheckCircle, ChevronDown, ChevronUp } from "lucide-react";

export interface Preferences {
  mode: "auto" | "manual";
  subtitleStyle: "clean-white" | "black-bg-white" | "color-highlight";
  subtitlePosition: "bottom" | "center" | "top";
}

const SUBTITLE_STYLES: {
  key: Preferences["subtitleStyle"];
  label: string;
  preview: string;
}[] = [
  {
    key: "clean-white",
    label: "简洁白字",
    preview: "白色文字 + 细描边",
  },
  {
    key: "black-bg-white",
    label: "黑底白字",
    preview: "黑色半透明底 + 白字",
  },
  {
    key: "color-highlight",
    label: "彩色高亮",
    preview: "关键词高亮 + 动态效果",
  },
];

const SUBTITLE_POSITIONS: {
  key: Preferences["subtitlePosition"];
  label: string;
}[] = [
  { key: "bottom", label: "底部" },
  { key: "center", label: "居中" },
  { key: "top", label: "顶部" },
];

interface PreferencePanelProps {
  preferences: Preferences;
  onChange: (prefs: Preferences) => void;
}

export function PreferencePanel({
  preferences,
  onChange,
}: PreferencePanelProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white border border-[#E5E7EB] rounded-lg p-4 lg:p-6">
      <h3 className="text-lg font-semibold text-text-primary mb-4">
        偏好设置
      </h3>

      {/* Auto mode tag */}
      <div className="flex items-center gap-2 mb-4">
        <CheckCircle className="w-5 h-5 text-success" />
        <span className="text-sm font-medium text-text-primary">
          让 AI 自动决定
        </span>
      </div>
      <p className="text-xs text-text-secondary mb-4">
        AI 会根据视频内容自动选择最佳的字幕样式和位置
      </p>

      {/* Advanced settings toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-sm text-primary hover:text-primary-hover font-medium transition-colors"
      >
        高级设置
        {expanded ? (
          <ChevronUp className="w-4 h-4" />
        ) : (
          <ChevronDown className="w-4 h-4" />
        )}
      </button>

      {/* Expanded settings */}
      {expanded && (
        <div className="mt-4 space-y-5 pt-4 border-t border-[#E5E7EB]">
          {/* Subtitle style */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              字幕样式
            </label>
            <div className="space-y-2">
              {SUBTITLE_STYLES.map((style) => (
                <button
                  key={style.key}
                  onClick={() =>
                    onChange({
                      ...preferences,
                      mode: "manual",
                      subtitleStyle: style.key,
                    })
                  }
                  className={`
                    w-full text-left px-3 py-2.5 rounded-md border text-sm transition-colors
                    ${
                      preferences.subtitleStyle === style.key
                        ? "border-primary bg-[#EFF6FF] text-primary"
                        : "border-[#E5E7EB] text-text-primary hover:bg-gray-50"
                    }
                  `}
                >
                  <span className="font-medium">{style.label}</span>
                  <span className="text-xs text-text-secondary ml-2">
                    {style.preview}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Subtitle position */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              字幕位置
            </label>
            <div className="flex gap-2">
              {SUBTITLE_POSITIONS.map((pos) => (
                <button
                  key={pos.key}
                  onClick={() =>
                    onChange({
                      ...preferences,
                      mode: "manual",
                      subtitlePosition: pos.key,
                    })
                  }
                  className={`
                    flex-1 px-3 py-2 rounded-md border text-sm font-medium text-center transition-colors
                    ${
                      preferences.subtitlePosition === pos.key
                        ? "border-primary bg-[#EFF6FF] text-primary"
                        : "border-[#E5E7EB] text-text-primary hover:bg-gray-50"
                    }
                  `}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
