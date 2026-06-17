import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CalendarDays,
  Check,
  Clock3,
  Edit3,
  FastForward,
  Plus,
  SlidersHorizontal,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import {
  completeScheduleOccurrence,
  createScheduleItem,
  deleteScheduleItem,
  getScheduleCalendar,
  getScheduleDay,
  getScheduleItem,
  postponeScheduleOccurrence,
  skipScheduleOccurrence,
  updateScheduleItem,
} from "../api/scheduleApi";
import { MonthCalendar } from "../components/schedule/CalendarSkeleton";
import { ScheduleTaskForm } from "../components/schedule/ScheduleTaskForm";
import { CharacterSelector } from "../components/character/CharacterSelector";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { TextField } from "../components/ui/TextField";
import { useScheduleStore } from "../stores/scheduleStore";
import type { ScheduleItemPayload, ScheduleItemSummary, ScheduleItemType, ScheduleOccurrenceStatus } from "../types/schedule";
import { schedulePriorityLabels, scheduleStatusLabels, scheduleTypeLabels } from "../types/schedule";
import { formatMonthKey, formatReadableDate, isToday, parseLocalDate } from "../utils/date";

const typeOptions: Array<{ value: ScheduleItemType | ""; label: string }> = [
  { value: "", label: "全部类型" },
  { value: "study_point", label: "学习" },
  { value: "task", label: "事项" },
  { value: "review_point", label: "复习" },
  { value: "habit", label: "习惯" },
];

const statusOptions: Array<{ value: ScheduleOccurrenceStatus | ""; label: string }> = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "待处理" },
  { value: "done", label: "已完成" },
  { value: "postponed", label: "已延期" },
  { value: "skipped", label: "已跳过" },
  { value: "overdue", label: "已逾期" },
];

function activeStatus(status: ScheduleOccurrenceStatus) {
  return status === "pending" || status === "overdue";
}

function mutationError(error: unknown): string {
  return error instanceof Error ? error.message : "";
}

export function SchedulePage() {
  const queryClient = useQueryClient();
  const selectedDate = useScheduleStore((state) => state.selectedDate);
  const selectedMonth = useScheduleStore((state) => state.selectedMonth);
  const selectedItemId = useScheduleStore((state) => state.selectedItemId);
  const itemTypeFilter = useScheduleStore((state) => state.itemTypeFilter);
  const statusFilter = useScheduleStore((state) => state.statusFilter);
  const editorMode = useScheduleStore((state) => state.editorMode);
  const setSelectedDate = useScheduleStore((state) => state.setSelectedDate);
  const setSelectedMonth = useScheduleStore((state) => state.setSelectedMonth);
  const selectItem = useScheduleStore((state) => state.selectItem);
  const openCreate = useScheduleStore((state) => state.openCreate);
  const openEdit = useScheduleStore((state) => state.openEdit);
  const clearSelection = useScheduleStore((state) => state.clearSelection);
  const closeEditor = useScheduleStore((state) => state.closeEditor);
  const setItemTypeFilter = useScheduleStore((state) => state.setItemTypeFilter);
  const setStatusFilter = useScheduleStore((state) => state.setStatusFilter);
  const [postponeTarget, setPostponeTarget] = useState<ScheduleItemSummary | null>(null);
  const [postponeDate, setPostponeDate] = useState(selectedDate);
  const [postponeTime, setPostponeTime] = useState("");
  const [postponeError, setPostponeError] = useState("");
  const [filterOpen, setFilterOpen] = useState(false);

  const dayQuery = useQuery({
    queryKey: ["schedule", "day", selectedDate, itemTypeFilter, statusFilter],
    queryFn: () => getScheduleDay({
      date: selectedDate,
      item_type: itemTypeFilter || undefined,
      status: statusFilter || undefined,
    }),
    retry: 0,
  });
  const calendarQuery = useQuery({
    queryKey: ["schedule", "calendar", selectedMonth],
    queryFn: () => getScheduleCalendar(selectedMonth),
    retry: 0,
  });
  const detailQuery = useQuery({
    queryKey: ["schedule", "item", selectedItemId],
    queryFn: () => getScheduleItem(selectedItemId!),
    enabled: selectedItemId != null,
    retry: 0,
  });

  const invalidateSchedule = () => {
    void queryClient.invalidateQueries({ queryKey: ["schedule"] });
  };

  const createMutation = useMutation({
    mutationFn: createScheduleItem,
    onSuccess: (item) => {
      selectItem(item.id, item.current_occurrence.id);
      setSelectedDate(item.current_occurrence.scheduled_date);
      invalidateSchedule();
    },
  });
  const updateMutation = useMutation({
    mutationFn: (payload: ScheduleItemPayload) => updateScheduleItem(selectedItemId!, payload),
    onSuccess: (item) => {
      selectItem(item.id, item.current_occurrence.id);
      setSelectedDate(item.current_occurrence.scheduled_date);
      invalidateSchedule();
    },
  });
  const deleteMutation = useMutation({
    mutationFn: (itemId: number) => deleteScheduleItem(itemId),
    onSuccess: () => {
      clearSelection();
      invalidateSchedule();
    },
  });
  const completeMutation = useMutation({
    mutationFn: completeScheduleOccurrence,
    onSuccess: invalidateSchedule,
  });
  const skipMutation = useMutation({
    mutationFn: skipScheduleOccurrence,
    onSuccess: invalidateSchedule,
  });
  const postponeMutation = useMutation({
    mutationFn: ({ occurrenceId, payload }: { occurrenceId: number; payload: { scheduled_date: string; scheduled_time: string | null } }) =>
      postponeScheduleOccurrence(occurrenceId, payload),
    onSuccess: (payload) => {
      setPostponeTarget(null);
      setPostponeError("");
      selectItem(payload.item.id, payload.new_occurrence.id);
      setSelectedDate(payload.new_occurrence.scheduled_date);
      invalidateSchedule();
    },
    onError: (error) => {
      setPostponeError(mutationError(error) || "延期失败");
    },
  });

  useEffect(() => {
    if (postponeTarget) {
      setPostponeDate(postponeTarget.current_occurrence.scheduled_date);
      setPostponeTime(postponeTarget.current_occurrence.scheduled_time || "");
      setPostponeError("");
    }
  }, [postponeTarget]);

  const selectedDetail = detailQuery.data;
  const day = dayQuery.data;
  const occurrences = day?.occurrences || [];
  const total = day?.total || 0;
  const done = day?.status_counts.done || 0;
  const pending = (day?.status_counts.pending || 0) + (day?.status_counts.overdue || 0);
  const completionRate = day?.completion_rate || 0;
  const progressStyle = { "--schedule-progress": `${Math.round(completionRate * 360)}deg` } as CSSProperties;
  const title = isToday(selectedDate) ? "今日任务" : `${formatReadableDate(selectedDate)}任务`;
  const typeLabel = typeOptions.find((option) => option.value === itemTypeFilter)?.label || "";
  const statusLabel = statusOptions.find((option) => option.value === statusFilter)?.label || "";
  const activeFilterCount = (itemTypeFilter ? 1 : 0) + (statusFilter ? 1 : 0);
  const detailError = mutationError(detailQuery.error);
  const actionError =
    mutationError(createMutation.error) ||
    mutationError(updateMutation.error) ||
    mutationError(deleteMutation.error) ||
    mutationError(completeMutation.error) ||
    mutationError(skipMutation.error);

  function chooseDate(value: string) {
    setSelectedDate(value);
    const month = formatMonthKey(parseLocalDate(value));
    if (month !== selectedMonth) {
      setSelectedMonth(month);
    }
  }

  function submitPostpone() {
    if (!postponeTarget) {
      return;
    }
    if (!postponeDate) {
      setPostponeError("请选择新的日期。");
      return;
    }
    postponeMutation.mutate({
      occurrenceId: postponeTarget.current_occurrence.id,
      payload: {
        scheduled_date: postponeDate,
        scheduled_time: postponeTime || null,
      },
    });
  }

  function confirmDelete(itemId: number) {
    if (window.confirm("确认删除这个任务吗？删除后不会出现在日列表和月历中。")) {
      deleteMutation.mutate(itemId);
    }
  }

  function resetFilters() {
    setItemTypeFilter("");
    setStatusFilter("");
  }

  return (
    <div className="schedule-workspace">
      <section className="schedule-main">
        <div className="schedule-hero">
          <div>
            <p className="eyebrow">Selected Day</p>
            <h2>{title}</h2>
            <p>{selectedDate} · 完成 {done} / {total} · 待处理 {pending}</p>
          </div>
          <div className="schedule-hero-actions">
            <CharacterSelector />
            <div className="schedule-filter-inline">
              <Dialog.Root open={filterOpen} onOpenChange={setFilterOpen}>
                <Dialog.Trigger asChild>
                  <Button variant="secondary" type="button">
                    <SlidersHorizontal size={16} />
                    筛选{activeFilterCount ? ` ${activeFilterCount}` : ""}
                  </Button>
                </Dialog.Trigger>
                <Dialog.Portal>
                  <Dialog.Overlay className="fixed inset-0 z-30 bg-black/10" />
                  <Dialog.Content className="schedule-filter-dialog">
                    <Dialog.Title className="text-lg font-black">筛选</Dialog.Title>
                    <div className="schedule-filter-panel">
                      <section>
                        <h3>任务类型</h3>
                        <div className="schedule-filter-options">
                          {typeOptions.map((option) => (
                            <button
                              className={itemTypeFilter === option.value ? "active" : ""}
                              type="button"
                              key={option.label}
                              onClick={() => setItemTypeFilter(option.value)}
                            >
                              {option.label}
                            </button>
                          ))}
                        </div>
                      </section>
                      <section>
                        <h3>任务状态</h3>
                        <div className="schedule-filter-options">
                          {statusOptions.map((option) => (
                            <button
                              className={statusFilter === option.value ? "active" : ""}
                              type="button"
                              key={option.label}
                              onClick={() => setStatusFilter(option.value)}
                            >
                              {option.label}
                            </button>
                          ))}
                        </div>
                      </section>
                    </div>
                    <div className="schedule-form-actions">
                      <Button variant="ghost" type="button" onClick={resetFilters}>重置</Button>
                      <Dialog.Close asChild>
                        <Button variant="primary" type="button">完成</Button>
                      </Dialog.Close>
                    </div>
                  </Dialog.Content>
                </Dialog.Portal>
              </Dialog.Root>
              {itemTypeFilter ? (
                <button className="schedule-filter-chip" type="button" onClick={() => setItemTypeFilter("")}>
                  {typeLabel}
                  <X size={13} />
                </button>
              ) : null}
              {statusFilter ? (
                <button className="schedule-filter-chip" type="button" onClick={() => setStatusFilter("")}>
                  {statusLabel}
                  <X size={13} />
                </button>
              ) : null}
            </div>
            <div className="schedule-progress-ring" style={progressStyle}>
              <strong>{Math.round(completionRate * 100)}%</strong>
              <span>完成率</span>
            </div>
          </div>
        </div>

        <div className="today-task-shell">
          <div className="today-task-header">
            <h3>任务列表</h3>
            <Button variant="primary" type="button" onClick={openCreate}>
              <Plus size={16} />
              新建任务
            </Button>
          </div>
          {dayQuery.error instanceof Error ? (
            <div className="inline-error">
              <span>{dayQuery.error.message}</span>
              <Button className="ml-auto h-8 min-h-8 px-3" variant="ghost" type="button" onClick={() => void dayQuery.refetch()}>
                重试
              </Button>
            </div>
          ) : dayQuery.isLoading ? (
            <div className="paper-empty">正在读取这一天的任务...</div>
          ) : occurrences.length ? (
            <div className="schedule-task-list">
              {occurrences.map((item) => (
                <article
                  className={`schedule-task-card ${selectedItemId === item.id ? "active" : ""} ${item.current_occurrence.status}`}
                  key={`${item.id}-${item.current_occurrence.id}`}
                >
                  <button type="button" onClick={() => selectItem(item.id, item.current_occurrence.id)}>
                    <div className="schedule-task-head">
                      <strong>{item.title}</strong>
                      <span className={`schedule-status ${item.current_occurrence.status}`}>
                        {scheduleStatusLabels[item.current_occurrence.status]}
                      </span>
                    </div>
                    <p>{item.note || "没有备注"}</p>
                    <div className="schedule-task-meta">
                      <span>{scheduleTypeLabels[item.item_type]}</span>
                      <span>{schedulePriorityLabels[item.priority]}</span>
                      <span>{item.current_occurrence.scheduled_time || "全天"}</span>
                      {item.estimated_minutes ? <span>{item.estimated_minutes} 分钟</span> : null}
                      <span>{item.current_occurrence.scheduled_date}</span>
                    </div>
                    <div className="schedule-tag-preview">
                      {item.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}
                      {item.tags.length > 4 ? <span>+{item.tags.length - 4}</span> : null}
                    </div>
                  </button>
                  {activeStatus(item.current_occurrence.status) ? (
                    <div className="schedule-action-row">
                      <button type="button" onClick={() => completeMutation.mutate(item.current_occurrence.id)}>
                        <Check size={15} />
                        完成
                      </button>
                      <button type="button" onClick={() => setPostponeTarget(item)}>
                        <Clock3 size={15} />
                        延期
                      </button>
                      <button type="button" onClick={() => skipMutation.mutate(item.current_occurrence.id)}>
                        <FastForward size={15} />
                        跳过
                      </button>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div className="schedule-empty-block">
              <EmptyState
                icon={<CalendarDays size={24} />}
                title="这一天还没有任务"
                description="新建一个任务开始安排。"
              />
              <Button variant="primary" type="button" onClick={openCreate}>
                <Plus size={16} />
                新建任务
              </Button>
            </div>
          )}
          {actionError ? <div className="inline-error"><span>{actionError}</span></div> : null}
        </div>

        <div className="schedule-calendar-shell">
          <MonthCalendar
            month={selectedMonth}
            selectedDate={selectedDate}
            days={calendarQuery.data?.days || []}
            isLoading={calendarQuery.isLoading}
            error={calendarQuery.error instanceof Error ? calendarQuery.error.message : ""}
            onMonthChange={setSelectedMonth}
            onDateSelect={chooseDate}
            onRetry={() => void calendarQuery.refetch()}
          />
        </div>
      </section>

      <aside className="schedule-detail-panel">
        <div className="page-kicker">
          <span>Task</span>
          <strong>任务详情</strong>
        </div>

        {editorMode === "create" ? (
          <ScheduleTaskForm
            mode="create"
            selectedDate={selectedDate}
            isPending={createMutation.isPending}
            error={mutationError(createMutation.error)}
            onSubmit={(payload) => createMutation.mutate(payload)}
            onCancel={closeEditor}
          />
        ) : editorMode === "edit" && selectedDetail ? (
          <ScheduleTaskForm
            mode="edit"
            selectedDate={selectedDate}
            item={selectedDetail}
            isPending={updateMutation.isPending}
            error={mutationError(updateMutation.error)}
            onSubmit={(payload) => updateMutation.mutate(payload)}
            onCancel={() => selectItem(selectedDetail.id, selectedDetail.current_occurrence.id)}
          />
        ) : selectedItemId ? (
          detailQuery.isLoading ? (
            <div className="paper-empty">正在读取任务详情...</div>
          ) : detailError ? (
            <div className="inline-error"><span>{detailError}</span></div>
          ) : selectedDetail ? (
            <div className="schedule-detail-card">
              <h3>{selectedDetail.title}</h3>
              <p>{selectedDetail.note || "没有备注"}</p>
              <div className="schedule-task-meta">
                <span>{scheduleTypeLabels[selectedDetail.item_type]}</span>
                <span>{schedulePriorityLabels[selectedDetail.priority]}</span>
                <span>{scheduleStatusLabels[selectedDetail.current_occurrence.status]}</span>
                <span>{selectedDetail.current_occurrence.scheduled_date}</span>
                <span>{selectedDetail.current_occurrence.scheduled_time || "全天"}</span>
              </div>
              <div className="schedule-tag-preview">
                {selectedDetail.tags.map((tag) => <span key={tag}>{tag}</span>)}
              </div>
              <div className="schedule-detail-actions">
                {activeStatus(selectedDetail.current_occurrence.status) ? (
                  <Button variant="secondary" type="button" onClick={openEdit}>
                    <Edit3 size={16} />
                    编辑
                  </Button>
                ) : null}
                <Button variant="danger" type="button" onClick={() => confirmDelete(selectedDetail.id)}>
                  <Trash2 size={16} />
                  删除
                </Button>
              </div>
              {activeStatus(selectedDetail.current_occurrence.status) ? (
                <div className="schedule-action-row">
                  <button type="button" onClick={() => completeMutation.mutate(selectedDetail.current_occurrence.id)}>
                    <Check size={15} />
                    完成
                  </button>
                  <button type="button" onClick={() => setPostponeTarget(selectedDetail)}>
                    <Clock3 size={15} />
                    延期
                  </button>
                  <button type="button" onClick={() => skipMutation.mutate(selectedDetail.current_occurrence.id)}>
                    <FastForward size={15} />
                    跳过
                  </button>
                </div>
              ) : null}
            </div>
          ) : null
        ) : (
          <div className="schedule-empty-block">
            <EmptyState
              title="未选择任务"
              description="选择任务列表中的任务，或新建一个任务。"
            />
            <Button variant="primary" type="button" onClick={openCreate}>
              <Plus size={16} />
              新建任务
            </Button>
          </div>
        )}
      </aside>

      <Dialog.Root open={Boolean(postponeTarget)} onOpenChange={(open) => !open && setPostponeTarget(null)}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm" />
          <Dialog.Content className="schedule-dialog">
            <Dialog.Title className="text-xl font-black">延期任务</Dialog.Title>
            <Dialog.Description className="mt-2 text-sm leading-6 text-[var(--muted)]">
              旧任务实例会保留为已延期，并创建新的待处理实例。
            </Dialog.Description>
            <div className="mt-5 grid gap-3">
              <TextField label="新日期" type="date" value={postponeDate} onChange={(event) => setPostponeDate(event.target.value)} />
              <TextField label="新时间" type="time" value={postponeTime} onChange={(event) => setPostponeTime(event.target.value)} />
              {postponeError ? <div className="inline-error"><span>{postponeError}</span></div> : null}
              <div className="schedule-form-actions">
                <Button variant="ghost" type="button" onClick={() => setPostponeTarget(null)}>取消</Button>
                <Button disabled={postponeMutation.isPending} variant="primary" type="button" onClick={submitPostpone}>
                  确认延期
                </Button>
              </div>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
