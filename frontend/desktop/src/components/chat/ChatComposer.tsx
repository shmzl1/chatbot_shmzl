import { Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Button } from "../ui/Button";

interface ChatComposerProps {
  disabled?: boolean;
  onSend: (message: string) => void;
  suggestedText?: string;
}

export function ChatComposer({ disabled, onSend, suggestedText }: ChatComposerProps) {
  const [message, setMessage] = useState(suggestedText || "");

  useEffect(() => {
    if (suggestedText) {
      setMessage(suggestedText);
    }
  }, [suggestedText]);

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
    <form className="soft-panel flex items-end gap-3 rounded-[24px] p-3" onSubmit={submit}>
      <textarea
        className="min-h-[70px] flex-1 resize-none rounded-2xl border border-transparent bg-[rgba(255,255,255,0.62)] px-4 py-3 text-sm leading-6 outline-none transition focus:border-[var(--green)] focus:bg-white"
        placeholder="说点什么..."
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
