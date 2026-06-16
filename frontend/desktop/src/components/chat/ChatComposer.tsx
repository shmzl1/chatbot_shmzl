import { Send } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { Button } from "../ui/Button";

interface ChatComposerProps {
  disabled?: boolean;
  focusKey?: string;
  onSend: (message: string) => void;
  suggestedText?: string;
}

export function ChatComposer({ disabled, focusKey, onSend, suggestedText }: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [message, setMessage] = useState(suggestedText || "");

  useEffect(() => {
    if (suggestedText) {
      setMessage(suggestedText);
    }
  }, [suggestedText]);

  useEffect(() => {
    if (!disabled) {
      textareaRef.current?.focus();
    }
  }, [disabled, focusKey]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const value = message.trim();
    if (!value) {
      return;
    }
    setMessage("");
    onSend(value);
  }

  return (
    <form className="chat-composer" onSubmit={submit}>
      <textarea
        ref={textareaRef}
        className="chat-composer-input"
        placeholder="说点什么..."
        disabled={disabled}
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />
      <Button className="h-[70px] w-[92px]" disabled={disabled} type="submit" variant="primary">
        <Send size={18} />
        发送
      </Button>
    </form>
  );
}
