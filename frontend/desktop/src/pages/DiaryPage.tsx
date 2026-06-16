import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Filter,
  MessageCircle,
  Plus,
  Save,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  createDiaryEntry,
  deleteDiaryEntry,
  deleteDiaryImage,
  getDiaryEntry,
  listDiaryEntries,
  updateDiaryEntry,
  uploadDiaryImage,
} from "../api/diaryApi";
import { DiaryImages } from "../components/diary/DiaryImages";
import { DiaryList } from "../components/diary/DiaryList";
import { PaperPanel } from "../components/paper/PaperPanel";
import { Button } from "../components/ui/Button";
import { TextField } from "../components/ui/TextField";
import { useAppStore } from "../stores/appStore";
import { useChatStore } from "../stores/chatStore";
import { useDiaryStore } from "../stores/diaryStore";
import type { DiaryEntryPayload, DiaryFilters } from "../types/diary";

function today() {
  return new Date().toISOString().slice(0, 10);
}

function emptyDraft(): DiaryEntryPayload {
  return {
    title: "",
    content_markdown: "",
    entry_date: today(),
    mood: "",
    tags: [],
  };
}

function parseTags(value: string) {
  return value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function DiaryPage() {
  const queryClient = useQueryClient();
  const activeEntryId = useDiaryStore((state) => state.activeEntryId);
  const setActiveEntryId = useDiaryStore((state) => state.setActiveEntryId);
  const setActiveView = useAppStore((state) => state.setActiveView);
  const setSelectedDiary = useAppStore((state) => state.setSelectedDiary);
  const setPendingChatDraft = useAppStore((state) => state.setPendingChatDraft);
  const startNewConversation = useChatStore((state) => state.startNewConversation);
  const [mode, setMode] = useState<"list" | "editor">("list");
  const [editorTab, setEditorTab] = useState<"write" | "preview">("write");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState<DiaryFilters>({});
  const [draft, setDraft] = useState<DiaryEntryPayload>(emptyDraft);
  const [tagInput, setTagInput] = useState("");
  const [localNotice, setLocalNotice] = useState("");

  const listQuery = useQuery({
    queryKey: ["diary", "entries", filters],
    queryFn: () => listDiaryEntries(filters),
  });
  const detailQuery = useQuery({
    queryKey: ["diary", "entry", activeEntryId],
    queryFn: () => getDiaryEntry(activeEntryId!),
    enabled: activeEntryId != null,
  });

  useEffect(() => {
    const entry = detailQuery.data;
    if (!entry || mode !== "editor") {
      return;
    }
    setDraft({
      title: entry.title || "",
      content_markdown: entry.content_markdown || "",
      entry_date: entry.entry_date || today(),
      mood: entry.mood || "",
      tags: entry.tags || [],
    });
    setTagInput((entry.tags || []).join("，"));
  }, [detailQuery.data, mode]);

  const payload = useMemo<DiaryEntryPayload>(
    () => ({
      ...draft,
      tags: parseTags(tagInput),
    }),
    [draft, tagInput],
  );

  const saveMutation = useMutation({
    mutationFn: () => (activeEntryId ? updateDiaryEntry(activeEntryId, payload) : createDiaryEntry(payload)),
    onSuccess: (entry) => {
      setActiveEntryId(entry.id);
      setLocalNotice("");
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDiaryEntry(activeEntryId!),
    onSuccess: () => {
      setActiveEntryId(null);
      setDraft(emptyDraft());
      setTagInput("");
      setMode("list");
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (files: FileList) => {
      if (!activeEntryId) {
        throw new Error("请先保存日记，再上传图片。");
      }
      for (const file of Array.from(files)) {
        await uploadDiaryImage(activeEntryId, file);
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });

  const deleteImageMutation = useMutation({
    mutationFn: deleteDiaryImage,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });

  const listError = listQuery.error instanceof Error ? listQuery.error.message : "";
  const detailError = detailQuery.error instanceof Error ? detailQuery.error.message : "";
  const mutationError =
    saveMutation.error instanceof Error
      ? saveMutation.error.message
      : deleteMutation.error instanceof Error
        ? deleteMutation.error.message
        : uploadMutation.error instanceof Error
          ? uploadMutation.error.message
          : deleteImageMutation.error instanceof Error
            ? deleteImageMutation.error.message
            : "";

  function newEntry() {
    setActiveEntryId(null);
    setDraft(emptyDraft());
    setTagInput("");
    setLocalNotice("");
    setEditorTab("write");
    setMode("editor");
  }

  function openEntry(entryId: number) {
    setActiveEntryId(entryId);
    setEditorTab("write");
    setMode("editor");
  }

  function backToList() {
    setMode("list");
  }

  function readWithCharacter() {
    if (!activeEntryId) {
      setLocalNotice("请先保存日记。");
      return;
    }
    startNewConversation();
    setSelectedDiary({ id: activeEntryId, title: draft.title || "未命名日记" });
    setPendingChatDraft("你看看这篇日记，和我聊聊。");
    setActiveView("chat");
  }

  if (mode === "list") {
    return (
      <div className="diary-page diary-list-view">
        <section className="diary-list-toolbar soft-panel">
          <div className="page-kicker">
            <span>Notebook</span>
            <strong>日记</strong>
          </div>
          <div className="diary-list-actions">
            <TextField
              aria-label="搜索日记"
              placeholder="搜索标题或正文"
              value={filters.keyword || ""}
              onChange={(event) => setFilters((current) => ({ ...current, keyword: event.target.value }))}
            />
            <Button variant="secondary" type="button" onClick={() => setFiltersOpen((current) => !current)}>
              <Filter size={16} />
              筛选
            </Button>
            <Button variant="primary" type="button" onClick={newEntry}>
              <Plus size={16} />
              新建日记
            </Button>
          </div>
        </section>

        {filtersOpen ? (
          <section className="diary-filter-panel soft-panel" aria-label="日记筛选">
            <TextField
              label="开始日期"
              type="date"
              value={filters.date_from || ""}
              onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value }))}
            />
            <TextField
              label="结束日期"
              type="date"
              value={filters.date_to || ""}
              onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value }))}
            />
            <TextField
              label="心情"
              placeholder="例如：烦、累、还行"
              value={filters.mood || ""}
              onChange={(event) => setFilters((current) => ({ ...current, mood: event.target.value }))}
            />
            <TextField
              label="标签"
              placeholder="输入一个标签"
              value={filters.tag || ""}
              onChange={(event) => setFilters((current) => ({ ...current, tag: event.target.value }))}
            />
          </section>
        ) : null}

        {listError ? (
          <div className="inline-error diary-list-error">
            <AlertCircle size={16} />
            <span>{listError}</span>
            <Button className="ml-auto h-8 min-h-8 px-3" variant="ghost" type="button" onClick={() => void listQuery.refetch()}>
              重试
            </Button>
          </div>
        ) : listQuery.isLoading ? (
          <div className="paper-empty">正在读取日记...</div>
        ) : (
          <DiaryList
            activeEntryId={activeEntryId}
            entries={listQuery.data?.entries || []}
            onSelect={openEntry}
          />
        )}
      </div>
    );
  }

  return (
    <div className="diary-page diary-editor-view">
      <section className="diary-editor-toolbar soft-panel">
        <Button variant="ghost" type="button" onClick={backToList}>
          <ArrowLeft size={16} />
          返回列表
        </Button>
        <div className="diary-editor-heading">
          <span>{activeEntryId ? "编辑日记" : "新建日记"}</span>
          <strong>{draft.title || "未命名日记"}</strong>
        </div>
        <div className="diary-editor-actions">
          <Button disabled={saveMutation.isPending} variant="primary" type="button" onClick={() => saveMutation.mutate()}>
            <Save size={16} />
            保存
          </Button>
          <Button disabled={!activeEntryId || deleteMutation.isPending} variant="danger" type="button" onClick={() => deleteMutation.mutate()}>
            <Trash2 size={16} />
            删除
          </Button>
        </div>
      </section>

      {detailError || mutationError ? (
        <div className="inline-error">
          <AlertCircle size={16} />
          <span>{detailError || mutationError}</span>
        </div>
      ) : null}

      <section className="diary-editor-layout">
        <PaperPanel className="diary-writing-panel">
          <input
            className="diary-title-input"
            placeholder="标题"
            value={draft.title}
            onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
          />
          <div className="diary-tab-row" role="tablist" aria-label="日记正文">
            <button className={editorTab === "write" ? "active" : ""} type="button" onClick={() => setEditorTab("write")}>
              写作
            </button>
            <button className={editorTab === "preview" ? "active" : ""} type="button" onClick={() => setEditorTab("preview")}>
              预览
            </button>
          </div>
          {editorTab === "write" ? (
            <textarea
              className="diary-textarea"
              placeholder="写今天发生的事..."
              value={draft.content_markdown}
              onChange={(event) => setDraft((current) => ({ ...current, content_markdown: event.target.value }))}
            />
          ) : (
            <div className="markdown-preview markdown-selectable">
              <ReactMarkdown>
                {draft.content_markdown || "暂无内容"}
              </ReactMarkdown>
            </div>
          )}
        </PaperPanel>

        <aside className="diary-info-panel soft-panel">
          <div className="diary-materials-title">
            <BookOpen className="text-[var(--green)]" size={20} />
            <h2>日记信息</h2>
          </div>
          <div className="diary-meta-grid">
            <TextField
              label="日期"
              type="date"
              value={draft.entry_date}
              onChange={(event) => setDraft((current) => ({ ...current, entry_date: event.target.value }))}
            />
            <TextField
              label="心情"
              placeholder="例如：烦、累、还行"
              value={draft.mood}
              onChange={(event) => setDraft((current) => ({ ...current, mood: event.target.value }))}
            />
            <TextField
              className="diary-tags-input"
              label="标签"
              placeholder="逗号分隔"
              value={tagInput}
              onChange={(event) => setTagInput(event.target.value)}
            />
          </div>
          <div className="tag-preview-row">
            {parseTags(tagInput).map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
          <Button variant="secondary" type="button" onClick={readWithCharacter}>
            <MessageCircle size={16} />
            让角色读这篇日记
          </Button>
          {localNotice ? <div className="inline-error"><span>{localNotice}</span></div> : null}
          <DiaryImages
            attachments={detailQuery.data?.attachments || []}
            disabled={!activeEntryId}
            onUpload={(files) => uploadMutation.mutate(files)}
            onDelete={(imageId) => deleteImageMutation.mutate(imageId)}
            onDisabledUpload={() => setLocalNotice("请先保存日记。")}
          />
        </aside>
      </section>
    </div>
  );
}
