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
    <form className="chat-composer" onSubmit={submit}>
      <textarea
        className="chat-composer-input"
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
