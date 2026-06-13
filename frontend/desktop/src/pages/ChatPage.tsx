import { useMutation, useQuery } from "@tanstack/react-query";
import { BookOpen, Eraser, MessageCircle } from "lucide-react";
import { listCharacters, sendChatMessage } from "../api/chatApi";
import { ChatComposer } from "../components/chat/ChatComposer";
import { MessageBubble } from "../components/chat/MessageBubble";
import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { Tag } from "../components/ui/Tag";
import { useAppStore } from "../stores/appStore";
import { useChatStore } from "../stores/chatStore";

export function ChatPage() {
  const selectedDiary = useAppStore((state) => state.selectedDiary);
  const setSelectedDiary = useAppStore((state) => state.setSelectedDiary);
  const pendingChatDraft = useAppStore((state) => state.pendingChatDraft);
  const setPendingChatDraft = useAppStore((state) => state.setPendingChatDraft);
  const sessionId = useChatStore((state) => state.sessionId);
  const messages = useChatStore((state) => state.messages);
  const setSessionId = useChatStore((state) => state.setSessionId);
  const appendMessage = useChatStore((state) => state.appendMessage);
  const clearMessages = useChatStore((state) => state.clearMessages);
  const charactersQuery = useQuery({ queryKey: ["characters"], queryFn: listCharacters });
  const characterId = charactersQuery.data?.characters?.[0]?.id || "role01";

  const sendMutation = useMutation({
    mutationFn: async (message: string) => {
      appendMessage({ id: crypto.randomUUID(), role: "user", content: message });
      setPendingChatDraft("");
      return sendChatMessage({
        character_id: characterId,
        message,
        session_id: sessionId,
        diary_entry_id: selectedDiary?.id ?? null,
      });
    },
    onSuccess: (payload) => {
      if (payload.session_id) {
        setSessionId(payload.session_id);
      }
      appendMessage({
        id: String(payload.turn_id || crypto.randomUUID()),
        role: "assistant",
        content: payload.reply,
        emotion: payload.emotion,
      });
    },
    onError: (error) => {
      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: error instanceof Error ? error.message : "聊天请求失败",
        emotion: "error",
      });
    },
  });

  return (
    <div className="chat-workspace">
      <section className="chat-hero">
        <div className="chat-character-card">
          <div className="chat-character-avatar">
            <MessageCircle size={22} />
          </div>
          <div>
            <p className="eyebrow">Chat</p>
            <h2>{charactersQuery.data?.characters?.[0]?.display_name || "role01"}</h2>
            <span>柔和对话流</span>
          </div>
        </div>
        <div className="chat-context-actions">
          {selectedDiary ? (
            <Tag>
              <BookOpen size={13} />
              正在阅读：{selectedDiary.title || "未命名日记"}
            </Tag>
          ) : null}
          <Button variant="ghost" onClick={clearMessages}>
            <Eraser size={16} />
            清空
          </Button>
        </div>
      </section>

      <section className="chat-stream paper-sheet">
        {messages.length ? (
          <div className="chat-message-stack">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<MessageCircle size={24} />}
            title="开始聊天"
            description="普通聊天不会读取日记。只有你在日记页选择一篇日记后，聊天才会带上那篇日记。"
          />
        )}
      </section>

      {selectedDiary ? (
        <div className="chat-diary-context">
          <span>本轮发送会携带日记上下文：{selectedDiary.title || "未命名日记"}</span>
          <Button variant="ghost" onClick={() => setSelectedDiary(null)}>
            清空上下文
          </Button>
        </div>
      ) : null}

      <ChatComposer
        disabled={sendMutation.isPending || charactersQuery.isLoading}
        suggestedText={pendingChatDraft}
        onSend={(message) => sendMutation.mutate(message)}
      />
    </div>
  );
}
