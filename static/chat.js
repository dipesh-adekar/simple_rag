(() => {
  const form = document.getElementById("chat-form");
  const messagesEl = document.getElementById("chat-messages");
  const submitBtn = document.getElementById("chat-submit");
  const sourceSelect = document.getElementById("source");

  const savedMode = localStorage.getItem("chatMode") || "stream";
  const modeInput = document.querySelector(`input[name="mode"][value="${savedMode}"]`);
  if (modeInput) modeInput.checked = true;

  const savedSource = localStorage.getItem("chatSource");
  if (savedSource && sourceSelect) {
    sourceSelect.value = savedSource;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

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
    }
  });

  function removeEmptyState() {
    const empty = messagesEl.querySelector(".chat-empty");
    if (empty) empty.remove();
  }

  function appendMessage(role, content) {
    removeEmptyState();

    const div = document.createElement("div");
    div.className = `message message-${role}`;

    const roleEl = document.createElement("div");
    roleEl.className = "message-role";
    roleEl.textContent = role;

    const contentEl = document.createElement("div");
    contentEl.className = "message-content";
    contentEl.textContent = content;

    div.appendChild(roleEl);
    div.appendChild(contentEl);
    messagesEl.appendChild(div);
    scrollToBottom();

    return div;
  }

  function appendMeta(messageEl, sources, contextChunks, relevant) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
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

  async function handleNormal(question, source) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("loading");
    contentEl.textContent = "Thinking…";

    try {
      const res = await fetch("/chat/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody(question, source)),
      });

      if (!res.ok) throw new Error("Request failed");

      const data = await res.json();
      contentEl.classList.remove("loading");
      contentEl.textContent = data.answer;
      appendMeta(messageEl, data.sources, data.context_chunks, data.relevant);
      appendSnippets(messageEl, data.snippets);
    } catch {
      contentEl.classList.remove("loading");
      contentEl.textContent = "Something went wrong. Please try again.";
    }
  }

  async function handleStream(question, source) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("streaming");

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody(question, source)),
      });

      if (!res.ok) throw new Error("Request failed");

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
            contentEl.textContent += event.content;
            scrollToBottom();
          } else if (event.type === "done") {
            contentEl.classList.remove("streaming");
            appendMeta(messageEl, event.sources, event.context_chunks, event.relevant);
            appendSnippets(messageEl, event.snippets);
          }
        }
      }
    } catch {
      contentEl.classList.remove("streaming");
      contentEl.textContent = "Something went wrong. Please try again.";
    }
  }
})();
