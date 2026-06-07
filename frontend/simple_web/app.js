const TOKEN_KEY = "roleChatbotToken";

const state = {
  token: window.localStorage.getItem(TOKEN_KEY) || "",
  hasUser: false,
  currentUser: null,
  currentCharacter: null,
  currentSessionId: null,
  currentTurnId: null,
  memorySuggestions: [],
  personaReview: null,
  characters: [],
  sessions: [],
};

const PERSONA_FEEDBACK_OPTIONS = [
  { label: "符合人设", rating: "good", tags: ["fits_persona"] },
  { label: "不符合人设", rating: "bad", tags: ["out_of_character"] },
  { label: "太 AI", rating: "bad", tags: ["too_ai"] },
  { label: "太温柔", rating: "bad", tags: ["too_soft"] },
  { label: "太冷淡", rating: "bad", tags: ["too_cold"] },
  { label: "太刺人", rating: "bad", tags: ["too_harsh"] },
  { label: "太啰嗦", rating: "bad", tags: ["too_verbose"] },
  { label: "不像角色", rating: "bad", tags: ["out_of_character"] },
  { label: "这条很好，保留这种风格", rating: "good", tags: ["keep_style"] },
];

const elements = {
  activeSessionTitle: document.querySelector("#activeSessionTitle"),
  appStatusInfo: document.querySelector("#appStatusInfo"),
  authError: document.querySelector("#authError"),
  authSubtitle: document.querySelector("#authSubtitle"),
  authTitle: document.querySelector("#authTitle"),
  candidateList: document.querySelector("#candidateList"),
  characterAvatarInput: document.querySelector("#characterAvatarInput"),
  characterJsonInput: document.querySelector("#characterJsonInput"),
  characterSelect: document.querySelector("#characterSelect"),
  chatForm: document.querySelector("#chatForm"),
  clearCurrentSessionButton: document.querySelector("#clearCurrentSessionButton"),
  clearKnowledgeButton: document.querySelector("#clearKnowledgeButton"),
  clearSessionsButton: document.querySelector("#clearSessionsButton"),
  closeSettingsButton: document.querySelector("#closeSettingsButton"),
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
  loginForm: document.querySelector("#loginForm"),
  loginPasswordInput: document.querySelector("#loginPasswordInput"),
  loginUsernameInput: document.querySelector("#loginUsernameInput"),
  logoutButton: document.querySelector("#logoutButton"),
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
  applyPersonaButton: document.querySelector("#applyPersonaButton"),
  personaFeedbackStats: document.querySelector("#personaFeedbackStats"),
  personaReviewPreview: document.querySelector("#personaReviewPreview"),
  promptToggle: document.querySelector("#promptToggle"),
  rawDebug: document.querySelector("#rawDebug"),
  refreshKnowledgeButton: document.querySelector("#refreshKnowledgeButton"),
  refreshMemoriesButton: document.querySelector("#refreshMemoriesButton"),
  refreshPersonaFeedbackButton: document.querySelector("#refreshPersonaFeedbackButton"),
  refreshSessionsButton: document.querySelector("#refreshSessionsButton"),
  retrievalList: document.querySelector("#retrievalList"),
  rollbackPersonaButton: document.querySelector("#rollbackPersonaButton"),
  saveCharacterButton: document.querySelector("#saveCharacterButton"),
  sendButton: document.querySelector("#sendButton"),
  sessionList: document.querySelector("#sessionList"),
  settingsButton: document.querySelector("#settingsButton"),
  settingsCharacterSelect: document.querySelector("#settingsCharacterSelect"),
  settingsDebugToggle: document.querySelector("#settingsDebugToggle"),
  settingsOverlay: document.querySelector("#settingsOverlay"),
  settingsVoiceToggle: document.querySelector("#settingsVoiceToggle"),
  setupForm: document.querySelector("#setupForm"),
  setupPasswordConfirmInput: document.querySelector("#setupPasswordConfirmInput"),
  setupPasswordInput: document.querySelector("#setupPasswordInput"),
  setupUsernameInput: document.querySelector("#setupUsernameInput"),
  statusText: document.querySelector("#statusText"),
  summarizePersonaButton: document.querySelector("#summarizePersonaButton"),
  userAvatarInput: document.querySelector("#userAvatarInput"),
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
  return state.token ? { Authorization: `Bearer ${state.token}`, ...headers } : headers;
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
  if (response.status === 401 && !options.skipAuthRedirect) {
    logout(false, "登录已失效，请重新登录");
  }
  if (!response.ok) {
    const detail = payload.detail || `${response.status} ${response.statusText} at ${url}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return payload;
}

function friendlyError(error) {
  const message = error?.message || String(error);
  if (message.includes("PostgreSQL is not ready")) {
    return "数据库还没准备好。请确认 Docker Desktop 已启动，并已运行 docker compose up -d。";
  }
  if (message.includes("Missing reference audio")) {
    return "还没有放入语音参考音频。可先关闭语音开关继续文字聊天。";
  }
  if (message.includes("GPT-SoVITS")) {
    return "语音服务暂时不可用。可先关闭语音开关继续文字聊天。";
  }
  if (message.includes("LLM request failed")) {
    return "AI 接口调用失败。请检查 API Key、模型名或网络连接。";
  }
  return message;
}

function showAuthError(errorOrMessage) {
  elements.authError.textContent =
    typeof errorOrMessage === "string" ? errorOrMessage : friendlyError(errorOrMessage);
  elements.authError.classList.remove("hidden");
}

function clearAuthError() {
  elements.authError.textContent = "";
  elements.authError.classList.add("hidden");
}

function showAuthMode(mode, message = "") {
  clearAuthError();
  const setup = mode === "setup";
  elements.setupForm.classList.toggle("hidden", !setup);
  elements.loginForm.classList.toggle("hidden", setup);
  elements.authTitle.textContent = setup ? "初始化本地账号" : "本地登录锁";
  elements.authSubtitle.textContent = setup
    ? "第一次使用前，先设置唯一的本地账号和密码。"
    : "请输入本地账号密码后进入聊天。";
  if (message) {
    showAuthError(message);
  }
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
  elements.currentUsername.textContent = user?.username || "未登录";
  elements.currentUserAvatar.innerHTML = avatarMarkup(
    user?.avatar_url,
    user?.username,
    firstText(user?.username, "我"),
    "large",
  );
}

function renderCharacterPanel() {
  const character = state.currentCharacter;
  elements.currentCharacterAvatar.innerHTML = avatarMarkup(
    character?.avatar_url,
    character?.display_name,
    firstText(character?.display_name, "AI"),
    "large",
  );
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
  const chips = PERSONA_FEEDBACK_OPTIONS.map((option) => {
    return `
      <button
        class="${escapeHtml(option.rating)}"
        type="button"
        data-persona-feedback="1"
        data-turn-id="${escapeHtml(turn.id)}"
        data-rating="${escapeHtml(option.rating)}"
        data-tags="${escapeHtml(option.tags.join(","))}"
      >${escapeHtml(option.label)}</button>
    `;
  }).join("");
  return `
    <div class="persona-feedback" data-persona-feedback-panel="${escapeHtml(turn.id)}">
      <textarea rows="2" placeholder="可选备注..."></textarea>
      <div class="persona-feedback-chips">${chips}</div>
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
  elements.messages.scrollTop = elements.messages.scrollHeight;
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
}

async function loadCharacterCard() {
  const characterId = getCharacterId();
  const payload = await requestJson(`/characters/${encodeURIComponent(characterId)}`);
  state.currentCharacter = payload;
  elements.characterJsonInput.value = JSON.stringify(payload, null, 2);
  renderCharacterPanel();
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
  const payload = await requestJson(`/feedback/persona/${encodeURIComponent(getCharacterId())}`);
  renderPersonaFeedbackStats(payload);
}

async function submitPersonaFeedback(button) {
  const turnId = Number(button.dataset.turnId || 0);
  const panel = button.closest("[data-persona-feedback-panel]");
  const status = panel.querySelector(".persona-feedback-status");
  const comment = panel.querySelector("textarea")?.value.trim() || "";
  const turn = await findTurnForFeedback(turnId);
  if (!turn) {
    window.alert("没有找到这条回复。");
    return;
  }
  status.textContent = "保存中...";
  await requestJson("/feedback/persona/turn", {
    method: "POST",
    body: JSON.stringify({
      character_id: turn.character_id || getCharacterId(),
      session_id: turn.session_id || state.currentSessionId,
      turn_id: turn.id,
      user_message: turn.user_message,
      assistant_message: turn.reply,
      rating: button.dataset.rating || "neutral",
      issue_tags: (button.dataset.tags || "").split(",").filter(Boolean),
      comment,
    }),
  });
  status.textContent = "已保存";
  panel.querySelector("textarea").value = "";
  await loadPersonaFeedbackStats();
  await loadDatabaseInfo();
}

async function findTurnForFeedback(turnId) {
  if (!state.currentSessionId) {
    return null;
  }
  const payload = await requestJson(`/debug/sessions/${encodeURIComponent(state.currentSessionId)}/turns`);
  return (payload.turns || []).find((turn) => Number(turn.id) === Number(turnId));
}

async function summarizePersonaReview() {
  elements.summarizePersonaButton.disabled = true;
  elements.personaReviewPreview.innerHTML = `<div class="empty-state">生成中...</div>`;
  try {
    const payload = await requestJson(
      `/characters/${encodeURIComponent(getCharacterId())}/persona-review/summarize`,
      {
        method: "POST",
        body: JSON.stringify({ limit: 30 }),
      },
    );
    renderPersonaReview(payload);
    setStatus("Persona review ready");
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
  elements.activeSessionTitle.textContent = "新会话";
  elements.messages.innerHTML = `<div class="empty-state centered">开始一轮新对话</div>`;
  renderDebug({ candidates: [], debug: {} });
  renderMemoryConfirmations([]);
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

async function afterAuth(payload) {
  state.token = payload.access_token;
  window.localStorage.setItem(TOKEN_KEY, state.token);
  state.currentUser = payload.user;
  setAuthenticated(true);
  renderUser();
  await initializeApp();
}

function logout(callServer = true, message = "") {
  if (callServer && state.token) {
    requestJson("/auth/logout", { method: "POST" }).catch(() => {});
  }
  state.token = "";
  state.currentUser = null;
  window.localStorage.removeItem(TOKEN_KEY);
  setAuthenticated(false);
  showAuthMode(state.hasUser ? "login" : "setup", message);
}

async function initializeApp() {
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
  startNewSession();
}

elements.setupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (elements.setupPasswordInput.value !== elements.setupPasswordConfirmInput.value) {
    showAuthError("两次输入的密码不一致");
    return;
  }
  try {
    const payload = await requestJson("/auth/setup", {
      method: "POST",
      body: JSON.stringify({
        username: elements.setupUsernameInput.value.trim(),
        password: elements.setupPasswordInput.value,
      }),
      skipAuthRedirect: true,
    });
    state.hasUser = true;
    await afterAuth(payload);
  } catch (error) {
    showAuthError(error);
  }
});

elements.loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = await requestJson("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: elements.loginUsernameInput.value.trim(),
        password: elements.loginPasswordInput.value,
      }),
      skipAuthRedirect: true,
    });
    await afterAuth(payload);
  } catch (error) {
    showAuthError(error);
  }
});

elements.logoutButton.addEventListener("click", () => logout(true));
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
  renderPersonaReview(null);
});
elements.characterSelect.addEventListener("change", async () => {
  setCharacterId(elements.characterSelect.value);
  await loadCharacterCard();
  await loadMemories();
  await loadKnowledge();
  await loadPersonaFeedbackStats();
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
  const button = event.target.closest("[data-persona-feedback]");
  if (!button) {
    return;
  }
  try {
    await submitPersonaFeedback(button);
  } catch (error) {
    const panel = button.closest("[data-persona-feedback-panel]");
    const status = panel?.querySelector(".persona-feedback-status");
    if (status) {
      status.textContent = friendlyError(error);
    } else {
      window.alert(friendlyError(error));
    }
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
  setAuthenticated(false);
  try {
    const status = await requestJson("/auth/status", { skipAuthRedirect: true });
    state.hasUser = Boolean(status.has_user);
    if (!state.hasUser) {
      showAuthMode("setup");
      return;
    }
    if (!state.token) {
      showAuthMode("login");
      return;
    }
    setAuthenticated(true);
    await initializeApp();
  } catch (error) {
    logout(false, friendlyError(error));
  }
}

boot();
