import { useEffect, useMemo, useState } from "react";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";
import type { ScheduleItemDetail, ScheduleItemPayload, ScheduleItemType } from "../../types/schedule";
import { schedulePriorityLabels, scheduleTypeLabels } from "../../types/schedule";

interface ScheduleTaskFormProps {
  mode: "create" | "edit";
  selectedDate: string;
  item?: ScheduleItemDetail;
  isPending?: boolean;
  error?: string;
  onSubmit: (payload: ScheduleItemPayload) => void;
  onCancel: () => void;
}

function tagsToInput(tags: string[]): string {
  return tags.join("，");
}

function parseTags(value: string): string[] {
  const result: string[] = [];
  value
    .split(/[,，]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((tag) => {
      if (!result.includes(tag) && result.length < 20) {
        result.push(tag);
      }
    });
  return result;
}

export function ScheduleTaskForm({
  mode,
  selectedDate,
  item,
  isPending,
  error,
  onSubmit,
  onCancel,
}: ScheduleTaskFormProps) {
  const currentOccurrence = item?.current_occurrence;
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [itemType, setItemType] = useState<ScheduleItemType>("task");
  const [priority, setPriority] = useState(3);
  const [scheduledDate, setScheduledDate] = useState(selectedDate);
  const [scheduledTime, setScheduledTime] = useState("");
  const [estimatedMinutes, setEstimatedMinutes] = useState("");
  const [tags, setTags] = useState("");
  const [localError, setLocalError] = useState("");

  useEffect(() => {
    if (mode === "edit" && item) {
      setTitle(item.title);
      setNote(item.note || "");
      setItemType(item.item_type);
      setPriority(item.priority);
      setScheduledDate(currentOccurrence?.scheduled_date || selectedDate);
      setScheduledTime(currentOccurrence?.scheduled_time || "");
      setEstimatedMinutes(item.estimated_minutes ? String(item.estimated_minutes) : "");
      setTags(tagsToInput(item.tags || []));
      return;
    }
    setTitle("");
    setNote("");
    setItemType("task");
    setPriority(3);
    setScheduledDate(selectedDate);
    setScheduledTime("");
    setEstimatedMinutes("");
    setTags("");
  }, [currentOccurrence?.scheduled_date, currentOccurrence?.scheduled_time, item, mode, selectedDate]);

  const tagPreview = useMemo(() => parseTags(tags), [tags]);

  function submit() {
    const cleanTitle = title.trim();
    if (!cleanTitle) {
      setLocalError("标题不能为空。");
      return;
    }
    const minutes = estimatedMinutes.trim() ? Number(estimatedMinutes) : null;
    if (minutes !== null && (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440)) {
      setLocalError("预计用时必须是 1 到 1440 的整数分钟。");
      return;
    }
    setLocalError("");
    onSubmit({
      title: cleanTitle,
      note: note.trim(),
      item_type: itemType,
      priority,
      tags: tagPreview,
      estimated_minutes: minutes,
      scheduled_date: scheduledDate,
      scheduled_time: scheduledTime || null,
    });
  }

  return (
    <form className="schedule-task-form" onSubmit={(event) => { event.preventDefault(); submit(); }}>
      <TextField label="标题" value={title} maxLength={200} onChange={(event) => setTitle(event.target.value)} />
      <label className="text-field">
        <span>备注</span>
        <textarea className="schedule-note-input" value={note} maxLength={10000} onChange={(event) => setNote(event.target.value)} />
      </label>
      <div className="schedule-form-grid">
        <label className="text-field">
          <span>类型</span>
          <select className="text-field-input" value={itemType} onChange={(event) => setItemType(event.target.value as ScheduleItemType)}>
            {(Object.keys(scheduleTypeLabels) as ScheduleItemType[]).map((type) => (
              <option key={type} value={type}>{scheduleTypeLabels[type]}</option>
            ))}
          </select>
        </label>
        <label className="text-field">
          <span>优先级</span>
          <select className="text-field-input" value={priority} onChange={(event) => setPriority(Number(event.target.value))}>
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>{schedulePriorityLabels[value]}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="schedule-form-grid">
        <TextField label="日期" type="date" value={scheduledDate} onChange={(event) => setScheduledDate(event.target.value)} />
        <TextField label="时间" type="time" value={scheduledTime} onChange={(event) => setScheduledTime(event.target.value)} />
      </div>
      <TextField
        label="预计用时（分钟）"
        type="number"
        min={1}
        max={1440}
        value={estimatedMinutes}
        onChange={(event) => setEstimatedMinutes(event.target.value)}
      />
      <TextField label="标签" placeholder="逗号分隔" value={tags} onChange={(event) => setTags(event.target.value)} />
      <div className="schedule-tag-preview">
        {tagPreview.map((tag) => <span key={tag}>{tag}</span>)}
      </div>
      {localError || error ? <div className="inline-error"><span>{localError || error}</span></div> : null}
      <div className="schedule-form-actions">
        <Button variant="ghost" type="button" onClick={onCancel}>取消</Button>
        <Button disabled={isPending} variant="primary" type="submit">
          {mode === "create" ? "创建任务" : "保存修改"}
        </Button>
      </div>
    </form>
  );
}
