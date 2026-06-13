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
    <div className="diary-note-list">
      {entries.map((entry) => (
        <button
          className={`diary-note-card ${activeEntryId === entry.id ? "active" : ""}`}
          key={entry.id}
          type="button"
          onClick={() => onSelect(entry.id)}
        >
          <div className="diary-note-card-head">
            <strong>{entry.title || "未命名日记"}</strong>
            <span>{entry.entry_date}</span>
          </div>
          <p>{entry.content_excerpt || "没有正文"}</p>
          <div className="diary-note-card-tags">
            {entry.mood ? <Tag>{entry.mood}</Tag> : null}
            {(Array.isArray(entry.tags) ? entry.tags : []).slice(0, 2).map((tag) => (
              <Tag key={tag}>{tag}</Tag>
            ))}
            {entry.image_count ? <Tag>{entry.image_count} 图</Tag> : null}
          </div>
        </button>
      ))}
    </div>
  );
}
