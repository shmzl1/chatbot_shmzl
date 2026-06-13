import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Eraser, MessageCircle } from "lucide-react";
import { useEffect } from "react";
import { listCharacters, listChatSessions, listChatTurns, sendChatMessage } from "../api/chatApi";
import { ChatComposer } from "../components/chat/ChatComposer";
import { CompactContextChip } from "../components/chat/CompactContextChip";
import { MessageBubble } from "../components/chat/MessageBubble";
import { EmptyState } from "../components/ui/EmptyState";
import { Button } from "../components/ui/Button";
import { useAppStore } from "../stores/appStore";
import { useChatStore } from "../stores/chatStore";

export function ChatPage() {
  const queryClient = useQueryClient();
  const selectedDiary = useAppStore((state) => state.selectedDiary);
  const setSelectedDiary = useAppStore((state) => state.setSelectedDiary);
  const pendingChatDraft = useAppStore((state) => state.pendingChatDraft);
  const setPendingChatDraft = useAppStore((state) => state.setPendingChatDraft);
  const sessionId = useChatStore((state) => state.sessionId);
  const messages = useChatStore((state) => state.messages);
  const setSessionId = useChatStore((state) => state.setSessionId);
  const setMessages = useChatStore((state) => state.setMessages);
  const appendMessage = useChatStore((state) => state.appendMessage);
  const clearMessages = useChatStore((state) => state.clearMessages);
  const charactersQuery = useQuery({ queryKey: ["characters"], queryFn: listCharacters, retry: 0 });
  const sessionsQuery = useQuery({ queryKey: ["chat", "sessions"], queryFn: () => listChatSessions(12), retry: 0 });
  const turnsQuery = useQuery({
    queryKey: ["chat", "turns", sessionId],
    queryFn: () => listChatTurns(sessionId!),
    enabled: Boolean(sessionId),
    retry: 0,
  });
  const characterId = charactersQuery.data?.characters?.[0]?.id || "role01";

  useEffect(() => {
    const firstSession = sessionsQuery.data?.sessions?.[0];
    if (!sessionId && !messages.length && firstSession) {
      setSessionId(firstSession.id);
    }
  }, [messages.length, sessionId, sessionsQuery.data, setSessionId]);

  useEffect(() => {
    const turns = turnsQuery.data?.turns;
    if (!turns) {
      return;
    }
    setMessages(
      turns.flatMap((turn) => [
        {
          id: `user-${turn.id}`,
          role: "user" as const,
          content: turn.user_message,
        },
        {
          id: `assistant-${turn.id}`,
          role: "assistant" as const,
          content: turn.reply,
          emotion: turn.emotion,
        },
      ]),
    );
  }, [turnsQuery.data, setMessages]);

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
      void queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
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
          <CompactContextChip selectedDiary={selectedDiary} onClear={() => setSelectedDiary(null)} />
          <Button variant="ghost" onClick={clearMessages}>
            <Eraser size={16} />
            清空
          </Button>
        </div>
      </section>

      {sessionsQuery.error instanceof Error ? (
        <div className="inline-error">{sessionsQuery.error.message}</div>
      ) : sessionsQuery.data?.sessions?.length ? (
        <section className="chat-session-strip" aria-label="最近会话">
          {sessionsQuery.data.sessions.slice(0, 6).map((session) => (
            <button
              className={session.id === sessionId ? "active" : ""}
              key={session.id}
              type="button"
              onClick={() => setSessionId(session.id)}
            >
              <BookOpen size={13} />
              <span>{session.last_user_message || session.last_reply || session.id}</span>
            </button>
          ))}
        </section>
      ) : null}

      <section className="chat-stream paper-sheet">
        {turnsQuery.error instanceof Error ? (
          <EmptyState
            icon={<MessageCircle size={24} />}
            title="聊天记录加载失败"
            description={turnsQuery.error.message}
          />
        ) : messages.length ? (
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

      <ChatComposer
        disabled={sendMutation.isPending || charactersQuery.isLoading}
        suggestedText={pendingChatDraft}
        onSend={(message) => sendMutation.mutate(message)}
      />
    </div>
  );
}
