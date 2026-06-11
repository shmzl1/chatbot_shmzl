import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { BookOpen, Save, Trash2 } from "lucide-react";
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
import { useDiaryStore } from "../stores/diaryStore";
import type { DiaryEntryPayload, DiaryFilters } from "../types/diary";

function today() {
  return new Date().toISOString().slice(0, 10);
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
  const [filters, setFilters] = useState<DiaryFilters>({});
  const [draft, setDraft] = useState<DiaryEntryPayload>({
    title: "",
    content_markdown: "",
    entry_date: today(),
    mood: "",
    tags: [],
  });
  const [tagInput, setTagInput] = useState("");

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
    if (!entry) {
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
  }, [detailQuery.data]);

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
      void queryClient.invalidateQueries({ queryKey: ["diary"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteDiaryEntry(activeEntryId!),
    onSuccess: () => {
      setActiveEntryId(null);
      setDraft({ title: "", content_markdown: "", entry_date: today(), mood: "", tags: [] });
      setTagInput("");
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

  function newEntry() {
    setActiveEntryId(null);
    setDraft({ title: "", content_markdown: "", entry_date: today(), mood: "", tags: [] });
    setTagInput("");
  }

  function readWithCharacter() {
    if (!activeEntryId) {
      window.alert("请先保存日记。");
      return;
    }
    setSelectedDiary({ id: activeEntryId, title: draft.title || "未命名日记" });
    setPendingChatDraft("你看看这篇日记，和我聊聊。");
    setActiveView("chat");
  }

  return (
    <div className="grid h-full grid-cols-[300px_minmax(420px,1fr)_300px] gap-5">
      <aside className="soft-panel min-h-0 overflow-auto rounded-[28px] p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-black">日记列表</h2>
          <Button className="px-3" variant="primary" onClick={newEntry}>
            新建
          </Button>
        </div>
        <div className="mb-4 grid gap-2">
          <TextField placeholder="搜索" onChange={(event) => setFilters((current) => ({ ...current, keyword: event.target.value }))} />
          <div className="grid grid-cols-2 gap-2">
            <TextField type="date" onChange={(event) => setFilters((current) => ({ ...current, date_from: event.target.value }))} />
            <TextField type="date" onChange={(event) => setFilters((current) => ({ ...current, date_to: event.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <TextField placeholder="心情" onChange={(event) => setFilters((current) => ({ ...current, mood: event.target.value }))} />
            <TextField placeholder="标签" onChange={(event) => setFilters((current) => ({ ...current, tag: event.target.value }))} />
          </div>
        </div>
        <DiaryList
          activeEntryId={activeEntryId}
          entries={listQuery.data?.entries || []}
          onSelect={(entryId) => setActiveEntryId(entryId)}
        />
      </aside>

      <PaperPanel className="grid min-h-0 grid-rows-[auto_1fr] gap-4 overflow-hidden">
        <div className="flex items-center justify-between gap-3">
          <input
            className="min-w-0 flex-1 bg-transparent text-3xl font-black outline-none placeholder:text-[rgba(43,41,36,0.32)]"
            placeholder="标题"
            value={draft.title}
            onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
          />
          <Button disabled={saveMutation.isPending} variant="primary" onClick={() => saveMutation.mutate()}>
            <Save size={16} />
            保存
          </Button>
        </div>
        <div className="grid min-h-0 grid-cols-2 gap-4">
          <textarea
            className="min-h-0 resize-none rounded-2xl border border-[var(--line)] bg-[rgba(255,255,255,0.54)] p-4 text-sm leading-7 outline-none focus:border-[var(--green)]"
            placeholder="写今天发生的事..."
            value={draft.content_markdown}
            onChange={(event) => setDraft((current) => ({ ...current, content_markdown: event.target.value }))}
          />
          <div className="min-h-0 overflow-auto rounded-2xl border border-[var(--line)] bg-[rgba(255,255,255,0.42)] p-4">
            <ReactMarkdown className="prose prose-sm max-w-none text-[var(--ink)]">
              {draft.content_markdown || "预览会出现在这里。"}
            </ReactMarkdown>
          </div>
        </div>
      </PaperPanel>

      <aside className="soft-panel min-h-0 overflow-auto rounded-[28px] p-4">
        <div className="mb-4 flex items-center gap-2">
          <BookOpen className="text-[var(--green)]" size={20} />
          <h2 className="text-lg font-black">日记属性</h2>
        </div>
        <div className="grid gap-4">
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
          <TextField label="标签" placeholder="逗号分隔" value={tagInput} onChange={(event) => setTagInput(event.target.value)} />
          <Button variant="secondary" onClick={readWithCharacter}>
            让角色读这篇日记
          </Button>
          <Button disabled={!activeEntryId} variant="danger" onClick={() => deleteMutation.mutate()}>
            <Trash2 size={16} />
            删除日记
          </Button>
          <DiaryImages
            attachments={detailQuery.data?.attachments || []}
            disabled={!activeEntryId}
            onUpload={(files) => uploadMutation.mutate(files)}
            onDelete={(imageId) => deleteImageMutation.mutate(imageId)}
          />
        </div>
      </aside>
    </div>
  );
}
