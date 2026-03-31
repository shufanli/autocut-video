"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

const features = [
  {
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" className="fill-blue-100" />
        <path d="M10 11h12M10 16h8M10 21h10" stroke="#2563EB" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "智能去口误",
    desc: "AI 自动识别重复词、填充词（嗯、啊、那个）和长停顿，一键清理",
  },
  {
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" className="fill-green-100" />
        <rect x="6" y="18" width="20" height="6" rx="2" stroke="#16A34A" strokeWidth="2" />
        <path d="M10 22h12" stroke="#16A34A" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "自动字幕",
    desc: "语音识别生成精准字幕，多种样式一键切换，无需手动对时间轴",
  },
  {
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" className="fill-amber-100" />
        <path d="M8 12h6v8H8zM18 12h6v8h-6z" stroke="#F59E0B" strokeWidth="2" strokeLinejoin="round" />
        <path d="M14 16h4" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "多段合并",
    desc: "多条素材按顺序合并，拖拽排序，告别繁琐的时间线操作",
  },
  {
    icon: (
      <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="32" height="32" rx="8" className="fill-red-100" />
        <path d="M16 8v6M11 11l3.5 3.5M21 11l-3.5 3.5" stroke="#DC2626" strokeWidth="2" strokeLinecap="round" />
        <path d="M9 18h14" stroke="#DC2626" strokeWidth="2" strokeLinecap="round" />
        <path d="M10 21h2M14 21h4M20 21h2" stroke="#DC2626" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    title: "逐条可审核",
    desc: "AI 的每一处修改都清晰标注，你可以逐条确认或恢复，100% 掌控成品",
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 max-w-content mx-auto">
          {features.map((f) => (
            <div
              key={f.title}
              className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow"
            >
              <div className="mb-4">{f.icon}</div>
              <h3 className="text-base sm:text-lg font-semibold text-text-primary mb-2">
                {f.title}
              </h3>
              <p className="text-sm sm:text-[15px] leading-relaxed text-text-secondary">
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
