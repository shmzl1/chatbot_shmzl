import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  Check,
  ChevronDown,
  History,
  MessageSquareWarning,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  applyPersonaReview,
  chatPersonaReview,
  finalizePersonaReview,
  getCharacterDetail,
  getPersonaFeedbackSummary,
  rollbackPersonaReview,
  savePersonaTurnFeedback,
} from "../../api/personaReviewApi";
import type {
  CharacterDetail,
  PersonaReviewFinalizeResponse,
  PersonaReviewHistoryMessage,
  PersonaReviewSelectedTurn,
  PersonaReviewTurn,
} from "../../types/personaReview";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";

type ReviewStep = "select" | "feedback" | "discuss" | "preview" | "applied";
type ConfirmAction = "apply" | "rollback" | null;

interface PersonaReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  characterId: string | null;
  characterName: string;
  sessionId: string | null;
  turns: PersonaReviewTurn[];
  onPersonaChanged?: () => void;
}

const MAX_SELECTED_TURNS = 5;
const COMMENT_LIMIT = 2000;
const PREVIEW_FIELDS = [
  "style_contract",
  "speaking_style",
  "forbidden",
  "dialogues",
  "reactions",
  "bad_examples",
  "evaluation_criteria",
  "revision_notes",
];
const PROTECTED_FIELDS = [
  "id",
  "display_name",
  "avatar_url",
  "voice",
  "gptsovits_base_url",
  "ref_audio_path",
  "prompt_text",
];
const ISSUE_TAGS = [
  { value: "out_of_character", label: "不符合人设" },
  { value: "too_ai", label: "表达太像 AI" },
  { value: "wrong_tone", label: "语气不对" },
  { value: "too_cold", label: "过于冷淡" },
  { value: "too_warm", label: "过于热情" },
  { value: "too_verbose", label: "回复太长" },
  { value: "too_short", label: "回复太短" },
  { value: "relationship_mismatch", label: "关系感不对" },
  { value: "repetitive", label: "重复表达" },
  { value: "violates_forbidden", label: "违反禁忌" },
  { value: "other", label: "其他" },
];

function safeErrorMessage(error: unknown, fallback: string) {
  const raw = error instanceof Error ? error.message : "";
  if (!raw) {
    return fallback;
  }
  const compact = raw.replace(/Traceback[\s\S]*/i, "后端返回了异常详情，请查看后端日志。").replace(/[A-Za-z]:\\[^\s"'<>]+/g, "[本地路径]");
  return compact.length > 480 ? `${compact.slice(0, 480)}...` : compact;
}

function valueText(value: unknown) {
  if (value === undefined) {
    return "未设置";
  }
  if (typeof value === "string") {
    return value || "空";
  }
  return JSON.stringify(value, null, 2);
}

function sameValue(left: unknown, right: unknown) {
  return JSON.stringify(left ?? null) === JSON.stringify(right ?? null);
}

function summarizePatch(patch: Record<string, unknown>) {
  return Object.entries(patch)
    .filter(([, value]) => {
      if (Array.isArray(value)) {
        return value.length > 0;
      }
      return value !== null && value !== undefined;
    })
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}: 新增 ${value.length} 条`;
      }
      return `${key}: 已生成`;
    });
}

function changedPreviewFields(current: CharacterDetail | undefined, finalReview: PersonaReviewFinalizeResponse | null) {
  if (!current || !finalReview) {
    return finalReview?.changed_fields || [];
  }
  const fields = new Set(finalReview.changed_fields);
  PREVIEW_FIELDS.forEach((field) => {
    if (!sameValue(current[field], finalReview.preview_character_json[field])) {
      fields.add(field);
    }
  });
  return Array.from(fields).filter((field) => PREVIEW_FIELDS.includes(field));
}

function protectedChanges(current: CharacterDetail | undefined, preview: Record<string, unknown> | undefined) {
  if (!current || !preview) {
    return [];
  }
  return PROTECTED_FIELDS.filter((field) => field in preview && !sameValue(current[field], preview[field]));
}

function numericTurnId(value: string | number | null | undefined) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export function PersonaReviewDialog({
  open,
  onOpenChange,
  characterId,
  characterName,
  sessionId,
  turns,
  onPersonaChanged,
}: PersonaReviewDialogProps) {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<ReviewStep>("select");
  const [selectedTurnIds, setSelectedTurnIds] = useState<number[]>([]);
  const [expandedTurnIds, setExpandedTurnIds] = useState<number[]>([]);
  const [issueTags, setIssueTags] = useState<string[]>([]);
  const [comment, setComment] = useState("");
  const [editorMessage, setEditorMessage] = useState("");
  const [editorHistory, setEditorHistory] = useState<PersonaReviewHistoryMessage[]>([]);
  const [finalReview, setFinalReview] = useState<PersonaReviewFinalizeResponse | null>(null);
  const [localError, setLocalError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);

  const selectedTurns = useMemo(
    () => turns.filter((turn) => selectedTurnIds.includes(turn.id)),
    [selectedTurnIds, turns],
  );
  const selectedPayload: PersonaReviewSelectedTurn[] = selectedTurns.map((turn) => ({
    turn_id: turn.turn_id,
    session_id: turn.session_id,
    user_message: turn.user_message,
    assistant_message: turn.assistant_message,
    emotion: turn.emotion,
  }));

  const characterQuery = useQuery({
    queryKey: ["character", characterId],
    queryFn: () => getCharacterDetail(characterId!),
    enabled: open && Boolean(characterId),
    retry: 0,
  });
  const feedbackQuery = useQuery({
    queryKey: ["persona-feedback", characterId],
    queryFn: () => getPersonaFeedbackSummary(characterId!, 30),
    enabled: open && Boolean(characterId),
    retry: 0,
  });

  const protectedChanged = protectedChanges(characterQuery.data, finalReview?.preview_character_json);
  const previewFields = changedPreviewFields(characterQuery.data, finalReview);
  const patchSummary = finalReview ? summarizePatch(finalReview.patch) : [];

  useEffect(() => {
    if (!open) {
      setStep("select");
      setSelectedTurnIds([]);
      setExpandedTurnIds([]);
      setIssueTags([]);
      setComment("");
      setEditorMessage("");
      setEditorHistory([]);
      setFinalReview(null);
      setLocalError("");
      setNotice("");
      setConfirmAction(null);
    }
  }, [open]);

  const saveFeedbackMutation = useMutation({
    mutationFn: async () => {
      if (!characterId) {
        throw new Error("缺少角色，无法保存人设反馈。");
      }
      if (!selectedTurns.length) {
        throw new Error("请先选择至少一轮对话。");
      }
      if (!issueTags.length && !comment.trim()) {
        throw new Error("请至少选择一个问题标签，或填写具体说明。");
      }
      await Promise.all(
        selectedTurns.map((turn) =>
          savePersonaTurnFeedback({
            character_id: characterId,
            session_id: String(turn.session_id || sessionId || ""),
            turn_id: numericTurnId(turn.turn_id),
            user_message: turn.user_message,
            assistant_message: turn.assistant_message,
            rating: "bad",
            issue_tags: issueTags,
            comment: comment.trim(),
          }),
        ),
      );
    },
    onSuccess: () => {
      setLocalError("");
      setNotice("反馈已保存，可以继续和人设编辑讨论。");
      setStep("discuss");
      void feedbackQuery.refetch();
    },
    onError: (error) => setLocalError(safeErrorMessage(error, "反馈保存失败")),
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!characterId) {
        throw new Error("缺少角色，无法联系人设编辑。");
      }
      return chatPersonaReview(characterId, {
        selected_turns: selectedPayload,
        message,
        history: editorHistory,
      });
    },
    onSuccess: (payload) => {
      setLocalError("");
      setEditorHistory(payload.history);
      setEditorMessage("");
      if (payload.should_generate_final) {
        setNotice("信息已经足够，可以生成修改方案。");
      }
    },
    onError: (error) => setLocalError(safeErrorMessage(error, "人设编辑讨论失败")),
  });

  const finalizeMutation = useMutation({
    mutationFn: async () => {
      if (!characterId) {
        throw new Error("缺少角色，无法生成修改方案。");
      }
      if (!selectedPayload.length || !editorHistory.length) {
        throw new Error("请先选择对话，并至少完成一轮人设编辑讨论。");
      }
      return finalizePersonaReview(characterId, {
        selected_turns: selectedPayload,
        history: editorHistory,
        limit: 20,
      });
    },
    onSuccess: (payload) => {
      setLocalError("");
      setFinalReview(payload);
      setStep("preview");
      void characterQuery.refetch();
    },
    onError: (error) => {
      setFinalReview(null);
      setLocalError(safeErrorMessage(error, "生成修改方案失败"));
    },
  });

  const applyMutation = useMutation({
    mutationFn: async () => {
      if (!characterId || !finalReview) {
        throw new Error("没有可应用的修改方案。");
      }
      if (protectedChanged.length) {
        throw new Error(`预览包含受保护字段变化，已阻止应用：${protectedChanged.join(", ")}`);
      }
      return applyPersonaReview(characterId, {
        preview_character_json: finalReview.preview_character_json,
        review_summary: {
          main_issues: finalReview.main_issues,
          revision_plan: finalReview.revision_plan,
          risk_notes: finalReview.risk_notes,
          changed_fields: finalReview.changed_fields,
          selected_turn_count: selectedTurns.length,
        },
      });
    },
    onSuccess: (payload) => {
      setConfirmAction(null);
      setLocalError("");
      setNotice(`已应用修改：${payload.changed_fields.join("、") || "已更新"}`);
      setStep("applied");
      void queryClient.invalidateQueries({ queryKey: ["characters"] });
      void queryClient.invalidateQueries({ queryKey: ["character", characterId] });
      onPersonaChanged?.();
    },
    onError: (error) => setLocalError(safeErrorMessage(error, "应用修改失败")),
  });

  const rollbackMutation = useMutation({
    mutationFn: async () => {
      if (!characterId) {
        throw new Error("缺少角色，无法回滚。");
      }
      return rollbackPersonaReview(characterId);
    },
    onSuccess: () => {
      setConfirmAction(null);
      setLocalError("");
      setNotice("已回滚最近一次人设修改。");
      void queryClient.invalidateQueries({ queryKey: ["characters"] });
      void queryClient.invalidateQueries({ queryKey: ["character", characterId] });
      onPersonaChanged?.();
    },
    onError: (error) => setLocalError(safeErrorMessage(error, "回滚失败")),
  });

  function toggleTurn(turnId: number) {
    setLocalError("");
    setSelectedTurnIds((current) => {
      if (current.includes(turnId)) {
        return current.filter((id) => id !== turnId);
      }
      if (current.length >= MAX_SELECTED_TURNS) {
        setLocalError(`最多选择 ${MAX_SELECTED_TURNS} 轮对话。`);
        return current;
      }
      return [...current, turnId];
    });
  }

  function toggleExpanded(turnId: number) {
    setExpandedTurnIds((current) => (
      current.includes(turnId) ? current.filter((id) => id !== turnId) : [...current, turnId]
    ));
  }

  function toggleIssueTag(tag: string) {
    setIssueTags((current) => (current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]));
  }

  function goFeedback() {
    if (!selectedTurns.length) {
      setLocalError("请先选择至少一轮对话。");
      return;
    }
    setLocalError("");
    setStep("feedback");
  }

  function saveFeedback() {
    if (!issueTags.length && !comment.trim()) {
      setLocalError("请至少选择一个问题标签，或填写具体说明。");
      return;
    }
    saveFeedbackMutation.mutate();
  }

  function sendEditorMessage() {
    const cleaned = editorMessage.trim();
    if (!cleaned) {
      setLocalError("请填写要和人设编辑讨论的内容。");
      return;
    }
    chatMutation.mutate(cleaned);
  }

  function applyConfirmedAction() {
    if (confirmAction === "apply") {
      applyMutation.mutate();
    }
    if (confirmAction === "rollback") {
      rollbackMutation.mutate();
    }
  }

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="persona-review-overlay" />
        <Dialog.Content className="persona-review-dialog">
          <div className="persona-review-header">
            <div>
              <Dialog.Title>人设修正工作台</Dialog.Title>
              <p>正在修正：{characterName || "未选择角色"}</p>
            </div>
            <div className="persona-review-header-actions">
              <Button variant="ghost" type="button" disabled={!characterId || rollbackMutation.isPending} onClick={() => setConfirmAction("rollback")}>
                <History size={15} />
                回滚上次修改
              </Button>
              <Dialog.Close asChild>
                <button type="button" className="persona-review-close" aria-label="关闭人设修正">
                  <X size={18} />
                </button>
              </Dialog.Close>
            </div>
          </div>

          <div className="persona-review-steps">
            {["select", "feedback", "discuss", "preview", "applied"].map((item) => (
              <span className={step === item ? "active" : ""} key={item}>
                {item === "select" ? "选择片段" : item === "feedback" ? "保存反馈" : item === "discuss" ? "编辑讨论" : item === "preview" ? "方案预览" : "完成"}
              </span>
            ))}
          </div>

          {localError ? (
            <div className="persona-review-error">
              <AlertTriangle size={16} />
              <span>{localError}</span>
            </div>
          ) : null}
          {notice ? (
            <div className="persona-review-notice">
              <Check size={16} />
              <span>{notice}</span>
            </div>
          ) : null}

          <div className="persona-review-body">
            {step === "select" ? (
              <section className="persona-review-panel">
                <div className="persona-review-panel-head">
                  <div>
                    <h3>选择需要修正的对话片段</h3>
                    <p>只选择完整的一轮用户消息和角色回复，最多 {MAX_SELECTED_TURNS} 轮。</p>
                  </div>
                  <span>{selectedTurns.length} / {MAX_SELECTED_TURNS}</span>
                </div>
                {!sessionId ? (
                  <EmptyState icon={<MessageSquareWarning size={24} />} title="还没有可修正的会话" description="产生至少一轮真实聊天后才能保存人设反馈。" />
                ) : turns.length ? (
                  <div className="persona-turn-list">
                    {turns.map((turn) => {
                      const selected = selectedTurnIds.includes(turn.id);
                      const expanded = expandedTurnIds.includes(turn.id);
                      return (
                        <article className={`persona-turn-card ${selected ? "selected" : ""}`} key={turn.id}>
                          <label>
                            <input type="checkbox" checked={selected} onChange={() => toggleTurn(turn.id)} />
                            <span>第 {turn.id} 轮</span>
                          </label>
                          <div className={`persona-turn-text ${expanded ? "expanded" : ""}`}>
                            <strong>用户：</strong>
                            <p>{turn.user_message}</p>
                            <strong>角色：</strong>
                            <p>{turn.assistant_message}</p>
                          </div>
                          <button type="button" onClick={() => toggleExpanded(turn.id)}>
                            {expanded ? "收起" : "展开"}
                            <ChevronDown size={14} />
                          </button>
                        </article>
                      );
                    })}
                  </div>
                ) : (
                  <EmptyState icon={<MessageSquareWarning size={24} />} title="当前会话没有角色回复" description="空对话不能进入人设修正。" />
                )}
              </section>
            ) : null}

            {step === "feedback" ? (
              <section className="persona-review-panel">
                <div className="persona-review-panel-head">
                  <div>
                    <h3>标记回复问题</h3>
                    <p>至少选择一个标签，或填写具体说明。反馈会保存到正式 persona feedback。</p>
                  </div>
                </div>
                <div className="persona-issue-tags">
                  {ISSUE_TAGS.map((tag) => (
                    <button className={issueTags.includes(tag.value) ? "active" : ""} key={tag.value} type="button" onClick={() => toggleIssueTag(tag.value)}>
                      {tag.label}
                    </button>
                  ))}
                </div>
                <label className="persona-review-textarea">
                  <span>具体说明</span>
                  <textarea
                    maxLength={COMMENT_LIMIT}
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    placeholder="例如：这里太像工具说明，缺少角色平时的别扭和嘴硬。"
                  />
                  <small>{comment.length} / {COMMENT_LIMIT}</small>
                </label>
              </section>
            ) : null}

            {step === "discuss" ? (
              <section className="persona-review-panel persona-discuss-grid">
                <div className="persona-editor-chat">
                  <div className="persona-review-panel-head">
                    <div>
                      <h3>人设编辑</h3>
                      <p>这里是人设编辑 AI，不是聊天角色本人；讨论不会写入普通聊天历史。</p>
                    </div>
                    {feedbackQuery.data ? <span>反馈 {feedbackQuery.data.total_feedback} 条</span> : null}
                  </div>
                  <div className="persona-editor-history">
                    {editorHistory.length ? (
                      editorHistory.map((message, index) => (
                        <article className={message.role} key={`${message.role}-${index}`}>
                          <strong>{message.role === "user" ? "你" : "人设编辑"}</strong>
                          <p>{message.content}</p>
                        </article>
                      ))
                    ) : (
                      <EmptyState icon={<Bot size={24} />} title="开始讨论修改方向" description="说明哪些表达不对、希望如何调整、是否只做轻微修正。" />
                    )}
                  </div>
                  <label className="persona-review-textarea compact">
                    <span>给人设编辑的说明</span>
                    <textarea
                      value={editorMessage}
                      onChange={(event) => setEditorMessage(event.target.value)}
                      maxLength={4000}
                      placeholder="例如：请重点修正这种回复太 AI 的问题，少量增加坏例子和评价标准。"
                    />
                  </label>
                </div>
                <aside className="persona-selected-summary">
                  <h4>已选片段</h4>
                  {selectedTurns.map((turn) => (
                    <p key={turn.id}>{turn.user_message.slice(0, 72)}{turn.user_message.length > 72 ? "..." : ""}</p>
                  ))}
                  {chatMutation.data?.suggested_tags?.length ? (
                    <>
                      <h4>建议标签</h4>
                      <div className="persona-suggested-tags">
                        {chatMutation.data.suggested_tags.map((tag) => <span key={tag}>{tag}</span>)}
                      </div>
                    </>
                  ) : null}
                </aside>
              </section>
            ) : null}

            {step === "preview" && finalReview ? (
              <section className="persona-review-panel persona-preview">
                <div className="persona-review-panel-head">
                  <div>
                    <h3>最终修改方案</h3>
                    <p>生成预览不会写入角色文件，必须确认应用后才生效。</p>
                  </div>
                  {finalReview.model ? <span>技术详情可展开查看</span> : null}
                </div>
                {protectedChanged.length ? (
                  <div className="persona-review-error">
                    <ShieldAlert size={16} />
                    <span>预览包含受保护字段变化，已阻止应用：{protectedChanged.join("、")}</span>
                  </div>
                ) : null}
                <div className="persona-preview-grid">
                  <PreviewList title="主要问题" items={finalReview.main_issues} />
                  <PreviewList title="修改计划" items={finalReview.revision_plan} />
                  <PreviewList title="风险提示" items={finalReview.risk_notes} />
                  <PreviewList title="patch 摘要" items={patchSummary.length ? patchSummary : ["没有可展示的 patch 摘要"]} />
                </div>
                <div className="persona-diff-list">
                  <h4>字段差异</h4>
                  {characterQuery.error instanceof Error ? (
                    <div className="persona-review-error"><AlertTriangle size={16} /><span>{safeErrorMessage(characterQuery.error, "角色详情加载失败")}</span></div>
                  ) : characterQuery.isLoading ? (
                    <div className="paper-empty">正在读取当前角色...</div>
                  ) : previewFields.length ? (
                    previewFields.map((field) => (
                      <details className="persona-diff-field" key={field} open>
                        <summary>{field}</summary>
                        <div>
                          <section>
                            <strong>当前</strong>
                            <pre>{valueText(characterQuery.data?.[field])}</pre>
                          </section>
                          <section>
                            <strong>修改后</strong>
                            <pre>{valueText(finalReview.preview_character_json[field])}</pre>
                          </section>
                        </div>
                      </details>
                    ))
                  ) : (
                    <div className="paper-empty">没有检测到可变字段变化。</div>
                  )}
                </div>
                <details className="persona-tech-details">
                  <summary>查看完整预览 JSON 和模型信息</summary>
                  <p>profile: {finalReview.llm_profile || "persona_editor"} / model: {finalReview.model || "未返回"}</p>
                  <pre>{JSON.stringify(finalReview.preview_character_json, null, 2)}</pre>
                </details>
              </section>
            ) : null}

            {step === "applied" ? (
              <section className="persona-review-panel">
                <EmptyState icon={<Sparkles size={24} />} title="人设修改已应用" description="修改只影响该角色之后的新回复，历史聊天不会改变。" />
              </section>
            ) : null}
          </div>

          <div className="persona-review-footer">
            <div>
              {step !== "select" && step !== "applied" ? (
                <Button variant="ghost" type="button" onClick={() => setStep(step === "preview" ? "discuss" : step === "discuss" ? "feedback" : "select")}>
                  返回
                </Button>
              ) : null}
            </div>
            <div>
              {step === "select" ? (
                <Button variant="primary" type="button" disabled={!selectedTurns.length} onClick={goFeedback}>
                  下一步
                </Button>
              ) : null}
              {step === "feedback" ? (
                <Button variant="primary" type="button" disabled={saveFeedbackMutation.isPending} onClick={saveFeedback}>
                  保存反馈并进入讨论
                </Button>
              ) : null}
              {step === "discuss" ? (
                <>
                  <Button variant="secondary" type="button" disabled={chatMutation.isPending} onClick={sendEditorMessage}>
                    <Bot size={16} />
                    发送给人设编辑
                  </Button>
                  <Button variant="primary" type="button" disabled={finalizeMutation.isPending || !editorHistory.length || !selectedTurns.length} onClick={() => finalizeMutation.mutate()}>
                    <Sparkles size={16} />
                    生成修改方案
                  </Button>
                </>
              ) : null}
              {step === "preview" ? (
                <Button variant="primary" type="button" disabled={!finalReview || protectedChanged.length > 0 || applyMutation.isPending} onClick={() => setConfirmAction("apply")}>
                  确认应用修改
                </Button>
              ) : null}
              {step === "applied" ? (
                <Dialog.Close asChild>
                  <Button variant="secondary" type="button">关闭</Button>
                </Dialog.Close>
              ) : null}
            </div>
          </div>

          {confirmAction ? (
            <div className="persona-confirm-layer">
              <div className="persona-confirm-card">
                <ShieldAlert size={24} />
                <h3>{confirmAction === "apply" ? "确认应用人设修改？" : "回滚最近一次人设修改？"}</h3>
                <p>
                  {confirmAction === "apply"
                    ? "修改会影响该角色之后的新回复，历史聊天不会改变。"
                    : "只会恢复该角色最近一次备份，不能选择任意历史版本。"}
                </p>
                <div>
                  <Button variant="ghost" type="button" onClick={() => setConfirmAction(null)}>取消</Button>
                  <Button
                    variant={confirmAction === "rollback" ? "danger" : "primary"}
                    type="button"
                    disabled={applyMutation.isPending || rollbackMutation.isPending}
                    onClick={applyConfirmedAction}
                  >
                    {confirmAction === "apply" ? "确认应用" : "确认回滚"}
                  </Button>
                </div>
              </div>
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function PreviewList({ title, items }: { title: string; items: unknown[] }) {
  return (
    <section>
      <h4>{title}</h4>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{typeof item === "string" ? item : JSON.stringify(item)}</li>
        ))}
      </ul>
    </section>
  );
}
