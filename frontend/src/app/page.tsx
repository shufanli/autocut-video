"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Scissors, Captions, CheckCircle, Download } from "lucide-react";

const features = [
  {
    icon: <Scissors className="w-6 h-6 text-primary" />,
    bgColor: "bg-blue-50",
    title: "智能去口误",
    desc: "AI 自动识别重复词、填充词（嗯、啊、那个）和长停顿，一键清理",
  },
  {
    icon: <Captions className="w-6 h-6 text-success" />,
    bgColor: "bg-green-50",
    title: "自动加字幕",
    desc: "语音识别生成精准字幕，多种样式一键切换，无需手动对时间轴",
  },
  {
    icon: <CheckCircle className="w-6 h-6 text-[#F59E0B]" />,
    bgColor: "bg-amber-50",
    title: "逐条可审核",
    desc: "AI 的每一处修改都清晰标注，你可以逐条确认或恢复，100% 掌控成品",
  },
  {
    icon: <Download className="w-6 h-6 text-[#DC2626]" />,
    bgColor: "bg-red-50",
    title: "一键出片",
    desc: "去口误、加字幕、合并素材一步到位，几分钟输出可直接发布的成品",
  },
];

export default function Home() {
  const { user, loading } = useAuth();

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col">
      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 py-12 sm:py-16 lg:py-20">
        <h1 className="text-[28px] sm:text-[36px] font-semibold leading-[1.2] text-text-primary max-w-2xl">
          口播视频，AI 一键出片
        </h1>
        <p className="mt-4 text-[15px] sm:text-base leading-relaxed text-text-secondary max-w-lg">
          上传素材 → AI 去口误、加字幕 → 几分钟出成品，每处修改可逐条审核
        </p>
        <div className="mt-8">
          {loading ? (
            <div className="w-36 h-12 bg-gray-100 rounded-lg animate-pulse" />
          ) : user ? (
            <Link
              href="/upload"
              className="inline-flex items-center justify-center bg-primary text-white rounded-lg px-8 py-3 text-base font-medium hover:bg-primary-hover transition-colors duration-150 focus:ring-2 focus:ring-primary focus:ring-offset-2 min-w-[160px]"
            >
              上传素材
            </Link>
          ) : (
            <Link
              href="/login"
              className="inline-flex items-center justify-center bg-primary text-white rounded-lg px-8 py-3 text-base font-medium hover:bg-primary-hover transition-colors duration-150 focus:ring-2 focus:ring-primary focus:ring-offset-2 min-w-[160px]"
            >
              免费试用
            </Link>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="pb-16 sm:pb-20 px-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 max-w-content mx-auto">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-white rounded-lg border border-border p-4 sm:p-6 hover:shadow-md transition-shadow duration-200"
            >
              <div className={`w-12 h-12 rounded-lg ${f.bgColor} flex items-center justify-center mb-3 sm:mb-4`}>
                {f.icon}
              </div>
              <h3 className="text-sm sm:text-lg font-semibold text-text-primary mb-1 sm:mb-2">
                {f.title}
              </h3>
              <p className="text-xs sm:text-sm leading-relaxed text-text-secondary">
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center">
        <p className="text-xs text-text-secondary">
          &copy; {new Date().getFullYear()} AutoCut. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
