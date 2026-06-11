const state = {
  currentUser: null,
  currentCharacter: null,
  currentSessionId: null,
  currentTurnId: null,
  memorySuggestions: [],
  personaReview: null,
  personaEditorHistory: [],
  selectedPersonaTurns: [],
  characters: [],
  sessions: [],
};

const PERSONA_TAG_OPTIONS = [
  { label: "太 AI", tag: "too_ai" },
  { label: "不像角色", tag: "out_of_character" },
  { label: "太温柔", tag: "too_soft" },
  { label: "太冷淡", tag: "too_cold" },
  { label: "太刺人", tag: "too_harsh" },
  { label: "太啰嗦", tag: "too_verbose" },
  { label: "太客服", tag: "too_customer_service" },
  { label: "太像心理咨询", tag: "too_therapy_like" },
  { label: "缺少角色味", tag: "missing_character_flavor" },
  { label: "缺少别扭感", tag: "missing_awkwardness" },
  { label: "这句很好，保留", tag: "keep_style" },
  { label: "语气对了", tag: "right_tone" },
  { label: "可以作为样例", tag: "good_example" },
  { label: "更像原角色", tag: "closer_to_original" },
  { label: "更自然", tag: "more_natural" },
  { label: "更短一点", tag: "shorter" },
];

const elements = {
  activeSessionTitle: document.querySelector("#activeSessionTitle"),
  appStatusInfo: document.querySelector("#appStatusInfo"),
  candidateList: document.querySelector("#candidateList"),
  characterAvatarInput: document.querySelector("#characterAvatarInput"),
  characterJsonInput: document.querySelector("#characterJsonInput"),
  characterSelect: document.querySelector("#characterSelect"),
  chatForm: document.querySelector("#chatForm"),
  clearCurrentSessionButton: document.querySelector("#clearCurrentSessionButton"),
  clearKnowledgeButton: document.querySelector("#clearKnowledgeButton"),
  clearSessionsButton: document.querySelector("#clearSessionsButton"),
  closeSettingsButton: document.querySelector("#closeSettingsButton"),
  closePersonaEditorButton: document.querySelector("#closePersonaEditorButton"),
  currentCharacterAvatar: document.querySelector("#currentCharacterAvatar"),
  currentUserAvatar: document.querySelector("#currentUserAvatar"),
  currentUsername: document.querySelector("#currentUsername"),
  databaseInfo: document.querySelector("#databaseInfo"),
  deleteSessionButton: document.querySelector("#deleteSessionButton"),
  feedbackForm: document.querySelector("#feedbackForm"),
  feedbackNoteInput: document.querySelector("#feedbackNoteInput"),
  feedbackScoreInput: document.querySelector("#feedbackScoreInput"),
  importKnowledgeButton: document.querySelector("#importKnowledgeButton"),
  knowledgeContentInput: document.querySelector("#knowledgeContentInput"),
  knowledgeForm: document.querySelector("#knowledgeForm"),
  knowledgeList: document.querySelector("#knowledgeList"),
  knowledgeTagsInput: document.querySelector("#knowledgeTagsInput"),
  knowledgeTitleInput: document.querySelector("#knowledgeTitleInput"),
  knowledgeTypeSelect: document.querySelector("#knowledgeTypeSelect"),
  loadCharacterButton: document.querySelector("#loadCharacterButton"),
  memoryConfirmList: document.querySelector("#memoryConfirmList"),
  memoryForm: document.querySelector("#memoryForm"),
  memoryImportanceInput: document.querySelector("#memoryImportanceInput"),
  memoryInput: document.querySelector("#memoryInput"),
  memoryList: document.querySelector("#memoryList"),
  memorySuggestionList: document.querySelector("#memorySuggestionList"),
  memoryTagsInput: document.querySelector("#memoryTagsInput"),
  messageInput: document.querySelector("#messageInput"),
  messages: document.querySelector("#messages"),
  newSessionButton: document.querySelector("#newSessionButton"),
  openPersonaEditorButton: document.querySelector("#openPersonaEditorButton"),
  applyPersonaButton: document.querySelector("#applyPersonaButton"),
  clearPersonaEditorButton: document.querySelector("#clearPersonaEditorButton"),
  personaFeedbackStats: document.querySelector("#personaFeedbackStats"),
  personaEditorCharacterId: document.querySelector("#personaEditorCharacterId"),
  personaEditorCharacterName: document.querySelector("#personaEditorCharacterName"),
  personaEditorChat: document.querySelector("#personaEditorChat"),
  personaEditorInput: document.querySelector("#personaEditorInput"),
  personaEditorOverlay: document.querySelector("#personaEditorOverlay"),
  personaEditorSelectedCount: document.querySelector("#personaEditorSelectedCount"),
  personaReviewPreview: document.querySelector("#personaReviewPreview"),
  personaTagList: document.querySelector("#personaTagList"),
  promptToggle: document.querySelector("#promptToggle"),
  rawDebug: document.querySelector("#rawDebug"),
  refreshKnowledgeButton: document.querySelector("#refreshKnowledgeButton"),
  refreshMemoriesButton: document.querySelector("#refreshMemoriesButton"),
  refreshPersonaFeedbackButton: document.querySelector("#refreshPersonaFeedbackButton"),
  refreshSessionsButton: document.querySelector("#refreshSessionsButton"),
  retrievalList: document.querySelector("#retrievalList"),
  rollbackPersonaButton: document.querySelector("#rollbackPersonaButton"),
  saveCharacterButton: document.querySelector("#saveCharacterButton"),
  savePersonaFeedbackButton: document.querySelector("#savePersonaFeedbackButton"),
  selectedPersonaTurns: document.querySelector("#selectedPersonaTurns"),
  sendPersonaEditorButton: document.querySelector("#sendPersonaEditorButton"),
  sendButton: document.querySelector("#sendButton"),
  sessionList: document.querySelector("#sessionList"),
  settingsButton: document.querySelector("#settingsButton"),
  settingsCharacterSelect: document.querySelector("#settingsCharacterSelect"),
  settingsDebugToggle: document.querySelector("#settingsDebugToggle"),
  settingsOverlay: document.querySelector("#settingsOverlay"),
  settingsUserAvatar: document.querySelector("#settingsUserAvatar"),
  settingsUserAvatarInput: document.querySelector("#settingsUserAvatarInput"),
  settingsVoiceToggle: document.querySelector("#settingsVoiceToggle"),
  saveUserProfileButton: document.querySelector("#saveUserProfileButton"),
  statusText: document.querySelector("#statusText"),
  summarizePersonaButton: document.querySelector("#summarizePersonaButton"),
  userAvatarInput: document.querySelector("#userAvatarInput"),
  userProfileUsernameInput: document.querySelector("#userProfileUsernameInput"),
  voiceTestEmotionSelect: document.querySelector("#voiceTestEmotionSelect"),
  voiceTestForm: document.querySelector("#voiceTestForm"),
  voiceTestResult: document.querySelector("#voiceTestResult"),
  voiceTestTextInput: document.querySelector("#voiceTestTextInput"),
  voiceToggle: document.querySelector("#voiceToggle"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function authHeaders(headers = {}) {
  return headers;
}

async function requestJson(url, options = {}) {
  const body = options.body;
  const isFormData = body instanceof FormData;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...authHeaders(options.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || `${response.status} ${response.statusText} at ${url}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

function friendlyError(error) {
  const message = error?.message || String(error);
  const lowerMessage = message.toLowerCase();
  if (message.includes("PostgreSQL is not ready")) {
    return "数据库还没准备好。请确认 Docker Desktop 已启动，并在项目根目录运行 docker compose --project-directory . -f deploy/docker/docker-compose.yml up -d postgres adminer。";
  }
  if (message.includes("Missing reference audio")) {
    return "还没有放入语音参考音频。可先关闭语音开关继续文字聊天。";
  }
  if (message.includes("GPT-SoVITS")) {
    return "语音服务暂时不可用。可先关闭语音开关继续文字聊天。";
  }
  if (
    message.includes("LLM request failed") &&
    (lowerMessage.includes("response_format") ||
      lowerMessage.includes("json_object") ||
      lowerMessage.includes("unsupported") ||
      lowerMessage.includes("badrequest"))
  ) {
    return `AI 接口调用失败：当前模型可能不支持 JSON mode / response_format。后端详情：${message}`;
  }
  if (message.includes("LLM request failed")) {
    return "AI 接口调用失败。请检查 API Key、模型名或网络连接。";
  }
  return message;
}

function setAuthenticated(authenticated) {
  document.body.classList.toggle("authenticated", authenticated);
  document.body.classList.toggle("unauthenticated", !authenticated);
}

function setStatus(text) {
  elements.statusText.textContent = text;
}

function setDebugMode(enabled) {
  document.body.classList.toggle("debug-mode", enabled);
  document.body.classList.toggle("user-mode", !enabled);
  elements.settingsDebugToggle.checked = enabled;
  window.localStorage.setItem("roleChatbotDebugMode", enabled ? "1" : "0");
}

function setSettingsOpen(open) {
  elements.settingsOverlay.classList.toggle("open", open);
  elements.settingsOverlay.setAttribute("aria-hidden", open ? "false" : "true");
  if (open) {
    loadAppStatus();
  }
}

function setPersonaEditorOpen(open) {
  elements.personaEditorOverlay.classList.toggle("open", open);
  elements.personaEditorOverlay.setAttribute("aria-hidden", open ? "false" : "true");
  if (open) {
    updatePersonaEditorHeader();
    renderSelectedPersonaTurns();
    renderPersonaEditorChat();
    loadPersonaFeedbackStats().catch((error) => {
      elements.personaFeedbackStats.innerHTML = `<div class="error-box">${escapeHtml(friendlyError(error))}</div>`;
    });
  }
}

function setVoiceEnabled(enabled) {
  elements.voiceToggle.checked = enabled;
  elements.settingsVoiceToggle.checked = enabled;
  window.localStorage.setItem("roleChatbotVoice", enabled ? "1" : "0");
}

function getCharacterId() {
  return elements.settingsCharacterSelect.value || elements.characterSelect.value || "role01";
}

function setCharacterId(characterId) {
  elements.characterSelect.value = characterId;
  elements.settingsCharacterSelect.value = characterId;
  updatePersonaEditorHeader();
}

function firstText(text, fallback) {
  const value = String(text || "").trim();
  return value ? value.slice(0, 1).toUpperCase() : fallback;
}

function avatarMarkup(url, label, fallback, size = "") {
  const safeSize = size ? ` ${size}` : "";
  if (url) {
    return `<img class="avatar${safeSize}" src="${escapeHtml(url)}" alt="${escapeHtml(label || "avatar")}" />`;
  }
  return `<span class="avatar${safeSize}" aria-label="${escapeHtml(label || "avatar")}">${escapeHtml(fallback)}</span>`;
}

function renderUser() {
  const user = state.currentUser;
  const username = user?.username || "我";
  elements.currentUsername.textContent = username;
  elements.currentUserAvatar.innerHTML = avatarMarkup(
    user?.avatar_url,
    username,
    firstText(username, "我"),
    "large",
  );
  if (elements.settingsUserAvatar) {
    elements.settingsUserAvatar.innerHTML = avatarMarkup(
      user?.avatar_url,
      username,
      firstText(username, "我"),
      "large",
    );
  }
  if (elements.userProfileUsernameInput) {
    elements.userProfileUsernameInput.value = username;
  }
}

function renderCharacterPanel() {
  const character = state.currentCharacter;
  elements.currentCharacterAvatar.innerHTML = avatarMarkup(
    character?.avatar_url,
    character?.display_name,
    firstText(character?.display_name, "AI"),
    "large",
  );
  updatePersonaEditorHeader();
}

function updatePersonaEditorHeader() {
  if (!elements.personaEditorCharacterName) {
    return;
  }
  const character = state.currentCharacter;
  elements.personaEditorCharacterName.textContent = character?.display_name || "-";
  elements.personaEditorCharacterId.textContent = character?.id || getCharacterId();
  elements.personaEditorSelectedCount.textContent = String(state.selectedPersonaTurns.length);
}

function renderCharacters() {
  const options = state.characters
    .map((character) => {
      return `<option value="${escapeHtml(character.id)}">${escapeHtml(character.display_name)}</option>`;
    })
    .join("");
  elements.characterSelect.innerHTML = options;
  elements.settingsCharacterSelect.innerHTML = options;
}

function renderSessions() {
  if (!state.sessions.length) {
    elements.sessionList.innerHTML = `<div class="empty-state">暂无会话</div>`;
    return;
  }
  elements.sessionList.innerHTML = state.sessions
    .map((session) => {
      const activeClass = session.id === state.currentSessionId ? " active" : "";
      const title = session.last_user_message || session.id;
      const subtitle = session.last_reply || `${session.turn_count} 轮`;
      return `
        <button class="session-item${activeClass}" type="button" data-session-id="${escapeHtml(session.id)}">
          <span class="session-title">${escapeHtml(title)}</span>
          <span class="session-subtitle">${escapeHtml(subtitle)}</span>
        </button>
      `;
    })
    .join("");
}

function renderDatabaseInfo(info) {
  elements.databaseInfo.innerHTML = `
    <div class="database-row"><span>Backend</span><strong>${escapeHtml(info.database_backend || "")}</strong></div>
    <div class="database-row"><span>Sessions</span><strong>${escapeHtml(info.session_count ?? 0)}</strong></div>
    <div class="database-row"><span>Turns</span><strong>${escapeHtml(info.turn_count ?? 0)}</strong></div>
    <div class="database-row"><span>Memories</span><strong>${escapeHtml(info.memory_count ?? 0)}</strong></div>
    <div class="database-row"><span>Relationship</span><strong>${escapeHtml(info.relationship_memory_count ?? 0)}</strong></div>
    <div class="database-row"><span>Knowledge</span><strong>${escapeHtml(info.knowledge_count ?? 0)}</strong></div>
    <div class="database-row"><span>Feedback</span><strong>${escapeHtml(info.feedback_count ?? 0)}</strong></div>
    <div class="database-row"><span>Persona</span><strong>${escapeHtml(info.persona_feedback_count ?? 0)}</strong></div>
    <div class="database-path">${escapeHtml(info.database_url || "")}</div>
  `;
}

function renderPersonaFeedbackStats(payload) {
  if (!payload) {
    elements.personaFeedbackStats.innerHTML = `<div class="empty-state">暂无人设反馈</div>`;
    return;
  }
  const counts = payload.rating_counts || {};
  const topIssues = Array.isArray(payload.top_issues) && payload.top_issues.length
    ? payload.top_issues.map((item) => `${item.tag}:${item.count}`).join("，")
    : "无";
  elements.personaFeedbackStats.innerHTML = `
    <div class="database-row"><span>总数</span><strong>${escapeHtml(payload.total_feedback ?? 0)}</strong></div>
    <div class="database-row"><span>good</span><strong>${escapeHtml(counts.good ?? 0)}</strong></div>
    <div class="database-row"><span>bad</span><strong>${escapeHtml(counts.bad ?? 0)}</strong></div>
    <div class="database-row"><span>neutral</span><strong>${escapeHtml(counts.neutral ?? 0)}</strong></div>
    <div class="database-row"><span>可回滚备份</span><strong>${payload.previous_backup_exists ? "有" : "无"}</strong></div>
    <div class="database-row"><span>上次修改</span><strong>${escapeHtml(payload.last_revision_summary || "无")}</strong></div>
    <div class="database-path">${escapeHtml(topIssues)}</div>
  `;
}

function renderPersonaReview(review) {
  state.personaReview = review;
  elements.applyPersonaButton.disabled = !review?.preview_character_json;
  if (!review) {
    elements.personaReviewPreview.innerHTML = `<div class="empty-state">还没有生成修改建议</div>`;
    return;
  }
  const sections = [
    ["主要问题", review.main_issues],
    ["修改计划", review.revision_plan],
    ["修改字段", review.changed_fields],
    ["太 AI", review.too_ai_expressions],
    ["不像人设", review.out_of_character],
    ["应加强", review.strengthen_styles],
    ["应删除/弱化", review.remove_styles],
    ["风险", review.risk_notes],
  ];
  elements.personaReviewPreview.innerHTML = `
    ${sections
      .map(([label, values]) => {
        const text = Array.isArray(values) && values.length ? values.join("；") : "无";
        return `<div class="database-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(text)}</strong></div>`;
      })
      .join("")}
    <pre>${escapeHtml(JSON.stringify(review.preview_character_json || {}, null, 2))}</pre>
  `;
}

function renderPersonaTags() {
  elements.personaTagList.innerHTML = PERSONA_TAG_OPTIONS.map((option) => {
    return `<button type="button" data-persona-tag="${escapeHtml(option.tag)}">${escapeHtml(option.label)}</button>`;
  }).join("");
}

function renderSelectedPersonaTurns() {
  updatePersonaEditorHeader();
  if (!state.selectedPersonaTurns.length) {
    elements.selectedPersonaTurns.innerHTML = `<div class="empty-state">还没有选择对话。先在角色回复旁边点“选中用于人设修改”。</div>`;
    return;
  }
  elements.selectedPersonaTurns.innerHTML = state.selectedPersonaTurns
    .map((turn) => {
      return `
        <article class="selected-persona-turn">
          <div class="memory-top">
            <span>turn #${escapeHtml(turn.turn_id || "")} / ${escapeHtml(turn.emotion || "neutral")}</span>
            <button class="text-button danger" type="button" data-remove-persona-turn="${escapeHtml(turn.turn_id)}">取消选择</button>
          </div>
          <div class="database-path">session: ${escapeHtml(turn.session_id || "-")} / character: ${escapeHtml(turn.character_id || getCharacterId())}</div>
          <p><strong>用户：</strong>${escapeHtml(turn.user_message)}</p>
          <p><strong>角色：</strong>${escapeHtml(turn.assistant_message)}</p>
        </article>
      `;
    })
    .join("");
}

function renderPersonaEditorChat() {
  if (!state.personaEditorHistory.length) {
    elements.personaEditorChat.innerHTML = `<div class="empty-state">这里会显示你和人设编辑 AI 的讨论。它不是当前角色，不会直接改文件。</div>`;
    return;
  }
  elements.personaEditorChat.innerHTML = state.personaEditorHistory
    .map((item) => {
      const roleLabel = item.role === "assistant" ? "人设编辑 AI" : "你";
      return `
        <article class="persona-editor-message ${escapeHtml(item.role)}">
          <strong>${escapeHtml(roleLabel)}</strong>
          <p>${escapeHtml(item.content)}</p>
        </article>
      `;
    })
    .join("");
  elements.personaEditorChat.scrollTop = elements.personaEditorChat.scrollHeight;
}

function clearPersonaWorkbench() {
  state.personaReview = null;
  state.personaEditorHistory = [];
  state.selectedPersonaTurns = [];
  elements.personaEditorInput.value = "";
  renderPersonaReview(null);
  renderPersonaEditorChat();
  renderSelectedPersonaTurns();
  renderMessagesSelectionState();
}

function renderMemories(memories) {
  if (!memories.length) {
    elements.memoryList.innerHTML = `<div class="empty-state">暂无长期记忆</div>`;
    return;
  }
  elements.memoryList.innerHTML = memories
    .map((memory) => {
      const tags = Array.isArray(memory.tags) && memory.tags.length ? memory.tags.join(", ") : "无标签";
      return `
        <article class="memory-card">
          <div class="memory-top">
            <span>${escapeHtml(memory.memory_type || "note")}</span>
            <strong>${escapeHtml(memory.importance)}</strong>
          </div>
          <p>${escapeHtml(memory.content)}</p>
          <small>${escapeHtml(tags)}</small>
          <button class="text-button danger" type="button" data-memory-id="${escapeHtml(memory.id)}">删除</button>
        </article>
      `;
    })
    .join("");
}

function renderMemorySuggestions(suggestions) {
  state.memorySuggestions = suggestions || [];
  if (!state.memorySuggestions.length) {
    elements.memorySuggestionList.innerHTML = "";
    return;
  }
  elements.memorySuggestionList.innerHTML = state.memorySuggestions
    .map((suggestion, index) => {
      return `
        <article class="memory-suggestion">
          <p>${escapeHtml(suggestion.content || "")}</p>
          <button class="text-button" type="button" data-suggestion-index="${index}">保存建议</button>
        </article>
      `;
    })
    .join("");
}

function renderMemoryConfirmations(suggestions) {
  if (!suggestions || !suggestions.length) {
    elements.memoryConfirmList.innerHTML = "";
    return;
  }
  elements.memoryConfirmList.innerHTML = suggestions
    .map((suggestion, index) => {
      return `
        <article class="memory-confirm">
          <div>
            <strong>要记住这件事吗？</strong>
            <p>${escapeHtml(suggestion.content || "")}</p>
          </div>
          <div class="memory-confirm-actions">
            <button class="text-button" type="button" data-confirm-memory="${index}">记住</button>
            <button class="text-button danger" type="button" data-dismiss-memory="${index}">忽略</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderKnowledge(items) {
  if (!items.length) {
    elements.knowledgeList.innerHTML = `<div class="empty-state">暂无数据库知识</div>`;
    return;
  }
  elements.knowledgeList.innerHTML = items
    .map((item) => {
      const tags = Array.isArray(item.tags) && item.tags.length ? item.tags.join(", ") : "无标签";
      return `
        <article class="knowledge-card">
          <div class="memory-top">
            <span>${escapeHtml(item.source_type)}</span>
            <strong>#${escapeHtml(item.id)}</strong>
          </div>
          <h4>${escapeHtml(item.title || "未命名")}</h4>
          <p>${escapeHtml(item.content)}</p>
          <small>${escapeHtml(tags)}</small>
          <button class="text-button danger" type="button" data-knowledge-id="${escapeHtml(item.id)}">删除</button>
        </article>
      `;
    })
    .join("");
}

function personaFeedbackMarkup(turn) {
  const selected = state.selectedPersonaTurns.some((item) => Number(item.turn_id) === Number(turn.id));
  return `
    <div class="persona-feedback" data-persona-feedback-panel="${escapeHtml(turn.id)}">
      <button
        class="persona-select-button${selected ? " selected" : ""}"
        type="button"
        data-select-persona-turn="${escapeHtml(turn.id)}"
      >${selected ? "已选中" : "选中用于人设修改"}</button>
      <div class="persona-feedback-status"></div>
    </div>
  `;
}

function turnMarkup(turn) {
  const audioPath = turn.debug?.audio_path;
  const audio = audioPath ? `<audio class="audio-player" controls src="${escapeHtml(audioPath)}"></audio>` : "";
  const user = state.currentUser || {};
  const character = state.currentCharacter || {};
  return `
    <article class="message-pair">
      <div class="message-row user">
        ${avatarMarkup(user.avatar_url, user.username, firstText(user.username, "我"))}
        <div class="bubble user">${escapeHtml(turn.user_message)}</div>
      </div>
      <div class="message-row assistant">
        ${avatarMarkup(character.avatar_url, character.display_name, firstText(character.display_name, "AI"))}
        <div class="bubble assistant">
          <div>${escapeHtml(turn.reply)}</div>
          <span class="emotion">${escapeHtml(turn.emotion)}</span>
          ${audio}
          ${personaFeedbackMarkup(turn)}
        </div>
      </div>
    </article>
  `;
}

function renderMessages(turns) {
  if (!turns.length) {
    elements.messages.innerHTML = `<div class="empty-state centered">开始一轮新对话</div>`;
    return;
  }
  elements.messages.innerHTML = turns.map(turnMarkup).join("");
  renderMessagesSelectionState();
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function renderMessagesSelectionState() {
  const selectedIds = new Set(state.selectedPersonaTurns.map((turn) => String(turn.turn_id)));
  elements.messages.querySelectorAll("[data-persona-feedback-panel]").forEach((panel) => {
    const turnId = panel.dataset.personaFeedbackPanel;
    const selected = selectedIds.has(String(turnId));
    const pair = panel.closest(".message-pair");
    const button = panel.querySelector("[data-select-persona-turn]");
    pair?.classList.toggle("persona-selected", selected);
    if (button) {
      button.classList.toggle("selected", selected);
      button.textContent = selected ? "已选中" : "选中用于人设修改";
    }
  });
}

function renderDebugFromTurn(turn) {
  if (!turn) {
    state.currentTurnId = null;
    renderDebug({ candidates: [], debug: {} });
    return;
  }
  state.currentTurnId = turn.id;
  renderDebug({ candidates: turn.candidates || [], debug: turn.debug || {} });
}

function renderDebug(payload) {
  const candidates = payload.candidates || [];
  const debug = payload.debug || {};
  const judge = debug.style_judge || {};
  const bestIndex = Number.isInteger(judge.best_index) ? judge.best_index : -1;
  elements.candidateList.innerHTML = candidates.length
    ? candidates
        .map((candidate, index) => {
          const score = Array.isArray(judge.scores) ? judge.scores[index]?.total : null;
          const selectedClass = index === bestIndex ? " selected" : "";
          return `
            <article class="candidate${selectedClass}">
              <div class="candidate-top">
                <span>#${index + 1}</span>
                <span>${escapeHtml(candidate.emotion || "neutral")}${score ? ` / ${escapeHtml(score)}` : ""}</span>
              </div>
              <p>${escapeHtml(candidate.reply || "")}</p>
              <small>${escapeHtml(candidate.reason || "")}</small>
            </article>
          `;
        })
        .join("")
    : `<div class="empty-state">暂无候选</div>`;

  const retrievalRows = [
    ["Lore", debug.used_lore],
    ["Dialogues", debug.used_dialogues],
    ["Reactions", debug.used_reactions],
    ["Memories", debug.used_memories],
    ["History", debug.history_count == null ? [] : [debug.history_count]],
  ];
  elements.retrievalList.innerHTML = retrievalRows
    .map(([label, values]) => {
      const ids = Array.isArray(values) && values.length ? values.join(", ") : "无";
      return `<div class="retrieval-row"><span>${label}</span><strong>${escapeHtml(ids)}</strong></div>`;
    })
    .join("");
  if (judge && Object.keys(judge).length) {
    elements.retrievalList.insertAdjacentHTML(
      "beforeend",
      `<div class="retrieval-row"><span>Style</span><strong>${escapeHtml(judge.scores?.[bestIndex]?.total ?? "无")}</strong></div>`,
    );
    elements.retrievalList.insertAdjacentHTML(
      "beforeend",
      `<div class="retrieval-row"><span>Rewrite</span><strong>${judge.rewritten ? "是" : "否"}</strong></div>`,
    );
  }
  elements.rawDebug.textContent = JSON.stringify(debug, null, 2);
  renderMemorySuggestions(debug.memory_suggestions || []);
  renderMemoryConfirmations(debug.memory_suggestions || []);
}

async function loadMe() {
  state.currentUser = await requestJson("/auth/me");
  renderUser();
}

async function loadCharacters() {
  const payload = await requestJson("/characters");
  state.characters = payload.characters || [];
  renderCharacters();
  const currentId = getCharacterId();
  if (state.characters.length && !state.characters.some((character) => character.id === currentId)) {
    setCharacterId(state.characters[0].id);
  }
}

async function loadCharacterCard() {
  const characterId = getCharacterId();
  try {
    const payload = await requestJson(`/characters/${encodeURIComponent(characterId)}`);
    state.currentCharacter = payload;
    elements.characterJsonInput.value = JSON.stringify(payload, null, 2);
    renderCharacterPanel();
  } catch (error) {
    state.currentCharacter = null;
    elements.characterJsonInput.value = `// ${friendlyError(error)}`;
    renderCharacterPanel();
    setStatus("Character load error");
    throw error;
  }
}

async function saveCharacterCard() {
  const characterId = getCharacterId();
  const payload = JSON.parse(elements.characterJsonInput.value);
  await requestJson(`/characters/${encodeURIComponent(characterId)}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  await loadCharacters();
  setCharacterId(characterId);
  await loadCharacterCard();
}

async function loadSessions() {
  const payload = await requestJson("/debug/sessions");
  state.sessions = payload.sessions || [];
  renderSessions();
}

async function loadDatabaseInfo() {
  const payload = await requestJson("/debug/database");
  renderDatabaseInfo(payload);
}

async function loadAppStatus() {
  const [health, database] = await Promise.all([
    requestJson("/health").catch((error) => ({ status: friendlyError(error), postgres: false })),
    requestJson("/debug/database").catch((error) => ({ error: friendlyError(error) })),
  ]);
  elements.appStatusInfo.innerHTML = `
    <div class="status-row"><span>后端</span><strong>${escapeHtml(health.status || "unknown")}</strong></div>
    <div class="status-row"><span>PostgreSQL</span><strong>${health.postgres ? "可用" : "不可用"}</strong></div>
    <div class="status-row"><span>会话</span><strong>${escapeHtml(database.session_count ?? "-")}</strong></div>
    <div class="status-row"><span>记忆</span><strong>${escapeHtml(database.memory_count ?? "-")}</strong></div>
  `;
}

async function loadMemories() {
  const payload = await requestJson(`/memory?character_id=${encodeURIComponent(getCharacterId())}`);
  renderMemories(payload.memories || []);
}

async function loadKnowledge() {
  const payload = await requestJson(`/knowledge?character_id=${encodeURIComponent(getCharacterId())}`);
  renderKnowledge(payload.items || []);
}

async function loadPersonaFeedbackStats() {
  const [feedback, debug] = await Promise.all([
    requestJson(`/feedback/persona/${encodeURIComponent(getCharacterId())}`),
    requestJson(`/debug/characters/${encodeURIComponent(getCharacterId())}`),
  ]);
  renderPersonaFeedbackStats({
    ...feedback,
    previous_backup_exists: debug.previous_backup_exists,
    last_revision_summary: debug.last_revision_note?.summary || "",
  });
}

async function findTurnForFeedback(turnId) {
  if (!state.currentSessionId) {
    return null;
  }
  const payload = await requestJson(`/debug/sessions/${encodeURIComponent(state.currentSessionId)}/turns`);
  return (payload.turns || []).find((turn) => Number(turn.id) === Number(turnId));
}

async function togglePersonaTurnSelection(turnId) {
  const existingIndex = state.selectedPersonaTurns.findIndex((turn) => Number(turn.turn_id) === Number(turnId));
  if (existingIndex >= 0) {
    state.selectedPersonaTurns.splice(existingIndex, 1);
    renderSelectedPersonaTurns();
    renderMessagesSelectionState();
    return;
  }
  const turn = await findTurnForFeedback(turnId);
  if (!turn) {
    window.alert("没有找到这条回复。");
    return;
  }
  state.selectedPersonaTurns.push({
    turn_id: turn.id,
    session_id: turn.session_id || state.currentSessionId,
    user_message: turn.user_message,
    assistant_message: turn.reply,
    emotion: turn.emotion || "neutral",
    character_id: turn.character_id || getCharacterId(),
  });
  renderSelectedPersonaTurns();
  renderMessagesSelectionState();
  setPersonaEditorOpen(true);
}

function appendPersonaTagText(text) {
  const current = elements.personaEditorInput.value.trim();
  elements.personaEditorInput.value = current ? `${current}；${text}` : text;
  elements.personaEditorInput.focus();
}

function inferPersonaFeedback(comment) {
  const text = comment.toLowerCase();
  const tags = [];
  const tagRules = [
    ["太 ai", "too_ai"],
    ["太ai", "too_ai"],
    ["ai", "too_ai"],
    ["不像", "out_of_character"],
    ["太温柔", "too_soft"],
    ["太冷淡", "too_cold"],
    ["太刺", "too_harsh"],
    ["太啰嗦", "too_verbose"],
    ["太客服", "too_customer_service"],
    ["心理咨询", "too_therapy_like"],
    ["口癖", "missing_character_phrase"],
    ["别扭", "missing_awkwardness"],
    ["保留", "keep_style"],
    ["很好", "keep_style"],
    ["语气对了", "right_tone"],
    ["样例", "good_example"],
    ["更自然", "more_natural"],
    ["更短", "shorter"],
  ];
  for (const [keyword, tag] of tagRules) {
    if (text.includes(keyword) && !tags.includes(tag)) {
      tags.push(tag);
    }
  }
  const goodTags = ["keep_style", "right_tone", "good_example"];
  const rating = tags.length && tags.every((tag) => goodTags.includes(tag)) ? "good" : "bad";
  return {
    rating: comment.trim() ? rating : "neutral",
    issue_tags: tags,
  };
}

async function saveSelectedPersonaFeedback() {
  const comment = elements.personaEditorInput.value.trim();
  if (!state.selectedPersonaTurns.length) {
    window.alert("先选择至少一条角色回复。");
    return;
  }
  if (!comment) {
    window.alert("先写一点评价，或者点击标签插入常用评价。");
    return;
  }
  const inferred = inferPersonaFeedback(comment);
  for (const turn of state.selectedPersonaTurns) {
    await requestJson("/feedback/persona/turn", {
      method: "POST",
      body: JSON.stringify({
        character_id: turn.character_id || getCharacterId(),
        session_id: turn.session_id,
        turn_id: turn.turn_id,
        user_message: turn.user_message,
        assistant_message: turn.assistant_message,
        rating: inferred.rating,
        issue_tags: inferred.issue_tags,
        comment,
      }),
    });
  }
  await loadPersonaFeedbackStats();
  await loadDatabaseInfo();
  setStatus("Persona feedback saved");
}

async function sendPersonaEditorMessage() {
  const message = elements.personaEditorInput.value.trim();
  if (!message) {
    window.alert("先写一点评价，或者点击标签插入常用评价。");
    return;
  }
  elements.sendPersonaEditorButton.disabled = true;
  try {
    state.personaEditorHistory.push({ role: "user", content: message });
    renderPersonaEditorChat();
    const payload = await requestJson(
      `/characters/${encodeURIComponent(getCharacterId())}/persona-review/chat`,
      {
        method: "POST",
        body: JSON.stringify({
          selected_turns: state.selectedPersonaTurns,
          message,
          history: state.personaEditorHistory.slice(0, -1),
        }),
      },
    );
    state.personaEditorHistory = payload.history || state.personaEditorHistory;
    elements.personaEditorInput.value = "";
    renderPersonaEditorChat();
    setStatus(payload.should_generate_final ? "Ready to finalize" : "Persona editor replied");
  } finally {
    elements.sendPersonaEditorButton.disabled = false;
  }
}

async function summarizePersonaReview() {
  elements.summarizePersonaButton.disabled = true;
  elements.personaReviewPreview.innerHTML = `<div class="empty-state">生成最终方案中...</div>`;
  try {
    const payload = await requestJson(
      `/characters/${encodeURIComponent(getCharacterId())}/persona-review/finalize`,
      {
        method: "POST",
        body: JSON.stringify({
          selected_turns: state.selectedPersonaTurns,
          history: state.personaEditorHistory,
          limit: 30,
        }),
      },
    );
    renderPersonaReview(payload);
    setStatus("Persona final plan ready");
  } finally {
    elements.summarizePersonaButton.disabled = false;
  }
}

async function applyPersonaReview() {
  if (!state.personaReview?.preview_character_json) {
    window.alert("请先生成修改建议。");
    return;
  }
  if (!window.confirm("确认应用这次人设修改？当前 character.json 会先备份为上一版。")) {
    return;
  }
  const payload = await requestJson(
    `/characters/${encodeURIComponent(getCharacterId())}/persona-review/apply`,
    {
      method: "POST",
      body: JSON.stringify({
        preview_character_json: state.personaReview.preview_character_json,
        review_summary: state.personaReview,
      }),
    },
  );
  renderPersonaReview(null);
  await loadCharacters();
  setCharacterId(payload.character?.id || getCharacterId());
  await loadCharacterCard();
  await loadPersonaFeedbackStats();
  setStatus(`Persona applied: ${(payload.changed_fields || []).join(", ")}`);
}

async function rollbackPersonaReview() {
  if (!window.confirm("回滚到上一版人设？当前 character.json 会被上一版覆盖。")) {
    return;
  }
  const payload = await requestJson(
    `/characters/${encodeURIComponent(getCharacterId())}/persona-review/rollback`,
    { method: "POST" },
  );
  renderPersonaReview(null);
  await loadCharacters();
  setCharacterId(payload.character?.id || getCharacterId());
  await loadCharacterCard();
  await loadPersonaFeedbackStats();
  setStatus("Persona rolled back");
}

async function loadSession(sessionId) {
  state.currentSessionId = sessionId;
  elements.activeSessionTitle.textContent = `会话 ${sessionId.slice(0, 8)}`;
  const payload = await requestJson(`/debug/sessions/${encodeURIComponent(sessionId)}/turns`);
  renderMessages(payload.turns || []);
  renderDebugFromTurn((payload.turns || [])[payload.turns.length - 1]);
  renderSessions();
}

function startNewSession() {
  state.currentSessionId = null;
  state.currentTurnId = null;
  state.selectedPersonaTurns = [];
  elements.activeSessionTitle.textContent = "新会话";
  elements.messages.innerHTML = `<div class="empty-state centered">开始一轮新对话</div>`;
  renderDebug({ candidates: [], debug: {} });
  renderMemoryConfirmations([]);
  renderSelectedPersonaTurns();
  renderMessagesSelectionState();
  renderSessions();
  elements.messageInput.focus();
}

async function sendMessage(message) {
  const voice = elements.voiceToggle.checked;
  const body = {
    character_id: getCharacterId(),
    message,
    debug_prompt: elements.promptToggle.checked,
  };
  if (voice) {
    body.voice = true;
  }
  if (state.currentSessionId) {
    body.session_id = state.currentSessionId;
  }

  setStatus("Sending");
  elements.sendButton.disabled = true;
  const payload = await requestJson(voice ? "/chat" : "/chat/text", {
    method: "POST",
    body: JSON.stringify(body),
  });

  state.currentSessionId = payload.session_id;
  state.currentTurnId = payload.turn_id;
  elements.activeSessionTitle.textContent = `会话 ${payload.session_id.slice(0, 8)}`;
  await loadSessions();
  await loadDatabaseInfo();
  await loadMemories();
  await loadKnowledge();
  await loadSession(payload.session_id);
  renderDebug(payload);
  setStatus(payload.debug?.mode || "Ready");
}

async function uploadFile(url, file) {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson(url, {
    method: "POST",
    body: formData,
  });
}

async function uploadUserAvatar(file) {
  await uploadFile("/auth/me/avatar", file);
  await loadMe();
  setStatus("用户头像已更新");
}

async function saveUserProfile() {
  const username = elements.userProfileUsernameInput.value.trim();
  if (!username) {
    window.alert("显示 ID / 用户名不能为空。");
    return;
  }
  state.currentUser = await requestJson("/auth/me", {
    method: "PUT",
    body: JSON.stringify({ username }),
  });
  renderUser();
  setStatus("用户信息已更新");
}

async function uploadCharacterAvatar(file) {
  const characterId = getCharacterId();
  await uploadFile(`/characters/${encodeURIComponent(characterId)}/avatar`, file);
  await loadCharacters();
  setCharacterId(characterId);
  await loadCharacterCard();
  if (state.currentSessionId) {
    await loadSession(state.currentSessionId);
  }
  setStatus("角色头像已更新");
}

async function initializeApp() {
  window.localStorage.removeItem("roleChatbotToken");
  setAuthenticated(true);
  setDebugMode(window.localStorage.getItem("roleChatbotDebugMode") === "1");
  setVoiceEnabled(window.localStorage.getItem("roleChatbotVoice") === "1");
  await loadMe();
  await loadCharacters();
  await loadCharacterCard();
  await loadSessions();
  await loadDatabaseInfo();
  await loadMemories();
  await loadKnowledge();
  await loadPersonaFeedbackStats();
  renderPersonaTags();
  renderSelectedPersonaTurns();
  renderPersonaEditorChat();
  renderPersonaReview(null);
  startNewSession();
}

elements.userAvatarInput.addEventListener("change", async () => {
  const file = elements.userAvatarInput.files?.[0];
  if (!file) {
    return;
  }
  try {
    await uploadUserAvatar(file);
  } catch (error) {
    window.alert(friendlyError(error));
  } finally {
    elements.userAvatarInput.value = "";
  }
});
elements.settingsUserAvatarInput.addEventListener("change", async () => {
  const file = elements.settingsUserAvatarInput.files?.[0];
  if (!file) {
    return;
  }
  try {
    await uploadUserAvatar(file);
  } catch (error) {
    window.alert(friendlyError(error));
  } finally {
    elements.settingsUserAvatarInput.value = "";
  }
});
elements.saveUserProfileButton.addEventListener("click", async () => {
  try {
    await saveUserProfile();
  } catch (error) {
    window.alert(friendlyError(error));
    setStatus("Error");
  }
});
elements.characterAvatarInput.addEventListener("change", async () => {
  const file = elements.characterAvatarInput.files?.[0];
  if (!file) {
    return;
  }
  try {
    await uploadCharacterAvatar(file);
  } catch (error) {
    window.alert(friendlyError(error));
  } finally {
    elements.characterAvatarInput.value = "";
  }
});
elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  if (!message) {
    return;
  }
  elements.messageInput.value = "";
  const user = state.currentUser || {};
  const character = state.currentCharacter || {};
  elements.messages.insertAdjacentHTML(
    "beforeend",
    `<article class="message-pair pending">
      <div class="message-row user">
        ${avatarMarkup(user.avatar_url, user.username, firstText(user.username, "我"))}
        <div class="bubble user">${escapeHtml(message)}</div>
      </div>
      <div class="message-row assistant">
        ${avatarMarkup(character.avatar_url, character.display_name, firstText(character.display_name, "AI"))}
        <div class="bubble assistant">...</div>
      </div>
    </article>`,
  );
  elements.messages.scrollTop = elements.messages.scrollHeight;

  try {
    await sendMessage(message);
  } catch (error) {
    setStatus("Error");
    elements.messages.insertAdjacentHTML("beforeend", `<div class="error-box">${escapeHtml(friendlyError(error))}</div>`);
  } finally {
    elements.sendButton.disabled = false;
    elements.messageInput.focus();
  }
});

elements.newSessionButton.addEventListener("click", startNewSession);
elements.openPersonaEditorButton.addEventListener("click", () => setPersonaEditorOpen(true));
elements.closePersonaEditorButton.addEventListener("click", () => setPersonaEditorOpen(false));
elements.settingsButton.addEventListener("click", () => setSettingsOpen(true));
elements.closeSettingsButton.addEventListener("click", () => setSettingsOpen(false));
elements.settingsOverlay.addEventListener("click", (event) => {
  if (event.target === elements.settingsOverlay) {
    setSettingsOpen(false);
  }
});
elements.settingsDebugToggle.addEventListener("change", () => setDebugMode(elements.settingsDebugToggle.checked));
elements.voiceToggle.addEventListener("change", () => setVoiceEnabled(elements.voiceToggle.checked));
elements.settingsVoiceToggle.addEventListener("change", () => setVoiceEnabled(elements.settingsVoiceToggle.checked));
elements.settingsCharacterSelect.addEventListener("change", async () => {
  setCharacterId(elements.settingsCharacterSelect.value);
  await loadCharacterCard();
  await loadMemories();
  await loadKnowledge();
  await loadPersonaFeedbackStats();
  clearPersonaWorkbench();
  renderPersonaReview(null);
});
elements.characterSelect.addEventListener("change", async () => {
  setCharacterId(elements.characterSelect.value);
  await loadCharacterCard();
  await loadMemories();
  await loadKnowledge();
  await loadPersonaFeedbackStats();
  clearPersonaWorkbench();
  renderPersonaReview(null);
});
elements.refreshSessionsButton.addEventListener("click", async () => {
  await loadSessions();
  await loadDatabaseInfo();
});
elements.deleteSessionButton.addEventListener("click", async () => {
  if (!state.currentSessionId || !window.confirm("删除当前会话记录？")) {
    return;
  }
  await requestJson(`/debug/sessions/${encodeURIComponent(state.currentSessionId)}`, { method: "DELETE" });
  await loadSessions();
  await loadDatabaseInfo();
  startNewSession();
});
elements.clearCurrentSessionButton.addEventListener("click", async () => {
  if (state.currentSessionId) {
    await requestJson(`/debug/sessions/${encodeURIComponent(state.currentSessionId)}`, { method: "DELETE" });
    await loadSessions();
    await loadDatabaseInfo();
  }
  startNewSession();
  setSettingsOpen(false);
});
elements.clearSessionsButton.addEventListener("click", async () => {
  if (!window.confirm("清空全部会话记录？")) {
    return;
  }
  await requestJson("/debug/sessions", { method: "DELETE" });
  await loadSessions();
  await loadDatabaseInfo();
  startNewSession();
});
elements.refreshMemoriesButton.addEventListener("click", loadMemories);
elements.refreshKnowledgeButton.addEventListener("click", loadKnowledge);
elements.refreshPersonaFeedbackButton.addEventListener("click", loadPersonaFeedbackStats);
elements.savePersonaFeedbackButton.addEventListener("click", async () => {
  try {
    await saveSelectedPersonaFeedback();
  } catch (error) {
    window.alert(friendlyError(error));
    setStatus("Error");
  }
});
elements.sendPersonaEditorButton.addEventListener("click", async () => {
  try {
    await sendPersonaEditorMessage();
  } catch (error) {
    window.alert(friendlyError(error));
    setStatus("Error");
  }
});
elements.summarizePersonaButton.addEventListener("click", async () => {
  try {
    await summarizePersonaReview();
  } catch (error) {
    elements.personaReviewPreview.innerHTML = `<div class="error-box">${escapeHtml(friendlyError(error))}</div>`;
    setStatus("Error");
  }
});
elements.applyPersonaButton.addEventListener("click", async () => {
  try {
    await applyPersonaReview();
    await loadPersonaFeedbackStats();
  } catch (error) {
    window.alert(friendlyError(error));
    setStatus("Error");
  }
});
elements.rollbackPersonaButton.addEventListener("click", async () => {
  try {
    await rollbackPersonaReview();
  } catch (error) {
    window.alert(friendlyError(error));
    setStatus("Error");
  }
});
elements.clearPersonaEditorButton.addEventListener("click", clearPersonaWorkbench);
elements.personaTagList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-persona-tag]");
  if (!button) {
    return;
  }
  const option = PERSONA_TAG_OPTIONS.find((item) => item.tag === button.dataset.personaTag);
  appendPersonaTagText(option?.label || button.textContent || "");
});
elements.selectedPersonaTurns.addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove-persona-turn]");
  if (!button) {
    return;
  }
  const turnId = Number(button.dataset.removePersonaTurn);
  state.selectedPersonaTurns = state.selectedPersonaTurns.filter((turn) => Number(turn.turn_id) !== turnId);
  renderSelectedPersonaTurns();
  renderMessagesSelectionState();
});
elements.importKnowledgeButton.addEventListener("click", async () => {
  await requestJson(`/knowledge/import-jsonl?character_id=${encodeURIComponent(getCharacterId())}`, { method: "POST" });
  await loadKnowledge();
  await loadDatabaseInfo();
});
elements.clearKnowledgeButton.addEventListener("click", async () => {
  if (!window.confirm("清空当前角色的数据库知识库？")) {
    return;
  }
  await requestJson(`/knowledge?character_id=${encodeURIComponent(getCharacterId())}`, { method: "DELETE" });
  await loadKnowledge();
  await loadDatabaseInfo();
});
elements.loadCharacterButton.addEventListener("click", loadCharacterCard);
elements.saveCharacterButton.addEventListener("click", async () => {
  try {
    await saveCharacterCard();
    setStatus("Character saved");
  } catch (error) {
    setStatus("Error");
    window.alert(friendlyError(error));
  }
});
elements.memoryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = elements.memoryInput.value.trim();
  if (!content) {
    return;
  }
  const tags = elements.memoryTagsInput.value.split(",").map((tag) => tag.trim()).filter(Boolean);
  await requestJson("/memory", {
    method: "POST",
    body: JSON.stringify({
      character_id: getCharacterId(),
      content,
      memory_type: "note",
      importance: Number(elements.memoryImportanceInput.value || 5),
      tags,
    }),
  });
  elements.memoryInput.value = "";
  elements.memoryTagsInput.value = "";
  await loadMemories();
  await loadDatabaseInfo();
});
elements.memoryList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-memory-id]");
  if (!button) {
    return;
  }
  await requestJson(`/memory/${encodeURIComponent(button.dataset.memoryId)}`, { method: "DELETE" });
  await loadMemories();
  await loadDatabaseInfo();
});
elements.knowledgeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = elements.knowledgeContentInput.value.trim();
  if (!content) {
    return;
  }
  const tags = elements.knowledgeTagsInput.value.split(",").map((tag) => tag.trim()).filter(Boolean);
  await requestJson("/knowledge", {
    method: "POST",
    body: JSON.stringify({
      character_id: getCharacterId(),
      source_type: elements.knowledgeTypeSelect.value || "lore",
      title: elements.knowledgeTitleInput.value.trim(),
      content,
      tags,
    }),
  });
  elements.knowledgeTitleInput.value = "";
  elements.knowledgeContentInput.value = "";
  elements.knowledgeTagsInput.value = "";
  await loadKnowledge();
  await loadDatabaseInfo();
});
elements.knowledgeList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-knowledge-id]");
  if (!button) {
    return;
  }
  await requestJson(`/knowledge/${encodeURIComponent(button.dataset.knowledgeId)}`, { method: "DELETE" });
  await loadKnowledge();
  await loadDatabaseInfo();
});
elements.messages.addEventListener("click", async (event) => {
  const selectButton = event.target.closest("[data-select-persona-turn]");
  if (selectButton) {
    try {
      await togglePersonaTurnSelection(selectButton.dataset.selectPersonaTurn);
    } catch (error) {
      window.alert(friendlyError(error));
    }
    return;
  }
});

async function saveSuggestion(index) {
  const suggestion = state.memorySuggestions[Number(index)];
  if (!suggestion) {
    return;
  }
  await requestJson("/memory", {
    method: "POST",
    body: JSON.stringify({
      character_id: getCharacterId(),
      content: suggestion.content,
      memory_type: suggestion.memory_type || "note",
      importance: Number(suggestion.importance || 5),
      tags: suggestion.tags || [],
    }),
  });
  await requestJson("/relationship-memory", {
    method: "POST",
    body: JSON.stringify({
      character_id: getCharacterId(),
      source_type: "chat",
      source_id: state.currentSessionId,
      source_turn_id: state.currentTurnId,
      content: suggestion.content,
      memory_type: suggestion.memory_type || "note",
      importance: Number(suggestion.importance || 5),
      evidence: {
        confirmed_from: "memory_suggestion",
        tags: suggestion.tags || [],
      },
    }),
  });
  state.memorySuggestions = state.memorySuggestions.filter((_, itemIndex) => itemIndex !== Number(index));
  renderMemoryConfirmations(state.memorySuggestions);
  renderMemorySuggestions(state.memorySuggestions);
  await loadMemories();
  await loadDatabaseInfo();
}

elements.memoryConfirmList.addEventListener("click", async (event) => {
  const saveButton = event.target.closest("[data-confirm-memory]");
  const dismissButton = event.target.closest("[data-dismiss-memory]");
  if (saveButton) {
    await saveSuggestion(saveButton.dataset.confirmMemory);
    return;
  }
  if (dismissButton) {
    state.memorySuggestions = state.memorySuggestions.filter(
      (_, index) => index !== Number(dismissButton.dataset.dismissMemory),
    );
    renderMemoryConfirmations(state.memorySuggestions);
    renderMemorySuggestions(state.memorySuggestions);
  }
});
elements.memorySuggestionList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-suggestion-index]");
  if (button) {
    await saveSuggestion(button.dataset.suggestionIndex);
  }
});
elements.feedbackForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.currentTurnId) {
    window.alert("先选择或发送一轮对话。");
    return;
  }
  await requestJson(`/debug/turns/${encodeURIComponent(state.currentTurnId)}/feedback`, {
    method: "POST",
    body: JSON.stringify({
      score: Number(elements.feedbackScoreInput.value || 8),
      note: elements.feedbackNoteInput.value.trim(),
    }),
  });
  elements.feedbackNoteInput.value = "";
  await loadDatabaseInfo();
});
elements.voiceTestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = elements.voiceTestTextInput.value.trim();
  if (!text) {
    return;
  }
  elements.voiceTestResult.innerHTML = `<div class="empty-state">生成中...</div>`;
  try {
    const payload = await requestJson("/voice/test", {
      method: "POST",
      body: JSON.stringify({
        character_id: getCharacterId(),
        text,
        emotion: elements.voiceTestEmotionSelect.value || "neutral",
      }),
    });
    elements.voiceTestResult.innerHTML = `
      <audio class="audio-player" controls src="${escapeHtml(payload.public_url)}"></audio>
      <div class="database-path">${escapeHtml(payload.audio_path || "")}</div>
    `;
  } catch (error) {
    elements.voiceTestResult.innerHTML = `<div class="error-box">${escapeHtml(friendlyError(error))}</div>`;
  }
});
elements.sessionList.addEventListener("click", async (event) => {
  const item = event.target.closest("[data-session-id]");
  if (item) {
    await loadSession(item.dataset.sessionId);
  }
});

async function boot() {
  setAuthenticated(true);
  try {
    await initializeApp();
  } catch (error) {
    setStatus("Error");
    elements.messages.innerHTML = `<div class="error-box">${escapeHtml(friendlyError(error))}</div>`;
  }
}

boot();
