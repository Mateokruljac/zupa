/**
 * Jednostavan rich text editor (contenteditable + alatna traka)
 */
(function (global) {
  const ALLOWED_TAGS = new Set(["P", "BR", "STRONG", "B", "EM", "I", "U", "UL", "OL", "LI", "A", "H3", "H4", "SPAN", "DIV"]);

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function plainTextToHtml(text) {
    const t = String(text ?? "").trim();
    if (!t) return "";
    return t
      .split(/\n\s*\n/)
      .map((p) => `<p>${escapeHtml(p.trim()).replace(/\n/g, "<br>")}</p>`)
      .join("");
  }

  function normalizeBody(htmlOrText) {
    const s = String(htmlOrText ?? "").trim();
    if (!s) return "";
    if (/<[a-z][\s\S]*>/i.test(s)) return sanitizeHtml(s);
    return plainTextToHtml(s);
  }

  function sanitizeHtml(html) {
    const tpl = document.createElement("template");
    tpl.innerHTML = String(html ?? "");
    const clean = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) return;
        if (child.nodeType !== Node.ELEMENT_NODE) {
          child.remove();
          return;
        }
        if (!ALLOWED_TAGS.has(child.tagName)) {
          const frag = document.createDocumentFragment();
          while (child.firstChild) frag.appendChild(child.firstChild);
          child.replaceWith(frag);
          return;
        }
        if (child.tagName === "A") {
          const href = child.getAttribute("href") || "";
          if (!/^https?:\/\//i.test(href) && !/^mailto:/i.test(href)) {
            child.removeAttribute("href");
          }
          child.removeAttribute("onclick");
          child.removeAttribute("style");
        } else {
          [...child.attributes].forEach((a) => child.removeAttribute(a.name));
        }
        clean(child);
      });
    };
    clean(tpl.content);
    return tpl.innerHTML.trim();
  }

  function toolbarHtml() {
    return `<div class="rte-toolbar" role="toolbar" aria-label="Oblikovanje teksta">
      <button type="button" class="rte-btn" data-cmd="bold" title="Podebljano"><strong>B</strong></button>
      <button type="button" class="rte-btn" data-cmd="italic" title="Kurziv"><em>I</em></button>
      <button type="button" class="rte-btn" data-cmd="underline" title="Podcrtano"><u>U</u></button>
      <span class="rte-sep"></span>
      <button type="button" class="rte-btn" data-cmd="insertUnorderedList" title="Lista">•</button>
      <button type="button" class="rte-btn" data-cmd="insertOrderedList" title="Numerirana lista">1.</button>
      <span class="rte-sep"></span>
      <button type="button" class="rte-btn" data-cmd="createLink" title="Poveznica">🔗</button>
      <button type="button" class="rte-btn" data-cmd="removeFormat" title="Ukloni oblikovanje">✕</button>
    </div>`;
  }

  function mount(wrap, opts = {}) {
    if (!wrap || wrap.dataset.rteMounted) return wrap?.querySelector(".rte-editor");
    wrap.dataset.rteMounted = "1";
    wrap.classList.add("rte-wrap");
    const initial = normalizeBody(opts.html || "");
    wrap.innerHTML = `${toolbarHtml()}<div class="rte-editor" contenteditable="true" role="textbox" aria-multiline="true" data-placeholder="${escapeHtml(opts.placeholder || "Upišite tekst…")}">${initial}</div>`;
    const editor = wrap.querySelector(".rte-editor");

    wrap.querySelectorAll(".rte-btn[data-cmd]").forEach((btn) => {
      btn.addEventListener("mousedown", (e) => e.preventDefault());
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        editor.focus();
        const cmd = btn.dataset.cmd;
        if (cmd === "createLink") {
          const url = prompt("URL poveznice (https://…)", "https://");
          if (url) document.execCommand("createLink", false, url);
          return;
        }
        document.execCommand(cmd, false, null);
        opts.onChange?.(sanitizeHtml(editor.innerHTML));
      });
    });

    editor.addEventListener("input", () => {
      opts.onChange?.(sanitizeHtml(editor.innerHTML));
    });

    editor.addEventListener("paste", (e) => {
      e.preventDefault();
      const text = e.clipboardData?.getData("text/plain") || "";
      document.execCommand("insertText", false, text);
    });

    return editor;
  }

  function getHtml(wrap) {
    const editor = wrap?.querySelector?.(".rte-editor");
    if (!editor) return normalizeBody(wrap?.value || "");
    return sanitizeHtml(editor.innerHTML);
  }

  function setHtml(wrap, html) {
    const editor = wrap?.querySelector?.(".rte-editor");
    if (editor) editor.innerHTML = normalizeBody(html);
  }

  function mountIn(root, selector, opts = {}) {
    root.querySelectorAll(selector).forEach((wrap) => {
      mount(wrap, {
        html: wrap.dataset.rteInitial || "",
        placeholder: wrap.dataset.rtePlaceholder,
        onChange: opts.onChange,
      });
    });
  }

  function renderBodyHtml(htmlOrText) {
    const html = normalizeBody(htmlOrText);
    return html || "<p>—</p>";
  }

  global.PastoralRichText = {
    mount,
    mountIn,
    getHtml,
    setHtml,
    sanitizeHtml,
    normalizeBody,
    renderBodyHtml,
    plainTextToHtml,
  };
})(typeof window !== "undefined" ? window : global);
