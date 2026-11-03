"use client";

import { useEffect, useRef } from "react";
import { MessageBubble, type Message } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

interface ChatWindowProps {
  messages: Message[];
  isTyping: boolean;
  primaryColor: string;
}

export function ChatWindow({ messages, isTyping, primaryColor }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 px-4 py-6">
      <div
        className="mx-auto flex max-w-2xl flex-col gap-3"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label="Conversation"
      >
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} primaryColor={primaryColor} />
        ))}
        {isTyping && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
