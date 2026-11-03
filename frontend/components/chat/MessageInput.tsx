"use client";

import { useState, type KeyboardEvent, type CSSProperties } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  primaryColor: string;
}

export function MessageInput({ onSend, disabled = false, primaryColor }: MessageInputProps) {
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const textareaStyle: CSSProperties = {
    scrollbarWidth: "thin",
    outline: "none",
    boxShadow: focused ? `0 0 0 2px ${primaryColor}40, 0 0 0 1px ${primaryColor}` : undefined,
  };

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3">
      <div className="mx-auto flex max-w-2xl items-end gap-2">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={disabled}
          rows={1}
          placeholder="Type a message…"
          aria-label="Type a message"
          className={cn(
            "flex-1 resize-none rounded-xl border border-gray-300 bg-gray-50 px-4 py-2.5 text-sm",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "max-h-32 overflow-y-auto",
          )}
          style={textareaStyle}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          aria-label="Send message"
          className={cn(
            "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-white",
            "transition-opacity disabled:cursor-not-allowed disabled:opacity-40",
          )}
          style={{ backgroundColor: primaryColor }}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
