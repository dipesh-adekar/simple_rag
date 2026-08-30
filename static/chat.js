(() => {
  const form = document.getElementById("chat-form");
  const messagesEl = document.getElementById("chat-messages");
  const submitBtn = document.getElementById("chat-submit");

  const savedMode = localStorage.getItem("chatMode") || "stream";
  const modeInput = document.querySelector(`input[name="mode"][value="${savedMode}"]`);
  if (modeInput) modeInput.checked = true;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = form.question.value.trim();
    if (!question) return;

    const mode = document.querySelector('input[name="mode"]:checked').value;
    localStorage.setItem("chatMode", mode);

    appendMessage("user", question);
    form.question.value = "";
    submitBtn.disabled = true;

    try {
      if (mode === "stream") {
        await handleStream(question);
      } else {
        await handleNormal(question);
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

  function appendMeta(messageEl, sources, contextChunks) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = `Sources: ${sources.join(", ")} · ${contextChunks} chunk(s) retrieved`;
    messageEl.appendChild(meta);
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  async function handleNormal(question) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("loading");
    contentEl.textContent = "Thinking…";

    try {
      const res = await fetch("/chat/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) throw new Error("Request failed");

      const data = await res.json();
      contentEl.classList.remove("loading");
      contentEl.textContent = data.answer;
      appendMeta(messageEl, data.sources, data.context_chunks);
    } catch {
      contentEl.classList.remove("loading");
      contentEl.textContent = "Something went wrong. Please try again.";
    }
  }

  async function handleStream(question) {
    const messageEl = appendMessage("assistant", "");
    const contentEl = messageEl.querySelector(".message-content");
    contentEl.classList.add("streaming");

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
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
            appendMeta(messageEl, event.sources, event.context_chunks);
          }
        }
      }
    } catch {
      contentEl.classList.remove("streaming");
      contentEl.textContent = "Something went wrong. Please try again.";
    }
  }
})();
