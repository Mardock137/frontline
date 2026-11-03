"use client";

import * as React from "react";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ToastVariant = "default" | "success" | "error" | "info";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface ToastContextValue {
  toasts: ToastMessage[];
  toast: (msg: Omit<ToastMessage, "id">) => void;
  dismiss: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastMessage[]>([]);
  const timeoutIds = React.useRef<ReturnType<typeof setTimeout>[]>([]);

  const toast = React.useCallback((msg: Omit<ToastMessage, "id">) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { ...msg, id }]);
    const timeoutId = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
      timeoutIds.current = timeoutIds.current.filter((tid) => tid !== timeoutId);
    }, 4000);
    timeoutIds.current.push(timeoutId);
  }, []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  React.useEffect(() => {
    return () => {
      timeoutIds.current.forEach(clearTimeout);
      timeoutIds.current = [];
    };
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastViewport />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

// ---------------------------------------------------------------------------
// Viewport
// ---------------------------------------------------------------------------

function ToastViewport() {
  const { toasts, dismiss } = React.useContext(ToastContext)!;

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Individual Toast
// ---------------------------------------------------------------------------

const variantStyles: Record<ToastVariant, string> = {
  default: "border-gray-200 bg-white text-gray-900",
  success: "border-green-200 bg-green-50 text-green-900",
  error: "border-red-200 bg-red-50 text-red-900",
  info: "border-blue-200 bg-blue-50 text-blue-900",
};

const variantIcons: Record<ToastVariant, React.ReactNode> = {
  default: <Info className="h-4 w-4 text-gray-500" />,
  success: <CheckCircle className="h-4 w-4 text-green-600" />,
  error: <AlertCircle className="h-4 w-4 text-red-600" />,
  info: <Info className="h-4 w-4 text-blue-600" />,
};

function Toast({
  toast,
  onDismiss,
}: {
  toast: ToastMessage;
  onDismiss: () => void;
}) {
  const variant = toast.variant ?? "default";
  return (
    <div
      className={cn(
        "flex w-80 items-start gap-3 rounded-lg border p-4 shadow-md",
        variantStyles[variant],
      )}
    >
      <span className="mt-0.5 shrink-0">{variantIcons[variant]}</span>
      <div className="flex-1">
        <p className="text-sm font-semibold">{toast.title}</p>
        {toast.description && (
          <p className="mt-0.5 text-xs opacity-80">{toast.description}</p>
        )}
      </div>
      <button
        onClick={onDismiss}
        className="shrink-0 rounded text-gray-400 hover:text-gray-700"
        aria-label="Chiudi"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
