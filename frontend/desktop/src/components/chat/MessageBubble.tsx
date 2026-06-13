import { clsx } from "clsx";
import type { ChatMessage } from "../../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <article className={clsx("chat-message", isUser ? "user" : "assistant")}>
      <div
        className={clsx(
          "chat-bubble",
          isUser ? "chat-bubble-user" : "chat-bubble-assistant",
        )}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.emotion ? <span className="mt-2 block text-xs font-black text-[var(--gold)]">{message.emotion}</span> : null}
      </div>
    </article>
  );
}
