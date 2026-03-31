"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  X,
  CreditCard,
  Loader2,
  CheckCircle,
  AlertCircle,
  Smartphone,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type PaymentChannel = "alipay" | "wechat";

type ModalStep = "select" | "paying" | "success" | "failed";

interface PaymentModalProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
  onPaymentSuccess: () => void;
}

// ---------------------------------------------------------------------------
// PaymentModal
// ---------------------------------------------------------------------------

export function PaymentModal({
  taskId,
  isOpen,
  onClose,
  onPaymentSuccess,
}: PaymentModalProps) {
  const { token } = useAuth();

  const [step, setStep] = useState<ModalStep>("select");
  const [channel, setChannel] = useState<PaymentChannel>("alipay");
  const [paymentId, setPaymentId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [failMessage, setFailMessage] = useState("");

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setStep("select");
      setChannel("alipay");
      setPaymentId(null);
      setIsCreating(false);
      setFailMessage("");
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [isOpen]);

  // ---------------------------------------------------------------------------
  // Create payment and start polling
  // ---------------------------------------------------------------------------
  const handlePay = useCallback(async () => {
    if (!token || isCreating) return;
    setIsCreating(true);

    try {
      // Create payment order
      const res = await fetch("/api/payments/create", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task_id: taskId,
          payment_channel: channel,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "创建订单失败");
      }

      const data = await res.json();
      setPaymentId(data.payment_id);
      setStep("paying");

      // MVP: auto-trigger mock payment after a short delay to simulate QR scan
      // In production, user would scan a real QR code
      setTimeout(async () => {
        try {
          await fetch(`/api/payments/${data.payment_id}/mock-pay`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          });
        } catch {
          // Will be caught by polling
        }
      }, 2000);

      // Start polling for payment status
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await fetch(
            `/api/payments/${data.payment_id}/status`,
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          if (statusRes.ok) {
            const statusData = await statusRes.json();
            if (statusData.payment_status === "success") {
              if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
              }
              setStep("success");
              // Brief delay to show success state before closing
              setTimeout(() => {
                onPaymentSuccess();
              }, 1200);
            } else if (statusData.payment_status === "failed") {
              if (pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
              }
              setStep("failed");
              setFailMessage("支付未完成，可稍后重新下载");
            }
          }
        } catch {
          // Polling error -- keep trying
        }
      }, 1500);
    } catch (err) {
      const message = err instanceof Error ? err.message : "创建订单失败";
      setFailMessage(message);
      setStep("failed");
    } finally {
      setIsCreating(false);
    }
  }, [token, taskId, channel, isCreating, onPaymentSuccess]);

  // ---------------------------------------------------------------------------
  // Handle close
  // ---------------------------------------------------------------------------
  const handleClose = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    // Cancel pending payment if exists
    if (paymentId && step === "paying" && token) {
      fetch(`/api/payments/${paymentId}/cancel`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      }).catch(() => {});
    }
    onClose();
  }, [paymentId, step, token, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && step !== "paying") {
          handleClose();
        }
      }}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Modal */}
      <div
        className="
          relative w-full max-w-[420px]
          bg-white rounded-lg shadow-lg
          p-6 sm:p-8
          animate-modal-in
        "
      >
        {/* Close button */}
        {step !== "paying" && (
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-text-secondary hover:text-text-primary transition-colors"
            aria-label="关闭"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        {/* Step: select payment channel */}
        {step === "select" && (
          <div>
            <div className="text-center mb-6">
              <CreditCard className="w-10 h-10 text-primary mx-auto mb-3" />
              <h2 className="text-xl font-semibold text-text-primary">
                付费下载
              </h2>
              <p className="text-sm text-text-secondary mt-1">
                免费额度已用完，需要付费下载此视频
              </p>
            </div>

            {/* Price display */}
            <div className="bg-surface rounded-lg p-4 mb-6 text-center">
              <p className="text-sm text-text-secondary">单条视频价格</p>
              <p className="text-3xl font-bold text-text-primary mt-1">
                <span className="text-lg font-normal">&#165;</span>9.9
              </p>
            </div>

            {/* Payment channel selection */}
            <div className="space-y-3 mb-6">
              <p className="text-sm font-medium text-text-primary">
                选择支付方式
              </p>

              {/* Alipay */}
              <button
                onClick={() => setChannel("alipay")}
                className={`
                  w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-200
                  ${
                    channel === "alipay"
                      ? "border-primary bg-blue-50"
                      : "border-border hover:border-gray-300"
                  }
                `}
              >
                <div
                  className={`
                  w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold
                  ${channel === "alipay" ? "bg-[#1677FF] text-white" : "bg-gray-100 text-gray-500"}
                `}
                >
                  <Smartphone className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-text-primary">
                    支付宝
                  </p>
                  <p className="text-xs text-text-secondary">
                    推荐 | 扫码支付
                  </p>
                </div>
                <div
                  className={`
                  ml-auto w-5 h-5 rounded-full border-2 flex items-center justify-center
                  ${
                    channel === "alipay"
                      ? "border-primary"
                      : "border-gray-300"
                  }
                `}
                >
                  {channel === "alipay" && (
                    <div className="w-2.5 h-2.5 rounded-full bg-primary" />
                  )}
                </div>
              </button>

              {/* WeChat Pay */}
              <button
                onClick={() => setChannel("wechat")}
                className={`
                  w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-200
                  ${
                    channel === "wechat"
                      ? "border-primary bg-blue-50"
                      : "border-border hover:border-gray-300"
                  }
                `}
              >
                <div
                  className={`
                  w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold
                  ${channel === "wechat" ? "bg-[#07C160] text-white" : "bg-gray-100 text-gray-500"}
                `}
                >
                  <Smartphone className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-text-primary">
                    微信支付
                  </p>
                  <p className="text-xs text-text-secondary">扫码支付</p>
                </div>
                <div
                  className={`
                  ml-auto w-5 h-5 rounded-full border-2 flex items-center justify-center
                  ${
                    channel === "wechat"
                      ? "border-primary"
                      : "border-gray-300"
                  }
                `}
                >
                  {channel === "wechat" && (
                    <div className="w-2.5 h-2.5 rounded-full bg-primary" />
                  )}
                </div>
              </button>
            </div>

            {/* Pay button */}
            <button
              onClick={handlePay}
              disabled={isCreating}
              className="
                w-full py-3 rounded-md text-base font-medium
                bg-primary text-white hover:bg-primary-hover
                transition-colors duration-150
                disabled:opacity-50 disabled:cursor-not-allowed
                flex items-center justify-center gap-2
              "
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  创建订单中...
                </>
              ) : (
                <>确认支付 &#165;9.9</>
              )}
            </button>
          </div>
        )}

        {/* Step: paying (waiting for payment) */}
        {step === "paying" && (
          <div className="text-center py-4">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-text-primary mb-2">
                等待支付
              </h2>
              <p className="text-sm text-text-secondary">
                请在{channel === "alipay" ? "支付宝" : "微信"}中完成支付
              </p>
            </div>

            {/* Mock QR Code area */}
            <div className="bg-surface border border-border rounded-lg p-8 mb-6 mx-auto max-w-[240px]">
              <div className="w-40 h-40 mx-auto bg-white border border-gray-200 rounded-lg flex items-center justify-center mb-3">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-2" />
                  <p className="text-xs text-text-secondary">
                    模拟支付中...
                  </p>
                </div>
              </div>
              <p className="text-xs text-text-secondary">
                {channel === "alipay" ? "支付宝" : "微信"}扫码支付
              </p>
            </div>

            <p className="text-2xl font-bold text-text-primary mb-4">
              &#165;9.9
            </p>

            <button
              onClick={handleClose}
              className="
                text-sm text-text-secondary hover:text-text-primary
                transition-colors duration-150
              "
            >
              取消支付
            </button>
          </div>
        )}

        {/* Step: success */}
        {step === "success" && (
          <div className="text-center py-6">
            <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-text-primary mb-2">
              支付成功
            </h2>
            <p className="text-sm text-text-secondary">
              即将开始下载视频...
            </p>
          </div>
        )}

        {/* Step: failed */}
        {step === "failed" && (
          <div className="text-center py-6">
            <AlertCircle className="w-12 h-12 text-danger mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-text-primary mb-2">
              支付未完成
            </h2>
            <p className="text-sm text-text-secondary mb-6">{failMessage}</p>
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={handleClose}
                className="
                  px-6 py-2.5 rounded-md text-sm font-medium
                  border border-border text-gray-700
                  hover:bg-surface transition-colors duration-150
                "
              >
                关闭
              </button>
              <button
                onClick={() => {
                  setStep("select");
                  setPaymentId(null);
                  setFailMessage("");
                }}
                className="
                  px-6 py-2.5 rounded-md text-sm font-medium
                  bg-primary text-white hover:bg-primary-hover
                  transition-colors duration-150
                "
              >
                重新支付
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
