"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { user, login } = useAuth();

  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [sendingCode, setSendingCode] = useState(false);
  const [loggingIn, setLoggingIn] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      router.replace("/upload");
    }
  }, [user, router]);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  const isValidPhone = phone.length === 11 && /^1\d{10}$/.test(phone);
  const isValidCode = code.length === 6 && /^\d{6}$/.test(code);

  const handleSendCode = useCallback(async () => {
    if (!isValidPhone || sendingCode || countdown > 0) return;
    setError("");
    setSendingCode(true);

    try {
      const res = await fetch("/api/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "发送失败，请稍后重试");
        return;
      }

      setCodeSent(true);
      setCountdown(60);
    } catch {
      setError("网络错误，请检查网络连接");
    } finally {
      setSendingCode(false);
    }
  }, [phone, isValidPhone, sendingCode, countdown]);

  const handleLogin = useCallback(async () => {
    if (!isValidPhone || !isValidCode || loggingIn) return;
    setError("");
    setLoggingIn(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, code }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "登录失败，请稍后重试");
        return;
      }

      login(data.token, data.user);
      router.replace("/upload");
    } catch {
      setError("网络错误，请检查网络连接");
    } finally {
      setLoggingIn(false);
    }
  }, [phone, code, isValidPhone, isValidCode, loggingIn, login, router]);

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-semibold text-text-primary md:text-3xl">
            登录 AutoCut
          </h1>
          <p className="mt-2 text-text-secondary text-sm">
            使用手机号验证码登录，新用户自动注册
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {/* Phone input */}
          <div className="mb-4">
            <label
              htmlFor="phone"
              className="block text-sm font-medium text-text-primary mb-1.5"
            >
              手机号
            </label>
            <input
              id="phone"
              type="tel"
              inputMode="numeric"
              autoComplete="tel"
              placeholder="请输入 11 位手机号"
              maxLength={11}
              value={phone}
              onChange={(e) => {
                const v = e.target.value.replace(/\D/g, "");
                setPhone(v);
                setError("");
              }}
              className={`w-full border rounded-lg px-4 py-3 text-base transition-colors focus:outline-none focus:ring-2 ${
                error && !codeSent
                  ? "border-red-500 focus:ring-red-500/20"
                  : "border-gray-300 focus:border-blue-500 focus:ring-blue-500/20"
              }`}
            />
          </div>

          {/* Code input + send button */}
          <div className="mb-4">
            <label
              htmlFor="code"
              className="block text-sm font-medium text-text-primary mb-1.5"
            >
              验证码
            </label>
            <div className="flex gap-3">
              <input
                id="code"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="6 位验证码"
                maxLength={6}
                value={code}
                onChange={(e) => {
                  const v = e.target.value.replace(/\D/g, "");
                  setCode(v);
                  setError("");
                }}
                className={`flex-1 border rounded-lg px-4 py-3 text-base transition-colors focus:outline-none focus:ring-2 ${
                  error && codeSent
                    ? "border-red-500 focus:ring-red-500/20"
                    : "border-gray-300 focus:border-blue-500 focus:ring-blue-500/20"
                }`}
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={!isValidPhone || sendingCode || countdown > 0}
                className={`whitespace-nowrap rounded-lg px-4 py-3 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                  !isValidPhone || sendingCode || countdown > 0
                    ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                    : "bg-primary text-white hover:bg-primary-hover"
                }`}
              >
                {sendingCode
                  ? "发送中..."
                  : countdown > 0
                  ? `已发送(${countdown}s)`
                  : "获取验证码"}
              </button>
            </div>
          </div>

          {/* Error message */}
          {error && (
            <p className="text-sm text-red-600 mb-4" role="alert">
              {error}
            </p>
          )}

          {/* Login button */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={!isValidPhone || !isValidCode || loggingIn}
            className={`w-full rounded-lg py-3 text-base font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
              !isValidPhone || !isValidCode || loggingIn
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : "bg-primary text-white hover:bg-primary-hover"
            }`}
          >
            {loggingIn ? "登录中..." : "登录"}
          </button>
        </div>

        {/* Footer hint */}
        <p className="text-center text-xs text-text-secondary mt-4">
          MVP 测试阶段，验证码固定为 123456
        </p>
      </div>
    </div>
  );
}
