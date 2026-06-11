import { clsx } from "clsx";
import type { ChatMessage } from "../../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  return (
    <article className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={clsx(
          "max-w-[76%] rounded-[22px] px-5 py-4 leading-7 shadow-soft",
          isUser
            ? "bg-[var(--blue)] text-white"
            : "paper-sheet rounded-bl-md text-[var(--ink)]",
        )}
      >
        <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        {message.emotion ? <span className="mt-2 block text-xs font-black text-[var(--gold)]">{message.emotion}</span> : null}
      </div>
    </article>
  );
}
