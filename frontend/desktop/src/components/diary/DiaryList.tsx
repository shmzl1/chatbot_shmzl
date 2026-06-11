import { BookOpen } from "lucide-react";
import { EmptyState } from "../ui/EmptyState";
import { Tag } from "../ui/Tag";
import type { DiaryEntryListItem } from "../../types/diary";

interface DiaryListProps {
  entries: DiaryEntryListItem[];
  activeEntryId: number | null;
  onSelect: (entryId: number) => void;
}

export function DiaryList({ entries, activeEntryId, onSelect }: DiaryListProps) {
  if (!entries.length) {
    return <EmptyState icon={<BookOpen size={22} />} title="还没有日记" description="写一篇今天的记录吧。" />;
  }

  return (
    <div className="grid gap-3">
      {entries.map((entry) => (
        <button
          className={`note-card grid gap-2 rounded-2xl p-4 text-left transition ${
            activeEntryId === entry.id ? "ring-2 ring-[var(--green)]" : "hover:-translate-y-0.5"
          }`}
          key={entry.id}
          type="button"
          onClick={() => onSelect(entry.id)}
        >
          <div className="flex items-center justify-between gap-3">
            <strong className="truncate text-sm">{entry.title || "未命名日记"}</strong>
            <span className="text-xs font-black text-[var(--muted)]">{entry.entry_date}</span>
          </div>
          <p className="line-clamp-2 text-xs leading-5 text-[var(--muted)]">{entry.content_excerpt || "没有正文"}</p>
          <div className="flex flex-wrap gap-1.5">
            {entry.mood ? <Tag>{entry.mood}</Tag> : null}
            {entry.tags.slice(0, 2).map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
            {entry.image_count ? <Tag>{entry.image_count} 图</Tag> : null}
          </div>
        </button>
      ))}
    </div>
  );
}
