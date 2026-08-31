(() => {
  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderInline(text) {
    let html = escapeHtml(text);
    html = html.replace(/`([^`\n]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
    return html;
  }

  function renderMarkdown(text) {
    const lines = text.replace(/\r\n/g, "\n").split("\n");
    const parts = [];
    let paragraph = [];
    let listItems = [];
    let listType = null;
    let inCodeBlock = false;
    let codeLines = [];

    function flushParagraph() {
      if (!paragraph.length) return;
      parts.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
      paragraph = [];
    }

    function flushList() {
      if (!listItems.length) return;
      const tag = listType === "ol" ? "ol" : "ul";
      parts.push(`<${tag}>${listItems.join("")}</${tag}>`);
      listItems = [];
      listType = null;
    }

    for (const line of lines) {
      if (inCodeBlock) {
        if (line.trim() === "```") {
          parts.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
          codeLines = [];
          inCodeBlock = false;
        } else {
          codeLines.push(line);
        }
        continue;
      }

      if (line.trim().startsWith("```")) {
        flushParagraph();
        flushList();
        inCodeBlock = true;
        continue;
      }

      const bulletMatch = line.match(/^\s*[-*]\s+(.+)/);
      if (bulletMatch) {
        flushParagraph();
        if (listType && listType !== "ul") flushList();
        listType = "ul";
        listItems.push(`<li>${renderInline(bulletMatch[1])}</li>`);
        continue;
      }

      const numberedMatch = line.match(/^\s*\d+\.\s+(.+)/);
      if (numberedMatch) {
        flushParagraph();
        if (listType && listType !== "ol") flushList();
        listType = "ol";
        listItems.push(`<li>${renderInline(numberedMatch[1])}</li>`);
        continue;
      }

      flushList();

      if (!line.trim()) {
        flushParagraph();
        continue;
      }

      paragraph.push(line.trim());
    }

    if (inCodeBlock && codeLines.length) {
      parts.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    }

    flushList();
    flushParagraph();

    return parts.join("") || `<p>${renderInline(text)}</p>`;
  }

  window.renderMarkdown = renderMarkdown;
})();
