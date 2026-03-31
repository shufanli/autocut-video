"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { useState, useRef, useEffect } from "react";

/**
 * Generate a deterministic color from a string (phone suffix).
 * Returns a hex color suitable for an avatar background.
 */
function avatarColor(seed: string): string {
  const colors = [
    "#2563EB", // blue
    "#7C3AED", // violet
    "#DB2777", // pink
    "#DC2626", // red
    "#EA580C", // orange
    "#16A34A", // green
    "#0891B2", // cyan
    "#4F46E5", // indigo
  ];
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export function Navbar() {
  const { user, loading, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <nav className="h-16 bg-white border-b border-border flex items-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-content mx-auto w-full flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <svg
            className="w-8 h-8 text-primary"
            viewBox="0 0 32 32"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="32" height="32" rx="8" fill="currentColor" />
            <path d="M10 10L22 16L10 22V10Z" fill="white" />
          </svg>
          <span className="text-lg font-semibold text-text-primary">
            AutoCut
          </span>
        </Link>

        {/* Right side */}
        <div className="flex items-center">
          {loading ? (
            <div className="w-20 h-9 bg-gray-100 rounded-lg animate-pulse" />
          ) : user ? (
            /* Logged in: avatar with dropdown */
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-full"
                aria-label="用户菜单"
              >
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-medium"
                  style={{ backgroundColor: avatarColor(user.phone_suffix) }}
                >
                  {user.phone_suffix}
                </div>
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-2 z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm text-text-secondary">
                      {user.phone.replace(/(\d{3})\d{4}(\d{4})/, "$1****$2")}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      logout();
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-danger hover:bg-gray-50 transition-colors"
                  >
                    退出登录
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* Not logged in: login button */
            <Link
              href="/login"
              className="bg-primary text-white rounded-lg px-6 py-2 text-sm font-medium hover:bg-primary-hover transition-colors duration-150 focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              登录
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
