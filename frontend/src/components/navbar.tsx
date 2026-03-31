"use client";

export function Navbar() {
  return (
    <nav className="h-16 bg-white border-b border-border flex items-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-content mx-auto w-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <svg
            className="w-8 h-8 text-primary"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="32" height="32" rx="8" fill="currentColor" />
            <path
              d="M10 10L22 16L10 22V10Z"
              fill="white"
            />
          </svg>
          <span className="text-lg font-semibold text-text-primary">
            AutoCut
          </span>
        </div>

        {/* Login button placeholder */}
        <button className="bg-primary text-white rounded-lg px-6 py-2 text-sm font-medium hover:bg-primary-hover transition-colors duration-150 focus:ring-2 focus:ring-primary focus:ring-offset-2">
          登录
        </button>
      </div>
    </nav>
  );
}
