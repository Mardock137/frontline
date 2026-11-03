import { cn } from "@/lib/utils";

export type MessageRole = "agent" | "customer";

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
}

interface MessageBubbleProps {
  message: Message;
  primaryColor: string;
}

export function MessageBubble({ message, primaryColor }: MessageBubbleProps) {
  const isAgent = message.role === "agent";

  return (
    <div
      className={cn(
        "flex w-full",
        isAgent ? "justify-start" : "justify-end",
      )}
    >
      <div
        className={cn(
          "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm",
          isAgent
            ? "rounded-tl-sm bg-white text-gray-800 ring-1 ring-gray-200"
            : "rounded-tr-sm text-white",
        )}
        style={!isAgent ? { backgroundColor: primaryColor } : undefined}
      >
        <span className="sr-only">{isAgent ? "Assistant:" : "You:"}</span>
        {message.content}
      </div>
    </div>
  );
}
