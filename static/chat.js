(() => {
  const form = document.getElementById("chat-form");
  const messagesEl = document.getElementById("chat-messages");
  const submitBtn = document.getElementById("chat-submit");
  const sourceSelect = document.getElementById("source");
  const clearBtn = document.getElementById("clear-history");
  const hasDocuments = form.dataset.hasDocuments === "true";

  const HISTORY_KEY = "chatHistory";
  const MAX_HISTORY = 50;

  const savedMode = localStorage.getItem("chatMode") || "stream";
  const modeInput = document.querySelector(`input[name="mode"][value="${savedMode}"]`);
  if (modeInput) modeInput.checked = true;

  const savedSource = localStorage.getItem("chatSource");
  if (savedSource && sourceSelect) {
    sourceSelect.value = savedSource;
  }

  if (!hasDocuments) {
    submitBtn.disabled = true;
    form.question.disabled = true;
    if (sourceSelect) sourceSelect.disabled = true;
  }

  loadHistory();

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      localStorage.removeItem(HISTORY_KEY);
      messagesEl.innerHTML = hasDocuments
        ? '<p class="muted chat-empty">No messages yet. Ask something about your uploaded documents.</p>'
        : '<div class="alert alert-error chat-empty">No documents indexed yet. <a href="/">Upload a document</a> to start chatting.</div>';
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!hasDocuments) return;

    const question = form.question.value.trim();
    if (!question) return;

    const mode = document.querySelector('input[name="mode"]:checked').value;
    const source = sourceSelect ? sourceSelect.value : "";

    localStorage.setItem("chatMode", mode);
    localStorage.setItem("chatSource", source);

    appendMessage("user", question);
    form.question.value = "";
    submitBtn.disabled = true;

    try {
      if (mode === "stream") {
        await handleStream(question, source);
      } else {
        await handleNormal(question, source);
      }
    } finally {
      submitBtn.disabled = false;
      saveHistory();
    }
  });

  function loadHistory() {
    const raw = localStorage.getItem(HISTORY_KEY);
    if (!raw) return;

    try {
      const history = JSON.parse(raw);
      if (!Array.isArray(history) || history.length === 0) return;

      messagesEl.innerHTML = "";
      for (const entry of history) {
        renderHistoryEntry(entry);
      }
      scrollToBottom();
    } catch {
      localStorage.removeItem(HISTORY_KEY);
    }
  }

  function saveHistory() {
    const entries = [];
    for (const messageEl of messagesEl.querySelectorAll(".message")) {
      const role = messageEl.classList.contains("message-user") ? "user" : "assistant";
      const contentEl = messageEl.querySelector(".message-content");
      const entry = {
        role,
        content: contentEl.dataset.rawContent || contentEl.textContent || "",
      };

      const metaEl = messageEl.querySelector(".message-meta");
      if (metaEl && metaEl.dataset.meta) {
        entry.meta = JSON.parse(metaEl.dataset.meta);
      }

      const snippetsEl = messageEl.querySelector(".context-snippets");
      if (snippetsEl && snippetsEl.dataset.snippets) {
        entry.snippets = JSON.parse(snippetsEl.dataset.snippets);
      }

      entries.push(entry);
    }

    localStorage.setItem(HISTORY_KEY, JSON.stringify(entries.slice(-MAX_HISTORY)));
  }

  function renderHistoryEntry(entry) {
    const messageEl = appendMessage(entry.role, entry.content, { persist: false });
    if (entry.role === "assistant") {
      setAssistantContent(messageEl.querySelector(".message-content"), entry.content);
      if (entry.meta) {
        appendMeta(messageEl, entry.meta.sources || [], entry.meta.contextChunks || 0, entry.meta.relevant);
      }
      if (entry.snippets) {
        appendSnippets(messageEl, entry.snippets);
      }
    }
  }

  function removeEmptyState() {
    const empty = messagesEl.querySelector(".chat-empty");
    if (empty) empty.remove();
  }

  function setAssistantContent(contentEl, text) {
    contentEl.dataset.rawContent = text;
    contentEl.classList.remove("loading", "streaming");
    contentEl.innerHTML = window.renderMarkdown(text);
  }

  function setUserContent(contentEl, text) {
    contentEl.dataset.rawContent = text;
    contentEl.textContent = text;
  }

  function appendMessage(role, content, options = {}) {
    removeEmptyState();

    const div = document.createElement("div");
    div.className = `message message-${role}`;

    const roleEl = document.createElement("div");
    roleEl.className = "message-role";
    roleEl.textContent = role;

    const contentEl = document.createElement("div");
    contentEl.className = "message-content";

    if (role === "assistant") {
      setAssistantContent(contentEl, content);
    } else {
      setUserContent(contentEl, content);
    }

    div.appendChild(roleEl);
    div.appendChild(contentEl);
    messagesEl.appendChild(div);
    scrollToBottom();

    if (options.persist !== false) {
      saveHistory();
    }

    return div;
  }

  function appendMeta(messageEl, sources, contextChunks, relevant) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.dataset.meta = JSON.stringify({ sources, contextChunks, relevant });

    if (relevant === false) {
      meta.textContent = "No relevant context found in your documents.";
    } else if (sources.length) {
      meta.textContent = `Sources: ${sources.join(", ")} · ${contextChunks} chunk(s) retrieved`;
    } else {
      meta.textContent = `${contextChunks} chunk(s) retrieved`;
    }

    messageEl.appendChild(meta);
  }

  function appendSnippets(messageEl, snippets) {
    if (!snippets || snippets.length === 0) return;

    const details = document.createElement("details");
    details.className = "context-snippets";
    details.dataset.snippets = JSON.stringify(snippets);

    const summary = document.createElement("summary");
    summary.textContent = `Context used (${snippets.length} chunk${snippets.length === 1 ? "" : "s"})`;
    details.appendChild(summary);

    const list = document.createElement("div");
    list.className = "snippet-list";

    for (const snippet of snippets) {
      const item = document.createElement("div");
      item.className = "snippet-item";

      const header = document.createElement("div");
      header.className = "snippet-header";
      header.textContent = `${snippet.source} · distance ${snippet.score}`;

      const text = document.createElement("div");
      text.className = "snippet-text";
      text.textContent = snippet.text;

      item.appendChild(header);
      item.appendChild(text);
      list.appendChild(item);
    }

    details.appendChild(list);
    messageEl.appendChild(details);
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function buildRequestBody(question, source) {
    const body = { question };
    if (source) body.source = source;
    return body;
  }

  async function readErrorDetail(response) {
    try {
      const data = await response.json();
      return data.detail || "Request failed";
    } catch {
      return "Request failed";
    }
  }

  async function handleNormal(question, source) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("loading");
    contentEl.textContent = "Thinking…";
    delete contentEl.dataset.rawContent;

    try {
      const res = await fetch("/chat/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody(question, source)),
      });

      if (!res.ok) {
        const detail = await readErrorDetail(res);
        throw new Error(detail);
      }

      const data = await res.json();
      contentEl.classList.remove("loading");
      setAssistantContent(contentEl, data.answer);
      appendMeta(messageEl, data.sources, data.context_chunks, data.relevant);
      appendSnippets(messageEl, data.snippets);
      saveHistory();
    } catch (error) {
      contentEl.classList.remove("loading");
      contentEl.textContent = error.message || "Something went wrong. Please try again.";
      delete contentEl.dataset.rawContent;
    }
  }

  async function handleStream(question, source) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("streaming");
    contentEl.textContent = "";
    delete contentEl.dataset.rawContent;

    let streamedText = "";

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody(question, source)),
      });

      if (!res.ok) {
        const detail = await readErrorDetail(res);
        throw new Error(detail);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          const event = JSON.parse(line.slice(6));

          if (event.type === "token") {
            streamedText += event.content;
            contentEl.textContent = streamedText;
            scrollToBottom();
          } else if (event.type === "done") {
            contentEl.classList.remove("streaming");
            setAssistantContent(contentEl, streamedText);
            appendMeta(messageEl, event.sources, event.context_chunks, event.relevant);
            appendSnippets(messageEl, event.snippets);
            saveHistory();
          }
        }
      }
    } catch (error) {
      contentEl.classList.remove("streaming");
      contentEl.textContent = error.message || "Something went wrong. Please try again.";
      delete contentEl.dataset.rawContent;
    }
  }
})();
