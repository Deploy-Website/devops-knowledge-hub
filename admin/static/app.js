"use strict";

const state = {
  tree: null,
  collapsed: new Set(),
  searchQuery: "",
  editor: {
    mode: "closed", // "closed" | "new" | "edit"
    path: null,
    protected: false,
    slugEdited: false,
  },
  sectionModal: {
    mode: "create", // "create" | "rename"
    sectionIndex: null,
    slugEdited: false,
  },
};

const els = {
  btnDashboard: document.getElementById("btnDashboard"),
  btnValidate: document.getElementById("btnValidate"),
  btnBuild: document.getElementById("btnBuild"),
  btnViewDocs: document.getElementById("btnViewDocs"),
  btnNewSection: document.getElementById("btnNewSection"),
  btnNewArticle: document.getElementById("btnNewArticle"),
  btnDashNewSection: document.getElementById("btnDashNewSection"),
  btnDashNewArticle: document.getElementById("btnDashNewArticle"),
  searchInput: document.getElementById("searchInput"),
  treeContainer: document.getElementById("treeContainer"),

  dashboardView: document.getElementById("dashboardView"),
  statSections: document.getElementById("statSections"),
  statArticles: document.getElementById("statArticles"),
  statEmpty: document.getElementById("statEmpty"),
  statValid: document.getElementById("statValid"),
  sectionsTableBody: document.getElementById("sectionsTableBody"),

  editorView: document.getElementById("editorView"),
  editorModeBadge: document.getElementById("editorModeBadge"),
  editorPathLabel: document.getElementById("editorPathLabel"),
  btnDeleteArticle: document.getElementById("btnDeleteArticle"),
  btnCancelEdit: document.getElementById("btnCancelEdit"),
  btnSaveArticle: document.getElementById("btnSaveArticle"),
  artTitle: document.getElementById("artTitle"),
  artSection: document.getElementById("artSection"),
  artSlug: document.getElementById("artSlug"),
  artNavTitle: document.getElementById("artNavTitle"),
  chkSyncNavTitle: document.getElementById("chkSyncNavTitle"),
  artTags: document.getElementById("artTags"),
  artContent: document.getElementById("artContent"),
  editorSplit: document.getElementById("editorSplit"),
  previewPane: document.getElementById("previewPane"),

  sectionModal: document.getElementById("sectionModal"),
  sectionModalTitle: document.getElementById("sectionModalTitle"),
  sectionForm: document.getElementById("sectionForm"),
  secTitle: document.getElementById("secTitle"),
  secCreateFields: document.getElementById("secCreateFields"),
  secKind: document.getElementById("secKind"),
  secSlug: document.getElementById("secSlug"),
  secTags: document.getElementById("secTags"),
  btnCloseSectionModal: document.getElementById("btnCloseSectionModal"),
  btnCancelSectionModal: document.getElementById("btnCancelSectionModal"),

  validationModal: document.getElementById("validationModal"),
  validationModalBody: document.getElementById("validationModalBody"),
  btnCloseValidationModal: document.getElementById("btnCloseValidationModal"),
  btnDoneValidationModal: document.getElementById("btnDoneValidationModal"),

  toastContainer: document.getElementById("toastContainer"),
};

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function slugifyText(text) {
  return String(text || "")
    .trim()
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function showToast(message, type = "info") {
  const div = document.createElement("div");
  div.className = `toast ${type}`;
  div.textContent = message;
  els.toastContainer.appendChild(div);
  setTimeout(() => {
    div.remove();
  }, 4000);
}

async function api(url, options = {}) {
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let data = {};
  try {
    data = await resp.json();
  } catch {
    data = {};
  }
  if (!resp.ok) {
    throw new Error(data.error || `HTTP ${resp.status}`);
  }
  return data;
}

function renderInlineMarkdown(escapedText) {
  let out = escapedText;
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  out = out.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    (_, label, href) => {
      const safeHref = /^(https?:\/\/|mailto:|\/|#|[a-zA-Z0-9._/-]+$)/.test(href.trim())
        ? href.trim()
        : "#";
      return `<a href="${safeHref}" target="_blank" rel="noopener">${label}</a>`;
    }
  );
  return out;
}

function renderMarkdownBody(markdown) {
  const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let inFence = false;
  let fenceLines = [];
  let listType = null;
  let inTable = false;
  let tableHeaderDone = false;

  const closeList = () => {
    if (listType) {
      html.push(listType === "ol" ? "</ol>" : "</ul>");
      listType = null;
    }
  };

  const closeTable = () => {
    if (inTable) {
      html.push("</tbody></table>");
      inTable = false;
      tableHeaderDone = false;
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.trim().startsWith("```")) {
      closeList();
      closeTable();
      if (!inFence) {
        inFence = true;
        fenceLines = [];
      } else {
        inFence = false;
        html.push(`<pre><code>${escapeHtml(fenceLines.join("\n"))}</code></pre>`);
      }
      continue;
    }

    if (inFence) {
      fenceLines.push(line);
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed) {
      closeList();
      closeTable();
      continue;
    }

    const admMatch = trimmed.match(/^!!!\s+(\w+)(?:\s+"([^"]*)")?/);
    if (admMatch) {
      closeList();
      closeTable();
      const admTitle = admMatch[2] || admMatch[1].toUpperCase();
      const admLines = [];
      while (i + 1 < lines.length && (lines[i + 1].startsWith("    ") || !lines[i + 1].trim())) {
        i++;
        if (lines[i].trim()) {
          admLines.push(renderInlineMarkdown(escapeHtml(lines[i].replace(/^ {4}/, ""))));
        }
      }
      html.push(
        `<div class="admonition"><div class="admonition-title">${escapeHtml(
          admTitle
        )}</div><div>${admLines.join("<br/>")}</div></div>`
      );
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      closeList();
      closeTable();
      const level = headingMatch[1].length;
      html.push(`<h${level}>${renderInlineMarkdown(escapeHtml(headingMatch[2]))}</h${level}>`);
      continue;
    }

    if (trimmed.startsWith(">")) {
      closeList();
      closeTable();
      html.push(
        `<blockquote>${renderInlineMarkdown(escapeHtml(trimmed.replace(/^>\s?/, "")))}</blockquote>`
      );
      continue;
    }

    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      closeList();
      const cells = trimmed
        .slice(1, -1)
        .split("|")
        .map((c) => c.trim());
      if (cells.every((c) => /^:?-{2,}:?$/.test(c))) {
        tableHeaderDone = true;
        continue;
      }
      if (!inTable) {
        inTable = true;
        tableHeaderDone = false;
        html.push(
          `<table><thead><tr>${cells
            .map((c) => `<th>${renderInlineMarkdown(escapeHtml(c))}</th>`)
            .join("")}</tr></thead><tbody>`
        );
      } else {
        html.push(
          `<tr>${cells
            .map((c) => `<td>${renderInlineMarkdown(escapeHtml(c))}</td>`)
            .join("")}</tr>`
        );
      }
      continue;
    }
    closeTable();

    const ulMatch = trimmed.match(/^[-*]\s+(.+)$/);
    if (ulMatch) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html.push("<ul>");
      }
      html.push(`<li>${renderInlineMarkdown(escapeHtml(ulMatch[1]))}</li>`);
      continue;
    }

    const olMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        html.push("<ol>");
      }
      html.push(`<li>${renderInlineMarkdown(escapeHtml(olMatch[1]))}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${renderInlineMarkdown(escapeHtml(trimmed))}</p>`);
  }

  closeList();
  closeTable();
  if (inFence) {
    html.push(`<pre><code>${escapeHtml(fenceLines.join("\n"))}</code></pre>`);
  }
  return html.join("\n");
}

function renderPreview() {
  const titleText = els.artTitle.value.trim() || "Tiêu đề bài viết";
  const bodyText = els.artContent.value;
  const headerHtml = `<h1>${escapeHtml(titleText)}</h1>`;
  if (!bodyText.trim()) {
    els.previewPane.innerHTML =
      headerHtml +
      `<div class="preview-empty-hint">Chưa có nội dung — mặc định bài viết hiển thị tiêu đề ở trên, bạn có thể tự viết nội dung Markdown ở khung bên trái.</div>`;
    return;
  }
  els.previewPane.innerHTML = headerHtml + renderMarkdownBody(bodyText);
}

async function loadTree() {
  const data = await api("/api/tree");
  state.tree = data;
  renderTopStatus(data);
  renderSidebar();
  renderDashboard();
  populateSectionSelect();
}

function renderTopStatus(data) {
  const v = data.validation;
  els.btnValidate.classList.remove("ok", "error");
  if (v.ok) {
    els.btnValidate.classList.add("ok");
    els.btnValidate.textContent = `${v.total_pages} trang hợp lệ`;
  } else {
    els.btnValidate.classList.add("error");
    els.btnValidate.textContent = `${v.errors.length} lỗi cấu trúc`;
  }

  if (data.zensical_available) {
    els.btnBuild.classList.remove("hidden");
  } else {
    els.btnBuild.classList.add("hidden");
  }
}

function renderSidebar() {
  const sections = state.tree?.sections || [];
  const q = state.searchQuery.trim().toLowerCase();
  els.treeContainer.innerHTML = "";

  if (!sections.length) {
    els.treeContainer.innerHTML = `<div class="loading">Chưa có mục nào.</div>`;
    return;
  }

  for (const sec of sections) {
    const secMatch = sec.title.toLowerCase().includes(q) || sec.slug.toLowerCase().includes(q);
    const matchingItems = sec.items.filter((item) => {
      if (!q || secMatch) return true;
      return (
        item.nav_title.toLowerCase().includes(q) ||
        item.title.toLowerCase().includes(q) ||
        item.path.toLowerCase().includes(q) ||
        (item.tags || []).some((t) => t.toLowerCase().includes(q))
      );
    });

    if (q && !secMatch && !matchingItems.length) {
      continue;
    }

    const secEl = document.createElement("div");
    secEl.className = "tree-section";

    const header = document.createElement("div");
    header.className = "tree-section-header";

    const left = document.createElement("div");
    left.className = "tree-section-left";

    const isCollapsed = !q && state.collapsed.has(sec.index);
    const chev = document.createElement("span");
    chev.className = "tree-chevron";
    chev.textContent = sec.type === "group" ? (isCollapsed ? "▸" : "▾") : "•";

    const titleSpan = document.createElement("span");
    titleSpan.className = "tree-section-title";
    titleSpan.textContent = sec.title;

    left.appendChild(chev);
    left.appendChild(titleSpan);

    if (sec.type === "group") {
      const countSpan = document.createElement("span");
      countSpan.className = "tree-count";
      countSpan.textContent = String(sec.items.length);
      left.appendChild(countSpan);
    }

    const actions = document.createElement("div");
    actions.className = "tree-actions";

    if (sec.type === "group") {
      const addBtn = makeMiniBtn("+", "Thêm bài viết vào mục này", (e) => {
        e.stopPropagation();
        openNewArticleEditor(sec.index);
      });
      actions.appendChild(addBtn);
    }

    actions.appendChild(
      makeMiniBtn("↑", "Di chuyển mục lên", (e) => {
        e.stopPropagation();
        moveSection(sec.index, "up");
      })
    );
    actions.appendChild(
      makeMiniBtn("↓", "Di chuyển mục xuống", (e) => {
        e.stopPropagation();
        moveSection(sec.index, "down");
      })
    );
    actions.appendChild(
      makeMiniBtn("✎", "Đổi tên mục", (e) => {
        e.stopPropagation();
        openRenameSectionModal(sec.index, sec.title);
      })
    );
    if (!sec.protected) {
      actions.appendChild(
        makeMiniBtn(
          "×",
          "Xóa mục",
          (e) => {
            e.stopPropagation();
            confirmDeleteSection(sec);
          },
          "danger"
        )
      );
    }

    header.appendChild(left);
    header.appendChild(actions);

    header.addEventListener("click", () => {
      if (sec.type === "page") {
        openEditArticleEditor(sec.path);
        return;
      }
      if (state.collapsed.has(sec.index)) {
        state.collapsed.delete(sec.index);
      } else {
        state.collapsed.add(sec.index);
      }
      renderSidebar();
    });

    secEl.appendChild(header);

    if (sec.type === "group" && !isCollapsed) {
      const itemsWrap = document.createElement("div");
      itemsWrap.className = "tree-items";
      for (const item of matchingItems) {
        const row = document.createElement("div");
        row.className = "tree-article";
        if (state.editor.mode === "edit" && state.editor.path === item.path) {
          row.classList.add("active");
        }

        const label = document.createElement("span");
        label.className = "tree-article-title";
        label.textContent = item.nav_title;
        label.title = `${item.title} (${item.path})`;
        row.appendChild(label);

        if (!item.has_content) {
          const emptyBadge = document.createElement("span");
          emptyBadge.className = "pill-empty";
          emptyBadge.textContent = "Chỉ tiêu đề";
          row.appendChild(emptyBadge);
        }

        const artActions = document.createElement("div");
        artActions.className = "tree-actions";
        artActions.appendChild(
          makeMiniBtn("↑", "Lên", (e) => {
            e.stopPropagation();
            moveArticle(item.path, "up");
          })
        );
        artActions.appendChild(
          makeMiniBtn("↓", "Xuống", (e) => {
            e.stopPropagation();
            moveArticle(item.path, "down");
          })
        );
        if (!item.protected) {
          artActions.appendChild(
            makeMiniBtn(
              "×",
              "Xóa bài viết",
              (e) => {
                e.stopPropagation();
                confirmDeleteArticle(item.path, item.nav_title);
              },
              "danger"
            )
          );
        }
        row.appendChild(artActions);

        row.addEventListener("click", () => openEditArticleEditor(item.path));
        itemsWrap.appendChild(row);
      }
      secEl.appendChild(itemsWrap);
    }

    els.treeContainer.appendChild(secEl);
  }
}

function makeMiniBtn(text, title, onClick, extraClass = "") {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = `mini-btn ${extraClass}`.trim();
  btn.textContent = text;
  btn.title = title;
  btn.addEventListener("click", onClick);
  return btn;
}

function renderDashboard() {
  if (!state.tree) return;
  const { stats, validation, sections } = state.tree;
  els.statSections.textContent = String(stats.total_sections);
  els.statArticles.textContent = String(stats.total_articles);
  els.statEmpty.textContent = String(stats.empty_articles);
  els.statValid.textContent = validation.ok ? "Hợp lệ" : `${validation.errors.length} lỗi`;
  els.statValid.style.color = validation.ok ? "var(--success)" : "var(--danger)";

  els.sectionsTableBody.innerHTML = "";
  for (const sec of sections) {
    const tr = document.createElement("tr");

    const tdTitle = document.createElement("td");
    const strong = document.createElement("strong");
    strong.textContent = sec.title;
    tdTitle.appendChild(strong);

    const tdType = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `badge ${sec.type === "group" ? "badge-group" : "badge-page"}`;
    badge.textContent = sec.type === "group" ? "Nhóm bài viết" : "Trang đơn";
    tdType.appendChild(badge);

    const tdPath = document.createElement("td");
    const code = document.createElement("code");
    code.textContent = sec.type === "group" ? `docs/${sec.slug}/` : `docs/${sec.path}`;
    tdPath.appendChild(code);

    const tdCount = document.createElement("td");
    tdCount.textContent = String(sec.items.length);

    const tdActions = document.createElement("td");
    tdActions.className = "col-actions";
    const rowBtns = document.createElement("div");
    rowBtns.className = "row-actions";

    if (sec.type === "group") {
      const btnAdd = document.createElement("button");
      btnAdd.type = "button";
      btnAdd.className = "btn btn-secondary btn-xs";
      btnAdd.textContent = "+ Bài viết";
      btnAdd.addEventListener("click", () => openNewArticleEditor(sec.index));
      rowBtns.appendChild(btnAdd);
    } else {
      const btnOpen = document.createElement("button");
      btnOpen.type = "button";
      btnOpen.className = "btn btn-secondary btn-xs";
      btnOpen.textContent = "Sửa nội dung";
      btnOpen.addEventListener("click", () => openEditArticleEditor(sec.path));
      rowBtns.appendChild(btnOpen);
    }

    const btnRename = document.createElement("button");
    btnRename.type = "button";
    btnRename.className = "btn btn-secondary btn-xs";
    btnRename.textContent = "Sửa mục";
    btnRename.addEventListener("click", () => openRenameSectionModal(sec.index, sec.title));
    rowBtns.appendChild(btnRename);

    const btnUp = document.createElement("button");
    btnUp.type = "button";
    btnUp.className = "btn btn-ghost btn-xs";
    btnUp.textContent = "↑";
    btnUp.title = "Di chuyển lên";
    btnUp.addEventListener("click", () => moveSection(sec.index, "up"));
    rowBtns.appendChild(btnUp);

    const btnDown = document.createElement("button");
    btnDown.type = "button";
    btnDown.className = "btn btn-ghost btn-xs";
    btnDown.textContent = "↓";
    btnDown.title = "Di chuyển xuống";
    btnDown.addEventListener("click", () => moveSection(sec.index, "down"));
    rowBtns.appendChild(btnDown);

    if (!sec.protected) {
      const btnDel = document.createElement("button");
      btnDel.type = "button";
      btnDel.className = "btn btn-danger btn-xs";
      btnDel.textContent = "Xóa";
      btnDel.addEventListener("click", () => confirmDeleteSection(sec));
      rowBtns.appendChild(btnDel);
    }

    tdActions.appendChild(rowBtns);
    tr.appendChild(tdTitle);
    tr.appendChild(tdType);
    tr.appendChild(tdPath);
    tr.appendChild(tdCount);
    tr.appendChild(tdActions);
    els.sectionsTableBody.appendChild(tr);
  }
}

function populateSectionSelect(selectedIndex = null, includeStandalone = false) {
  const sections = state.tree?.sections || [];
  els.artSection.innerHTML = "";
  for (const sec of sections) {
    if (!includeStandalone && sec.type !== "group") continue;
    const opt = document.createElement("option");
    opt.value = String(sec.index);
    opt.textContent = sec.title;
    els.artSection.appendChild(opt);
  }
  if (selectedIndex !== null) {
    els.artSection.value = String(selectedIndex);
  }
}

function showDashboard() {
  state.editor.mode = "closed";
  state.editor.path = null;
  els.editorView.classList.add("hidden");
  els.dashboardView.classList.remove("hidden");
  renderSidebar();
}

function openNewArticleEditor(preferredSectionIndex = null) {
  const groupSections = (state.tree?.sections || []).filter((s) => s.type === "group");
  if (!groupSections.length) {
    showToast("Hãy tạo ít nhất một mục nhóm trước khi thêm bài viết.", "warning");
    openCreateSectionModal();
    return;
  }

  state.editor = {
    mode: "new",
    path: null,
    protected: false,
    slugEdited: false,
  };

  els.editorModeBadge.className = "badge badge-new";
  els.editorModeBadge.textContent = "Bài viết mới";
  els.editorPathLabel.textContent = "Mặc định hiển thị tiêu đề, nội dung tự viết";
  els.btnDeleteArticle.classList.add("hidden");
  els.btnSaveArticle.textContent = "Tạo bài viết";

  populateSectionSelect(
    preferredSectionIndex !== null ? preferredSectionIndex : groupSections[0].index,
    false
  );
  els.artSection.disabled = false;
  els.artSlug.disabled = false;

  els.artTitle.value = "";
  els.artSlug.value = "";
  els.artNavTitle.value = "";
  els.chkSyncNavTitle.checked = true;
  els.artNavTitle.disabled = true;
  els.artTags.value = "";
  // Default: body content is empty so the article starts with title only
  els.artContent.value = "";

  els.dashboardView.classList.add("hidden");
  els.editorView.classList.remove("hidden");
  renderPreview();
  renderSidebar();
  els.artTitle.focus();
}

async function openEditArticleEditor(relPath) {
  try {
    const doc = await api(`/api/articles?path=${encodeURIComponent(relPath)}`);
    state.editor = {
      mode: "edit",
      path: doc.path,
      protected: Boolean(doc.protected),
      slugEdited: true,
    };

    const isStandalone = doc.item_index === null;
    populateSectionSelect(doc.section_index, isStandalone);
    els.artSection.disabled = isStandalone;
    els.artSlug.disabled = true;

    els.editorModeBadge.className = "badge badge-edit";
    els.editorModeBadge.textContent = "Chỉnh sửa";
    els.editorPathLabel.textContent = `docs/${doc.path}`;
    els.btnSaveArticle.textContent = "Lưu thay đổi";

    if (doc.protected) {
      els.btnDeleteArticle.classList.add("hidden");
    } else {
      els.btnDeleteArticle.classList.remove("hidden");
    }

    els.artTitle.value = doc.title;
    els.artSlug.value = doc.path.split("/").pop().replace(/\.md$/, "");
    els.artNavTitle.value = doc.nav_title;
    const synced = doc.nav_title === doc.title;
    els.chkSyncNavTitle.checked = synced;
    els.artNavTitle.disabled = synced;
    els.artTags.value = (doc.tags || []).join(", ");
    els.artContent.value = doc.content || "";

    els.dashboardView.classList.add("hidden");
    els.editorView.classList.remove("hidden");
    renderPreview();
    renderSidebar();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function saveArticle() {
  const title = els.artTitle.value.trim();
  if (!title) {
    showToast("Vui lòng nhập tiêu đề bài viết.", "error");
    els.artTitle.focus();
    return;
  }

  const navTitle = els.chkSyncNavTitle.checked
    ? title
    : els.artNavTitle.value.trim() || title;
  const tags = els.artTags.value;
  const content = els.artContent.value;
  const sectionIndex = Number(els.artSection.value);

  els.btnSaveArticle.disabled = true;
  try {
    if (state.editor.mode === "new") {
      const created = await api("/api/articles", {
        method: "POST",
        body: JSON.stringify({
          section_index: sectionIndex,
          title,
          nav_title: navTitle,
          slug: els.artSlug.value.trim() || null,
          tags,
          content,
        }),
      });
      await loadTree();
      showToast(`Đã tạo bài viết: docs/${created.path}`, "success");
      await openEditArticleEditor(created.path);
    } else if (state.editor.mode === "edit" && state.editor.path) {
      const updated = await api("/api/articles", {
        method: "PUT",
        body: JSON.stringify({
          path: state.editor.path,
          title,
          nav_title: navTitle,
          tags,
          content,
          target_section_index: els.artSection.disabled ? null : sectionIndex,
        }),
      });
      state.editor.path = updated.path;
      await loadTree();
      showToast(`Đã lưu bài viết: docs/${updated.path}`, "success");
      els.editorPathLabel.textContent = `docs/${updated.path}`;
      renderSidebar();
    }
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    els.btnSaveArticle.disabled = false;
  }
}

async function confirmDeleteArticle(relPath, label) {
  if (!window.confirm(`Xác nhận xóa bài viết "${label}" (docs/${relPath})?`)) {
    return;
  }
  try {
    const res = await api(`/api/articles?path=${encodeURIComponent(relPath)}`, {
      method: "DELETE",
    });
    if (state.editor.path === relPath) {
      showDashboard();
    }
    await loadTree();
    showToast(`Đã xóa bài viết "${res.deleted_title}".`, "success");
    if (res.warnings?.length) {
      showToast(`Cảnh báo liên kết cũ: ${res.warnings[0]}`, "warning");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function moveArticle(relPath, direction) {
  try {
    await api("/api/articles/move", {
      method: "POST",
      body: JSON.stringify({ path: relPath, direction }),
    });
    await loadTree();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openCreateSectionModal() {
  state.sectionModal = { mode: "create", sectionIndex: null, slugEdited: false };
  els.sectionModalTitle.textContent = "Thêm mục mới";
  els.secCreateFields.classList.remove("hidden");
  els.secTitle.value = "";
  els.secKind.value = "group";
  els.secSlug.value = "";
  els.secTags.value = "";
  els.sectionModal.classList.remove("hidden");
  els.secTitle.focus();
}

function openRenameSectionModal(sectionIndex, currentTitle) {
  state.sectionModal = { mode: "rename", sectionIndex, slugEdited: true };
  els.sectionModalTitle.textContent = "Đổi tên mục";
  els.secCreateFields.classList.add("hidden");
  els.secTitle.value = currentTitle;
  els.sectionModal.classList.remove("hidden");
  els.secTitle.focus();
}

function closeSectionModal() {
  els.sectionModal.classList.add("hidden");
}

async function submitSectionModal(e) {
  e.preventDefault();
  const title = els.secTitle.value.trim();
  if (!title) {
    showToast("Tên mục không được để trống.", "error");
    return;
  }

  try {
    if (state.sectionModal.mode === "create") {
      const created = await api("/api/sections", {
        method: "POST",
        body: JSON.stringify({
          title,
          kind: els.secKind.value,
          slug: els.secSlug.value.trim() || null,
          tags: els.secTags.value,
        }),
      });
      closeSectionModal();
      await loadTree();
      showToast(`Đã tạo mục "${created.title}" (docs/${created.path}).`, "success");
    } else {
      await api(`/api/sections/${state.sectionModal.sectionIndex}`, {
        method: "PUT",
        body: JSON.stringify({ title }),
      });
      closeSectionModal();
      await loadTree();
      showToast(`Đã đổi tên mục thành "${title}".`, "success");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function moveSection(sectionIndex, direction) {
  try {
    await api(`/api/sections/${sectionIndex}/move`, {
      method: "POST",
      body: JSON.stringify({ direction }),
    });
    await loadTree();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function confirmDeleteSection(sec) {
  const count = sec.items.length;
  const msg =
    sec.type === "group"
      ? `Xác nhận xóa mục "${sec.title}" cùng toàn bộ ${count} bài viết trong docs/${sec.slug}/?`
      : `Xác nhận xóa trang "${sec.title}" (docs/${sec.path})?`;
  if (!window.confirm(msg)) {
    return;
  }
  try {
    const res = await api(`/api/sections/${sec.index}`, { method: "DELETE" });
    if (state.editor.path && res.deleted_files.includes(state.editor.path)) {
      showDashboard();
    }
    await loadTree();
    showToast(`Đã xóa mục "${res.deleted_title}".`, "success");
    if (res.warnings?.length) {
      showToast(`Cảnh báo liên kết cũ: ${res.warnings[0]}`, "warning");
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openValidationModal() {
  const v = state.tree?.validation;
  if (!v) return;
  if (v.ok) {
    els.validationModalBody.innerHTML = `<p style="color:var(--success);font-weight:600">Tất cả ${v.total_pages} file Markdown và ${v.total_links} liên kết menu trong <code>zensical.toml</code> đều hợp lệ.</p>`;
  } else {
    const list = v.errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("");
    els.validationModalBody.innerHTML = `<p style="color:var(--danger);font-weight:600">Phát hiện ${v.errors.length} vấn đề:</p><ul class="validation-list">${list}</ul>`;
  }
  els.validationModal.classList.remove("hidden");
}

async function runZensicalBuild() {
  els.btnBuild.disabled = true;
  els.btnBuild.textContent = "Đang build...";
  try {
    const res = await api("/api/build", { method: "POST" });
    if (res.ok) {
      showToast("Zensical build --strict thành công!", "success");
    } else {
      showToast("Zensical build thất bại, xem chi tiết.", "error");
      els.validationModalBody.innerHTML = `<pre>${escapeHtml(
        (res.stderr || res.stdout || "Build lỗi").trim()
      )}</pre>`;
      els.validationModal.classList.remove("hidden");
    }
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    els.btnBuild.disabled = false;
    els.btnBuild.textContent = "Kiểm tra Build";
  }
}

function insertMarkdownSnippet(type) {
  const ta = els.artContent;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  const selected = ta.value.slice(start, end);
  let snippet = "";

  switch (type) {
    case "h2":
      snippet = `\n## ${selected || "Tiêu đề phần"}\n\n`;
      break;
    case "h3":
      snippet = `\n### ${selected || "Tiêu đề phụ"}\n\n`;
      break;
    case "bold":
      snippet = `**${selected || "chữ đậm"}**`;
      break;
    case "italic":
      snippet = `*${selected || "chữ nghiêng"}*`;
      break;
    case "code":
      snippet = `\`${selected || "command"}\``;
      break;
    case "fence":
      snippet = `\n\`\`\`bash\n${selected || "# nhập lệnh tại đây"}\n\`\`\`\n`;
      break;
    case "list":
      snippet = `\n- ${selected || "Mục 1"}\n- Mục 2\n`;
      break;
    case "table":
      snippet = `\n| Cột 1 | Cột 2 |\n| --- | --- |\n| Giá trị 1 | Giá trị 2 |\n`;
      break;
    case "admonition":
      snippet = `\n!!! note "Ghi chú"\n    ${selected || "Nội dung ghi chú"}\n`;
      break;
    default:
      return;
  }

  ta.setRangeText(snippet, start, end, "end");
  ta.focus();
  renderPreview();
}

function bindEvents() {
  els.btnDashboard.addEventListener("click", showDashboard);
  els.btnNewSection.addEventListener("click", openCreateSectionModal);
  els.btnDashNewSection.addEventListener("click", openCreateSectionModal);
  els.btnNewArticle.addEventListener("click", () => openNewArticleEditor());
  els.btnDashNewArticle.addEventListener("click", () => openNewArticleEditor());
  els.btnValidate.addEventListener("click", openValidationModal);
  els.btnBuild.addEventListener("click", runZensicalBuild);

  els.searchInput.addEventListener("input", () => {
    state.searchQuery = els.searchInput.value;
    renderSidebar();
  });

  els.btnCancelEdit.addEventListener("click", showDashboard);
  els.btnSaveArticle.addEventListener("click", saveArticle);
  els.btnDeleteArticle.addEventListener("click", () => {
    if (state.editor.path) {
      confirmDeleteArticle(state.editor.path, els.artNavTitle.value || state.editor.path);
    }
  });

  els.artTitle.addEventListener("input", () => {
    if (state.editor.mode === "new" && !state.editor.slugEdited) {
      els.artSlug.value = slugifyText(els.artTitle.value);
    }
    if (els.chkSyncNavTitle.checked) {
      els.artNavTitle.value = els.artTitle.value;
    }
    renderPreview();
  });

  els.artSlug.addEventListener("input", () => {
    state.editor.slugEdited = els.artSlug.value.trim().length > 0;
  });

  els.chkSyncNavTitle.addEventListener("change", () => {
    els.artNavTitle.disabled = els.chkSyncNavTitle.checked;
    if (els.chkSyncNavTitle.checked) {
      els.artNavTitle.value = els.artTitle.value;
    }
  });

  els.artContent.addEventListener("input", renderPreview);

  document.querySelectorAll(".tool-btn").forEach((btn) => {
    btn.addEventListener("click", () => insertMarkdownSnippet(btn.dataset.md));
  });

  document.querySelectorAll(".view-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".view-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      els.editorSplit.classList.remove("mode-split", "mode-edit", "mode-preview");
      els.editorSplit.classList.add(`mode-${btn.dataset.view}`);
    });
  });

  els.secTitle.addEventListener("input", () => {
    if (state.sectionModal.mode === "create" && !state.sectionModal.slugEdited) {
      els.secSlug.value = slugifyText(els.secTitle.value);
    }
  });
  els.secSlug.addEventListener("input", () => {
    state.sectionModal.slugEdited = els.secSlug.value.trim().length > 0;
  });

  els.sectionForm.addEventListener("submit", submitSectionModal);
  els.btnCloseSectionModal.addEventListener("click", closeSectionModal);
  els.btnCancelSectionModal.addEventListener("click", closeSectionModal);

  els.btnCloseValidationModal.addEventListener("click", () =>
    els.validationModal.classList.add("hidden")
  );
  els.btnDoneValidationModal.addEventListener("click", () =>
    els.validationModal.classList.add("hidden")
  );

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      if (state.editor.mode !== "closed") {
        e.preventDefault();
        saveArticle();
      }
    }
  });
}

(async function init() {
  bindEvents();
  try {
    const [meta] = await Promise.all([api("/api/meta"), loadTree()]);
    if (els.btnViewDocs && meta?.docs_url) {
      els.btnViewDocs.href = meta.docs_url;
    }
  } catch (err) {
    els.treeContainer.innerHTML = `<div class="loading">Lỗi tải dữ liệu: ${escapeHtml(
      err.message
    )}</div>`;
    showToast(err.message, "error");
  }
})();
