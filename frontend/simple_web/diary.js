const diaryModule = (() => {
  const state = {
    initialized: false,
    currentEntry: null,
    entries: [],
    callbacks: {},
  };

  const elements = {};

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function requestJson(url, options = {}) {
    const body = options.body;
    const isFormData = body instanceof FormData;
    const response = await fetch(url, {
      ...options,
      headers: {
        ...(!isFormData ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = payload.detail || `${response.status} ${response.statusText} at ${url}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return payload;
  }

  function today() {
    return new Date().toISOString().slice(0, 10);
  }

  function parseTags(value) {
    return String(value || "")
      .split(/[,，]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function setDiaryStatus(text) {
    if (elements.statusText) {
      elements.statusText.textContent = text;
    }
    state.callbacks.setStatus?.(text);
  }

  function bindElements() {
    Object.assign(elements, {
      contentInput: document.querySelector("#diaryContentInput"),
      dateFromInput: document.querySelector("#diaryDateFromInput"),
      dateInput: document.querySelector("#diaryDateInput"),
      dateToInput: document.querySelector("#diaryDateToInput"),
      deleteButton: document.querySelector("#deleteDiaryButton"),
      editorTitle: document.querySelector("#diaryEditorTitle"),
      entryList: document.querySelector("#diaryEntryList"),
      filterForm: document.querySelector("#diaryFilterForm"),
      imageInput: document.querySelector("#diaryImageInput"),
      imageList: document.querySelector("#diaryImageList"),
      keywordInput: document.querySelector("#diaryKeywordInput"),
      moodFilterInput: document.querySelector("#diaryMoodFilterInput"),
      moodInput: document.querySelector("#diaryMoodInput"),
      newButton: document.querySelector("#newDiaryButton"),
      readButton: document.querySelector("#readDiaryWithCharacterButton"),
      saveButton: document.querySelector("#saveDiaryButton"),
      statusText: document.querySelector("#diaryStatusText"),
      tagFilterInput: document.querySelector("#diaryTagFilterInput"),
      tagsInput: document.querySelector("#diaryTagsInput"),
      titleInput: document.querySelector("#diaryTitleInput"),
    });
  }

  function renderList() {
    if (!elements.entryList) {
      return;
    }
    if (!state.entries.length) {
      elements.entryList.innerHTML = `<div class="empty-state">暂无日记</div>`;
      return;
    }
    elements.entryList.innerHTML = state.entries
      .map((entry) => {
        const active = state.currentEntry?.id === entry.id ? " active" : "";
        const tags = Array.isArray(entry.tags) && entry.tags.length ? entry.tags.join("，") : "无标签";
        return `
          <button class="diary-entry-item${active}" type="button" data-diary-entry-id="${escapeHtml(entry.id)}">
            <span class="diary-entry-title">${escapeHtml(entry.title || "未命名日记")}</span>
            <span class="diary-entry-meta">${escapeHtml(entry.entry_date)} / ${escapeHtml(entry.mood || "未填写")}</span>
            <span class="diary-entry-excerpt">${escapeHtml(entry.content_excerpt || "")}</span>
            <span class="diary-entry-tags">${escapeHtml(tags)}${entry.image_count ? ` / ${entry.image_count} 图` : ""}</span>
          </button>
        `;
      })
      .join("");
  }

  function renderImages() {
    const attachments = state.currentEntry?.attachments || [];
    if (!attachments.length) {
      elements.imageList.innerHTML = `<div class="empty-state">暂无图片</div>`;
      return;
    }
    elements.imageList.innerHTML = attachments
      .map((image) => {
        return `
          <article class="diary-image-card">
            <img src="${escapeHtml(image.public_url)}" alt="${escapeHtml(image.original_filename || image.filename)}" />
            <div>
              <strong>${escapeHtml(image.original_filename || image.filename)}</strong>
              <button class="text-button danger" type="button" data-diary-image-id="${escapeHtml(image.id)}">删除</button>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderEditor(entry) {
    state.currentEntry = entry;
    const isSaved = Boolean(entry?.id);
    elements.editorTitle.textContent = isSaved ? entry.title || "未命名日记" : "新日记";
    elements.statusText.textContent = isSaved ? `#${entry.id}` : "Draft";
    elements.titleInput.value = entry?.title || "";
    elements.dateInput.value = entry?.entry_date || today();
    elements.moodInput.value = entry?.mood || "";
    elements.tagsInput.value = Array.isArray(entry?.tags) ? entry.tags.join("，") : "";
    elements.contentInput.value = entry?.content_markdown || "";
    elements.deleteButton.disabled = !isSaved;
    elements.readButton.disabled = !isSaved;
    elements.imageInput.disabled = !isSaved;
    renderImages();
    renderList();
  }

  function collectPayload() {
    return {
      title: elements.titleInput.value.trim(),
      content_markdown: elements.contentInput.value.trim(),
      entry_date: elements.dateInput.value || today(),
      mood: elements.moodInput.value.trim(),
      tags: parseTags(elements.tagsInput.value),
    };
  }

  async function loadEntries() {
    const params = new URLSearchParams();
    const filters = [
      ["keyword", elements.keywordInput.value.trim()],
      ["date_from", elements.dateFromInput.value],
      ["date_to", elements.dateToInput.value],
      ["mood", elements.moodFilterInput.value.trim()],
      ["tag", elements.tagFilterInput.value.trim()],
    ];
    for (const [key, value] of filters) {
      if (value) {
        params.set(key, value);
      }
    }
    const payload = await requestJson(`/diary/entries?${params.toString()}`);
    state.entries = payload.entries || [];
    renderList();
  }

  async function loadEntry(entryId) {
    const entry = await requestJson(`/diary/entries/${encodeURIComponent(entryId)}`);
    renderEditor(entry);
  }

  async function saveEntry() {
    const payload = collectPayload();
    if (!payload.title && !payload.content_markdown) {
      window.alert("标题和正文至少写一个。");
      return;
    }
    const isSaved = Boolean(state.currentEntry?.id);
    const entry = await requestJson(
      isSaved ? `/diary/entries/${encodeURIComponent(state.currentEntry.id)}` : "/diary/entries",
      {
        method: isSaved ? "PUT" : "POST",
        body: JSON.stringify(payload),
      },
    );
    await loadEntries();
    renderEditor(entry);
    setDiaryStatus("Diary saved");
  }

  async function deleteEntry() {
    if (!state.currentEntry?.id) {
      return;
    }
    if (!window.confirm("删除这篇日记？")) {
      return;
    }
    await requestJson(`/diary/entries/${encodeURIComponent(state.currentEntry.id)}`, { method: "DELETE" });
    renderEditor(null);
    await loadEntries();
    setDiaryStatus("Diary deleted");
  }

  async function uploadImages() {
    if (!state.currentEntry?.id) {
      window.alert("先保存日记，再上传图片。");
      return;
    }
    const files = Array.from(elements.imageInput.files || []);
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      await requestJson(`/diary/entries/${encodeURIComponent(state.currentEntry.id)}/images`, {
        method: "POST",
        body: formData,
      });
    }
    elements.imageInput.value = "";
    await loadEntry(state.currentEntry.id);
    await loadEntries();
    setDiaryStatus("Diary images updated");
  }

  async function deleteImage(imageId) {
    await requestJson(`/diary/images/${encodeURIComponent(imageId)}`, { method: "DELETE" });
    if (state.currentEntry?.id) {
      await loadEntry(state.currentEntry.id);
      await loadEntries();
    }
  }

  async function readWithCharacter() {
    if (!state.currentEntry?.id) {
      window.alert("先保存日记。");
      return;
    }
    const title = state.currentEntry.title || "这篇日记";
    state.callbacks.switchView?.("chat");
    await state.callbacks.submitChatMessage?.(`读一下《${title}》，陪我聊聊。`, state.currentEntry.id);
  }

  function bindEvents() {
    elements.filterForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await loadEntries();
      } catch (error) {
        window.alert(error.message);
      }
    });
    elements.newButton.addEventListener("click", () => renderEditor(null));
    elements.saveButton.addEventListener("click", async () => {
      try {
        await saveEntry();
      } catch (error) {
        window.alert(error.message);
      }
    });
    elements.deleteButton.addEventListener("click", async () => {
      try {
        await deleteEntry();
      } catch (error) {
        window.alert(error.message);
      }
    });
    elements.readButton.addEventListener("click", async () => {
      try {
        await readWithCharacter();
      } catch (error) {
        window.alert(error.message);
      }
    });
    elements.imageInput.addEventListener("change", async () => {
      try {
        await uploadImages();
      } catch (error) {
        elements.imageInput.value = "";
        window.alert(error.message);
      }
    });
    elements.entryList.addEventListener("click", async (event) => {
      const item = event.target.closest("[data-diary-entry-id]");
      if (!item) {
        return;
      }
      try {
        await loadEntry(item.dataset.diaryEntryId);
      } catch (error) {
        window.alert(error.message);
      }
    });
    elements.imageList.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-diary-image-id]");
      if (!button) {
        return;
      }
      try {
        await deleteImage(button.dataset.diaryImageId);
      } catch (error) {
        window.alert(error.message);
      }
    });
  }

  async function init(callbacks = {}) {
    if (state.initialized) {
      return;
    }
    state.callbacks = callbacks;
    bindElements();
    bindEvents();
    renderEditor(null);
    await loadEntries();
    state.initialized = true;
  }

  async function refresh() {
    if (!state.initialized) {
      return;
    }
    await loadEntries();
  }

  return {
    init,
    refresh,
  };
})();

window.diaryModule = diaryModule;
