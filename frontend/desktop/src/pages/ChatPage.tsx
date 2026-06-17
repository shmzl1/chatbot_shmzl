import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  ArchiveRestore,
  BookOpen,
  Check,
  Edit3,
  Menu,
  MessageCircle,
  MoreHorizontal,
  Plus,
  Search,
  UserRoundCog,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  archiveChatSession,
  listCharacters,
  listChatSessions,
  listChatTurns,
  renameChatSession,
  sendChatMessage,
  unarchiveChatSession,
} from "../api/chatApi";
import { ChatComposer } from "../components/chat/ChatComposer";
import { CompactContextChip } from "../components/chat/CompactContextChip";
import { MessageBubble } from "../components/chat/MessageBubble";
import { CharacterSelector } from "../components/character/CharacterSelector";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { TextField } from "../components/ui/TextField";
import { PersonaReviewDialog } from "../components/persona/PersonaReviewDialog";
import { useAppStore } from "../stores/appStore";
import { useChatStore } from "../stores/chatStore";
import type { ChatSessionSummary } from "../types/chat";
import { turnToPersonaReviewTurn } from "../types/personaReview";

function useDebouncedValue(value: string, delay = 260) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [delay, value]);

  return debounced;
}

function sessionTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleString("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function groupSessions(sessions: ChatSessionSummary[]) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;
  const startOfWeek = startOfToday - 6 * 24 * 60 * 60 * 1000;
  const groups: Array<{ label: string; sessions: ChatSessionSummary[] }> = [
    { label: "今天", sessions: [] },
    { label: "昨天", sessions: [] },
    { label: "最近 7 天", sessions: [] },
    { label: "更早", sessions: [] },
  ];

  sessions.forEach((session) => {
    const time = new Date(session.updated_at).getTime();
    if (time >= startOfToday) {
      groups[0].sessions.push(session);
    } else if (time >= startOfYesterday) {
      groups[1].sessions.push(session);
    } else if (time >= startOfWeek) {
      groups[2].sessions.push(session);
    } else {
      groups[3].sessions.push(session);
    }
  });

  return groups.filter((group) => group.sessions.length);
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "";
}

export function ChatPage() {
  const queryClient = useQueryClient();
  const selectedDiary = useAppStore((state) => state.selectedDiary);
  const setSelectedDiary = useAppStore((state) => state.setSelectedDiary);
  const pendingChatDraft = useAppStore((state) => state.pendingChatDraft);
  const setPendingChatDraft = useAppStore((state) => state.setPendingChatDraft);
  const selectedCharacterId = useAppStore((state) => state.selectedCharacterId);
  const setSelectedCharacterId = useAppStore((state) => state.setSelectedCharacterId);
  const activeSessionId = useChatStore((state) => state.activeSessionId);
  const conversationMode = useChatStore((state) => state.conversationMode);
  const sessionSidebarOpen = useChatStore((state) => state.sessionSidebarOpen);
  const sessionSearch = useChatStore((state) => state.sessionSearch);
  const sessionListMode = useChatStore((state) => state.sessionListMode);
  const messages = useChatStore((state) => state.messages);
  const setActiveSessionId = useChatStore((state) => state.setActiveSessionId);
  const selectSession = useChatStore((state) => state.selectSession);
  const startNewConversation = useChatStore((state) => state.startNewConversation);
  const setSessionSidebarOpen = useChatStore((state) => state.setSessionSidebarOpen);
  const setSessionSearch = useChatStore((state) => state.setSessionSearch);
  const setSessionListMode = useChatStore((state) => state.setSessionListMode);
  const setMessages = useChatStore((state) => state.setMessages);
  const appendMessage = useChatStore((state) => state.appendMessage);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [renameTarget, setRenameTarget] = useState<ChatSessionSummary | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [renameError, setRenameError] = useState("");
  const [roleNotice, setRoleNotice] = useState("");
  const [personaReviewOpen, setPersonaReviewOpen] = useState(false);
  const debouncedSearch = useDebouncedValue(sessionSearch);

  const charactersQuery = useQuery({ queryKey: ["characters"], queryFn: listCharacters, retry: 0 });
  const sessionsQuery = useQuery({
    queryKey: ["chat", "sessions", sessionListMode, debouncedSearch, 50, 0],
    queryFn: () =>
      listChatSessions({
        query: debouncedSearch,
        archived: sessionListMode === "archived",
        limit: 50,
        offset: 0,
      }),
    retry: 0,
  });
  const turnsQuery = useQuery({
    queryKey: ["chat", "turns", activeSessionId],
    queryFn: () => listChatTurns(activeSessionId!),
    enabled: Boolean(activeSessionId),
    retry: 0,
  });
  const currentCharacter = charactersQuery.data?.characters.find((character) => character.id === selectedCharacterId) || null;
  const sessions = sessionsQuery.data?.sessions || [];
  const currentSession = sessions.find((session) => session.id === activeSessionId);
  const reviewCharacterId = currentSession?.character_id || turnsQuery.data?.turns?.[0]?.character_id || null;
  const reviewCharacter = charactersQuery.data?.characters.find((character) => character.id === reviewCharacterId) || null;
  const characterName = reviewCharacter?.display_name || currentCharacter?.display_name || "选择角色";
  const reviewTurns = (turnsQuery.data?.turns || []).map(turnToPersonaReviewTurn);
  const canOpenPersonaReview = Boolean(activeSessionId && reviewCharacterId && reviewTurns.length && !turnsQuery.isLoading && !turnsQuery.error);
  const isArchivedView = conversationMode === "archived";
  const groupedSessions = useMemo(() => groupSessions(sessions), [sessions]);

  useEffect(() => {
    const turns = turnsQuery.data?.turns;
    if (!turns || !activeSessionId) {
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
  }, [activeSessionId, turnsQuery.data, setMessages]);

  useEffect(() => {
    if (renameTarget) {
      setRenameTitle(renameTarget.title);
      setRenameError("");
    }
  }, [renameTarget]);

  const invalidateSessions = () => {
    void queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
  };

  const sendMutation = useMutation({
    mutationFn: async (message: string) => {
      appendMessage({ id: crypto.randomUUID(), role: "user", content: message });
      setPendingChatDraft("");
      if (!currentCharacter) {
        throw new Error("请先选择角色。");
      }
      return sendChatMessage({
        character_id: currentCharacter.id,
        message,
        session_id: conversationMode === "existing" ? activeSessionId : null,
        diary_entry_id: selectedDiary?.id ?? null,
      });
    },
    onSuccess: (payload) => {
      if (payload.session_id) {
        setActiveSessionId(payload.session_id);
      }
      appendMessage({
        id: String(payload.turn_id || crypto.randomUUID()),
        role: "assistant",
        content: payload.reply,
        emotion: payload.emotion,
      });
      invalidateSessions();
      void queryClient.invalidateQueries({ queryKey: ["chat", "turns", payload.session_id] });
    },
    onError: (error) => {
      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: errorMessage(error) || "聊天请求失败",
        emotion: "error",
      });
    },
  });

  const renameMutation = useMutation({
    mutationFn: () => renameChatSession(renameTarget!.id, { title: renameTitle }),
    onSuccess: () => {
      setRenameTarget(null);
      setRenameError("");
      invalidateSessions();
    },
    onError: (error) => setRenameError(errorMessage(error) || "重命名失败"),
  });

  const archiveMutation = useMutation({
    mutationFn: archiveChatSession,
    onSuccess: (_, sessionId) => {
      setOpenMenuId(null);
      if (activeSessionId === sessionId) {
        startNewConversation();
      }
      invalidateSessions();
    },
  });

  const unarchiveMutation = useMutation({
    mutationFn: unarchiveChatSession,
    onSuccess: (payload) => {
      setOpenMenuId(null);
      setSessionListMode("active");
      selectSession(payload.session.id, "existing");
      invalidateSessions();
    },
  });

  function newConversation() {
    setPersonaReviewOpen(false);
    startNewConversation();
    setSelectedDiary(null);
  }

  function chooseSession(session: ChatSessionSummary) {
    setPersonaReviewOpen(false);
    setSelectedCharacterId(session.character_id);
    selectSession(session.id, session.is_archived ? "archived" : "existing");
  }

  function handleCharacterChange() {
    setPersonaReviewOpen(false);
    if (activeSessionId && conversationMode !== "new") {
      startNewConversation();
      setSelectedDiary(null);
      setRoleNotice("已切换角色，将开始新的对话。");
    }
  }

  function openRename(session: ChatSessionSummary) {
    setOpenMenuId(null);
    setRenameTarget(session);
  }

  function saveRename() {
    if (!renameTitle.trim()) {
      setRenameError("标题不能为空。");
      return;
    }
    renameMutation.mutate();
  }

  const actionError = errorMessage(archiveMutation.error) || errorMessage(unarchiveMutation.error);
  const chatTitle = currentSession?.title || (conversationMode === "new" ? "新对话" : "对话");

  useEffect(() => {
    if (!roleNotice) {
      return;
    }
    const timer = window.setTimeout(() => setRoleNotice(""), 2400);
    return () => window.clearTimeout(timer);
  }, [roleNotice]);

  return (
    <div className="chat-workspace chat-with-sidebar">
      <button className="chat-sidebar-toggle" type="button" onClick={() => setSessionSidebarOpen(true)}>
        <Menu size={16} />
        对话
      </button>
      {sessionSidebarOpen ? <button className="chat-sidebar-scrim" type="button" aria-label="关闭会话列表" onClick={() => setSessionSidebarOpen(false)} /> : null}
      <aside className={`chat-session-sidebar ${sessionSidebarOpen ? "open" : ""}`}>
        <div className="chat-session-sidebar-head">
          <Button variant="primary" type="button" onClick={newConversation}>
            <Plus size={16} />
            新建对话
          </Button>
          <button className="chat-sidebar-close" type="button" onClick={() => setSessionSidebarOpen(false)} aria-label="关闭会话列表">
            <X size={16} />
          </button>
        </div>
        <label className="chat-session-search">
          <Search size={15} />
          <input
            placeholder="搜索对话"
            value={sessionSearch}
            onChange={(event) => setSessionSearch(event.target.value)}
          />
        </label>
        <div className="chat-session-tabs">
          <button className={sessionListMode === "active" ? "active" : ""} type="button" onClick={() => setSessionListMode("active")}>
            对话
          </button>
          <button className={sessionListMode === "archived" ? "active" : ""} type="button" onClick={() => setSessionListMode("archived")}>
            已归档
          </button>
        </div>
        {sessionsQuery.error instanceof Error ? (
          <div className="inline-error"><span>{sessionsQuery.error.message}</span></div>
        ) : sessionsQuery.isLoading ? (
          <div className="paper-empty">正在读取对话...</div>
        ) : sessions.length ? (
          <div className="chat-session-list">
            {groupedSessions.map((group) => (
              <section key={group.label}>
                <h3>{group.label}</h3>
                {group.sessions.map((session) => (
                  <article className={`chat-session-item ${session.id === activeSessionId ? "active" : ""}`} key={session.id}>
                    <button type="button" onClick={() => chooseSession(session)}>
                      <strong>{session.title || "未命名对话"}</strong>
                      <span>{sessionTime(session.updated_at)}</span>
                    </button>
                    <div className="chat-session-menu-wrap">
                      <button type="button" aria-label="会话操作" onClick={() => setOpenMenuId((current) => current === session.id ? null : session.id)}>
                        <MoreHorizontal size={16} />
                      </button>
                      {openMenuId === session.id ? (
                        <div className="chat-session-menu">
                          {!session.is_archived ? (
                            <>
                              <button type="button" onClick={() => openRename(session)}>
                                <Edit3 size={14} />
                                重命名
                              </button>
                              <button type="button" onClick={() => archiveMutation.mutate(session.id)}>
                                <Archive size={14} />
                                归档
                              </button>
                            </>
                          ) : (
                            <button type="button" onClick={() => unarchiveMutation.mutate(session.id)}>
                              <ArchiveRestore size={14} />
                              恢复
                            </button>
                          )}
                        </div>
                      ) : null}
                    </div>
                  </article>
                ))}
              </section>
            ))}
          </div>
        ) : (
          <div className="paper-empty">{sessionListMode === "archived" ? "没有归档对话。" : "还没有对话。"}</div>
        )}
        {actionError ? <div className="inline-error"><span>{actionError}</span></div> : null}
      </aside>

      <section className="chat-main-panel">
        <section className="chat-hero">
          <div className="chat-character-card">
            <div className="chat-character-avatar">
              <MessageCircle size={22} />
            </div>
            <div>
              <p className="eyebrow">Chat</p>
              <h2>{chatTitle}</h2>
              <span>{characterName}</span>
            </div>
          </div>
          <div className="chat-context-actions">
            <CharacterSelector onCharacterChange={handleCharacterChange} />
            <Button
              variant="secondary"
              type="button"
              disabled={!canOpenPersonaReview}
              title={canOpenPersonaReview ? "打开人设修正工作台" : "当前对话还没有可修正的角色回复"}
              onClick={() => setPersonaReviewOpen(true)}
            >
              <UserRoundCog size={16} />
              人设修正
            </Button>
            <CompactContextChip selectedDiary={selectedDiary} onClear={() => setSelectedDiary(null)} />
            {isArchivedView ? (
              <Button variant="secondary" type="button" onClick={() => activeSessionId && unarchiveMutation.mutate(activeSessionId)}>
                <ArchiveRestore size={16} />
                恢复
              </Button>
            ) : null}
          </div>
        </section>

        {isArchivedView ? (
          <div className="chat-archived-banner">
            <Archive size={16} />
            <span>已归档</span>
          </div>
        ) : null}
        {roleNotice ? <div className="chat-role-notice">{roleNotice}</div> : null}

        <section className="chat-stream paper-sheet">
          {turnsQuery.error instanceof Error ? (
            <div className="chat-centered-state">
              <EmptyState
                icon={<MessageCircle size={24} />}
                title="聊天记录加载失败"
                description={turnsQuery.error.message}
              />
              <Button variant="secondary" type="button" onClick={() => void turnsQuery.refetch()}>
                重试
              </Button>
            </div>
          ) : activeSessionId && turnsQuery.isLoading ? (
            <div className="paper-empty">正在读取消息...</div>
          ) : messages.length ? (
            <div className="chat-message-stack">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={selectedDiary ? <BookOpen size={24} /> : <MessageCircle size={24} />}
              title="开始新的对话"
              description={selectedDiary ? `日记：《${selectedDiary.title || "未命名日记"}》` : currentCharacter ? "随便说点什么。" : "请先选择角色。"}
            />
          )}
        </section>

        <ChatComposer
          disabled={sendMutation.isPending || charactersQuery.isLoading || Boolean(charactersQuery.error) || !currentCharacter || isArchivedView}
          suggestedText={pendingChatDraft}
          focusKey={`${conversationMode}-${activeSessionId || "new"}-${pendingChatDraft}`}
          onSend={(message) => sendMutation.mutate(message)}
        />
      </section>

      <Dialog.Root open={Boolean(renameTarget)} onOpenChange={(open) => !open && setRenameTarget(null)}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm" />
          <Dialog.Content className="context-dialog">
            <Dialog.Title>重命名对话</Dialog.Title>
            <div className="mt-4 grid gap-3">
              <TextField value={renameTitle} maxLength={100} onChange={(event) => setRenameTitle(event.target.value)} />
              {renameError ? <div className="inline-error"><span>{renameError}</span></div> : null}
              <div className="context-dialog-actions">
                <Dialog.Close asChild>
                  <Button variant="ghost" type="button">取消</Button>
                </Dialog.Close>
                <Button disabled={renameMutation.isPending} variant="primary" type="button" onClick={saveRename}>
                  <Check size={16} />
                  保存
                </Button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <PersonaReviewDialog
        open={personaReviewOpen}
        onOpenChange={setPersonaReviewOpen}
        characterId={reviewCharacterId}
        characterName={reviewCharacter?.display_name || reviewCharacterId || "未选择角色"}
        sessionId={activeSessionId}
        turns={reviewTurns}
        onPersonaChanged={() => {
          void queryClient.invalidateQueries({ queryKey: ["characters"] });
        }}
      />
    </div>
  );
}
