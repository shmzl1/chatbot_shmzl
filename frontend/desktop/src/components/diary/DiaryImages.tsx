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
  onDisabledUpload?: () => void;
}

export function DiaryImages({ attachments, disabled, onUpload, onDelete, onDisabledUpload }: DiaryImagesProps) {
  const safeAttachments = Array.isArray(attachments) ? attachments : [];

  return (
    <section className="diary-images">
      <label className={`image-upload-button ${disabled ? "disabled" : ""}`} onClick={() => disabled && onDisabledUpload?.()}>
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
      {safeAttachments.length ? (
        <div className="image-grid">
          {safeAttachments.map((image) => (
            <article className="image-tile" key={image.id}>
              <img src={resolveAssetUrl(image.public_url)} alt={image.original_filename || image.filename} />
              <div>
                <span>{image.original_filename || image.filename}</span>
                <Button className="size-8 px-0" variant="ghost" type="button" onClick={() => onDelete(image.id)}>
                  <Trash2 size={15} />
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="没有图片" />
      )}
    </section>
  );
}
