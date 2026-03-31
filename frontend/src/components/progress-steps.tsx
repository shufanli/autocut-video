"use client";

import { CheckCircle, Loader2, Circle } from "lucide-react";

export interface StageInfo {
  key: string;
  name: string;
  status: "completed" | "active" | "pending";
}

interface ProgressStepsProps {
  stages: StageInfo[];
  currentStageName: string;
  estimatedSeconds: number;
}

export function ProgressSteps({
  stages,
  currentStageName,
  estimatedSeconds,
}: ProgressStepsProps) {
  return (
    <div className="w-full">
      {/* Step indicators */}
      <div className="flex items-center justify-between mb-8">
        {stages.map((stage, index) => (
          <div key={stage.key} className="flex items-center flex-1 last:flex-none">
            {/* Step circle */}
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center
                  transition-all duration-300
                  ${
                    stage.status === "completed"
                      ? "bg-success text-white"
                      : stage.status === "active"
                      ? "bg-primary text-white"
                      : "bg-gray-100 text-text-disabled border border-border"
                  }
                `}
              >
                {stage.status === "completed" ? (
                  <CheckCircle className="w-5 h-5" />
                ) : stage.status === "active" ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Circle className="w-5 h-5" />
                )}
              </div>
              {/* Stage name below circle */}
              <span
                className={`
                  mt-2 text-xs font-medium text-center whitespace-nowrap
                  ${
                    stage.status === "completed"
                      ? "text-success"
                      : stage.status === "active"
                      ? "text-primary"
                      : "text-text-disabled"
                  }
                `}
              >
                {stage.name}
              </span>
            </div>

            {/* Connector line between steps */}
            {index < stages.length - 1 && (
              <div
                className={`
                  flex-1 h-0.5 mx-2 mt-[-20px]
                  transition-colors duration-300
                  ${
                    stage.status === "completed"
                      ? "bg-success"
                      : "bg-border"
                  }
                `}
              />
            )}
          </div>
        ))}
      </div>

      {/* Current stage description */}
      <div className="text-center">
        <p className="text-lg font-semibold text-text-primary">
          {stages.every((s) => s.status === "completed")
            ? "处理完成!"
            : `正在${currentStageName}...`}
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
    </div>
  );
}
