import * as Dialog from "@radix-ui/react-dialog";
import { BookOpen, X } from "lucide-react";
import { Button } from "../ui/Button";
import type { SelectedDiaryContext } from "../../stores/appStore";

interface CompactContextChipProps {
  selectedDiary: SelectedDiaryContext | null;
  onClear: () => void;
}

export function CompactContextChip({ selectedDiary, onClear }: CompactContextChipProps) {
  if (!selectedDiary) {
    return <span className="context-mini-hint">普通聊天</span>;
  }

  return (
    <Dialog.Root>
      <div className="context-chip">
        <BookOpen size={14} />
        <span>日记《{selectedDiary.title || "未命名日记"}》</span>
        <Dialog.Trigger asChild>
          <button type="button">查看</button>
        </Dialog.Trigger>
        <button type="button" onClick={onClear} aria-label="清除日记上下文">
          <X size={13} />
        </button>
      </div>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm" />
        <Dialog.Content className="context-dialog">
          <Dialog.Title>日记详情</Dialog.Title>
          <Dialog.Description>
            本轮聊天会携带这篇日记的内容：{selectedDiary.title || "未命名日记"}。
          </Dialog.Description>
          <div className="context-dialog-actions">
            <Button variant="ghost" onClick={onClear}>
              <X size={15} />
              清除
            </Button>
            <Dialog.Close asChild>
              <Button variant="primary">知道了</Button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
