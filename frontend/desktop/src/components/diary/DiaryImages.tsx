import { ImagePlus, Trash2 } from "lucide-react";
import { resolveAssetUrl } from "../../api/client";
import type { DiaryAttachment } from "../../types/diary";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";

interface DiaryImagesProps {
  attachments: DiaryAttachment[];
  disabled?: boolean;
  onUpload: (files: FileList) => void;
  onDelete: (imageId: number) => void;
}

export function DiaryImages({ attachments, disabled, onUpload, onDelete }: DiaryImagesProps) {
  return (
    <section className="grid gap-3">
      <label className="inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--line)] bg-[var(--surface)] px-4 text-sm font-bold text-[var(--green)] transition hover:bg-[var(--surface-2)]">
        <ImagePlus size={17} />
        上传图片
        <input
          className="hidden"
          disabled={disabled}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          onChange={(event) => {
            if (event.target.files) {
              onUpload(event.target.files);
              event.target.value = "";
            }
          }}
        />
      </label>
      {attachments.length ? (
        <div className="grid grid-cols-2 gap-3">
          {attachments.map((image) => (
            <article className="note-card overflow-hidden rounded-2xl p-2" key={image.id}>
              <img className="aspect-square w-full rounded-xl object-cover" src={resolveAssetUrl(image.public_url)} alt={image.original_filename || image.filename} />
              <div className="mt-2 flex items-center justify-between gap-2">
                <span className="truncate text-xs font-bold text-[var(--muted)]">{image.original_filename || image.filename}</span>
                <Button className="size-8 px-0" variant="ghost" onClick={() => onDelete(image.id)}>
                  <Trash2 size={15} />
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="没有图片" description="保存日记后可以上传 png、jpg、jpeg、webp。" />
      )}
    </section>
  );
}
