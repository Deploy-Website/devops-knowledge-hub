"use strict";

const docsState = {
  tree: null,
  meta: { admin_url: "/" },
  currentPath: "index.md",
  flatPages: [],
};

const dEls = {
  siteName: document.getElementById("siteName"),
  brandLink: document.getElementById("brandLink"),
  btnToggleMenu: document.getElementById("btnToggleMenu"),
  btnThemeToggle: document.getElementById("btnThemeToggle"),
  btnOpenAdmin: document.getElementById("btnOpenAdmin"),
  docsSearch: document.getElementById("docsSearch"),
  searchResults: document.getElementById("searchResults"),
  topTabs: document.getElementById("topTabs"),
  docsSidebar: document.getElementById("docsSidebar"),
  sidebarNav: document.getElementById("sidebarNav"),
  articleBody: document.getElementById("articleBody"),
  pagerNav: document.getElementById("pagerNav"),
  siteCopyright: document.getElementById("siteCopyright"),
  tocList: document.getElementById("tocList"),
};

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function slugId(text) {
  return String(text || "")
    .trim()
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "section";
}

function resolveDocLink(currentFilePath, rawHref) {
  const href = rawHref.trim();
  if (/^(https?:\/\/|mailto:|#)/i.test(href)) {
    return { external: !href.startsWith("#"), href };
  }
  const [pathPart, hashPart] = href.split("#", 2);
  if (!pathPart) {
    return { external: false, href: `#${hashPart || ""}` };
  }
  const baseDirParts = currentFilePath.split("/").slice(0, -1);
  for (const seg of pathPart.split("/")) {
    if (!seg || seg === ".") continue;
    if (seg === "..") {
      baseDirParts.pop();
    } else {
      baseDirParts.push(seg);
    }
  }
  const resolved = baseDirParts.join("/");
  return {
    external: false,
    docPath: resolved,
    hash: hashPart || "",
  };
}

function renderInline(escapedText, currentFilePath) {
  let out = escapedText;
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, rawHref) => {
    const cleanHref = rawHref.replace(/&amp;/g, "&").split(' "', 1)[0];
    const resolved = resolveDocLink(currentFilePath, cleanHref);
    if (resolved.external) {
      if (!/^https?:\/\//i.test(resolved.href) && !/^mailto:/i.test(resolved.href)) {
        return label;
      }
      return `<a href="${escapeHtml(resolved.href)}" target="_blank" rel="noopener">${label}</a>`;
    }
    if (resolved.docPath && resolved.docPath.endsWith(".md")) {
      const targetUrl = `?page=${encodeURIComponent(resolved.docPath)}${
        resolved.hash ? `#${escapeHtml(resolved.hash)}` : ""
      }`;
      return `<a href="${targetUrl}" data-doc-path="${escapeHtml(resolved.docPath)}">${label}</a>`;
    }
    return `<a href="${escapeHtml(resolved.href || "#")}">${label}</a>`;
  });
  return out;
}

function renderArticleMarkdown(markdown, currentFilePath) {
  const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  const headings = [];
  const usedIds = new Map();
  let inFence = false;
  let fenceLines = [];
  let listType = null;
  let inTable = false;

  const uniqueHeadingId = (title) => {
    const base = slugId(title);
    const count = (usedIds.get(base) || 0) + 1;
    usedIds.set(base, count);
    return count === 1 ? base : `${base}-${count}`;
  };

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
        html.push(
          `<div class="code-wrap"><button class="code-copy-btn" type="button">Copy</button><pre><code>${escapeHtml(
            fenceLines.join("\n")
          )}</code></pre></div>`
        );
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

    if (/^(-{3,}|\*{3,})$/.test(trimmed)) {
      closeList();
      closeTable();
      html.push("<hr/>");
      continue;
    }

    const admMatch = trimmed.match(/^!!!\s+(\w+)(?:\s+"([^"]*)")?/);
    if (admMatch) {
      closeList();
      closeTable();
      const admType = admMatch[1].toLowerCase();
      const admTitle = admMatch[2] || admMatch[1].toUpperCase();
      const admLines = [];
      while (i + 1 < lines.length && (lines[i + 1].startsWith("    ") || !lines[i + 1].trim())) {
        i++;
        if (lines[i].trim()) {
          admLines.push(renderInline(escapeHtml(lines[i].replace(/^ {4}/, "")), currentFilePath));
        }
      }
      html.push(
        `<div class="admonition ${escapeHtml(admType)}"><div class="admonition-title">${escapeHtml(
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
      const rawHeading = headingMatch[2];
      const id = uniqueHeadingId(rawHeading);
      if (level === 2 || level === 3) {
        headings.push({ level, text: rawHeading, id });
      }
      html.push(`<h${level} id="${id}">${renderInline(escapeHtml(rawHeading), currentFilePath)}</h${level}>`);
      continue;
    }

    if (trimmed.startsWith(">")) {
      closeList();
      closeTable();
      html.push(
        `<blockquote>${renderInline(escapeHtml(trimmed.replace(/^>\s?/, "")), currentFilePath)}</blockquote>`
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
        continue;
      }
      if (!inTable) {
        inTable = true;
        html.push(
          `<table><thead><tr>${cells
            .map((c) => `<th>${renderInline(escapeHtml(c), currentFilePath)}</th>`)
            .join("")}</tr></thead><tbody>`
        );
      } else {
        html.push(
          `<tr>${cells
            .map((c) => `<td>${renderInline(escapeHtml(c), currentFilePath)}</td>`)
            .join("")}</tr>`
        );
      }
      continue;
    }
    closeTable();

    const taskMatch = trimmed.match(/^[-*]\s+\[( |x|X)\]\s+(.+)$/);
    if (taskMatch) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html.push("<ul>");
      }
      const checked = taskMatch[1].toLowerCase() === "x" ? "checked" : "";
      html.push(
        `<li style="list-style:none"><input type="checkbox" disabled ${checked}/> ${renderInline(
          escapeHtml(taskMatch[2]),
          currentFilePath
        )}</li>`
      );
      continue;
    }

    const ulMatch = trimmed.match(/^[-*]\s+(.+)$/);
    if (ulMatch) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html.push("<ul>");
      }
      html.push(`<li>${renderInline(escapeHtml(ulMatch[1]), currentFilePath)}</li>`);
      continue;
    }

    const olMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        html.push("<ol>");
      }
      html.push(`<li>${renderInline(escapeHtml(olMatch[1]), currentFilePath)}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${renderInline(escapeHtml(trimmed), currentFilePath)}</p>`);
  }

  closeList();
  closeTable();
  if (inFence) {
    html.push(
      `<div class="code-wrap"><button class="code-copy-btn" type="button">Copy</button><pre><code>${escapeHtml(
        fenceLines.join("\n")
      )}</code></pre></div>`
    );
  }
  return { html: html.join("\n"), headings };
}

async function fetchJson(url) {
  const resp = await fetch(url);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
  return data;
}

function buildFlatPages(sections) {
  const list = [];
  for (const sec of sections) {
    for (const item of sec.items) {
      list.push({
        sectionIndex: sec.index,
        sectionTitle: sec.title,
        navTitle: item.nav_title,
        title: item.title,
        path: item.path,
        tags: item.tags || [],
      });
    }
  }
  return list;
}

function findActiveSection(path) {
  for (const sec of docsState.tree.sections) {
    if (sec.items.some((item) => item.path === path)) {
      return sec;
    }
  }
  return docsState.tree.sections[0] || null;
}

function renderNav() {
  const sections = docsState.tree.sections;
  const activeSection = findActiveSection(docsState.currentPath);

  dEls.topTabs.innerHTML = "";
  for (const sec of sections) {
    const firstPath = sec.items[0]?.path || "index.md";
    const a = document.createElement("a");
    a.className = "top-tab";
    if (activeSection && sec.index === activeSection.index) {
      a.classList.add("active");
    }
    a.href = `?page=${encodeURIComponent(firstPath)}`;
    a.textContent = sec.title;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      navigateTo(firstPath);
    });
    dEls.topTabs.appendChild(a);
  }

  dEls.sidebarNav.innerHTML = "";
  if (activeSection) {
    const groupTitle = document.createElement("div");
    groupTitle.className = "sidebar-group-title";
    groupTitle.textContent = activeSection.title;
    dEls.sidebarNav.appendChild(groupTitle);

    for (const item of activeSection.items) {
      const link = document.createElement("a");
      link.className = "sidebar-link";
      if (item.path === docsState.currentPath) {
        link.classList.add("active");
      }
      link.href = `?page=${encodeURIComponent(item.path)}`;
      link.textContent = item.nav_title;
      link.addEventListener("click", (e) => {
        e.preventDefault();
        navigateTo(item.path);
        dEls.docsSidebar.classList.remove("open");
      });
      dEls.sidebarNav.appendChild(link);
    }
  }
}

function renderPager(currentPath) {
  dEls.pagerNav.innerHTML = "";
  const idx = docsState.flatPages.findIndex((p) => p.path === currentPath);
  if (idx === -1) return;

  const prev = idx > 0 ? docsState.flatPages[idx - 1] : null;
  const next = idx < docsState.flatPages.length - 1 ? docsState.flatPages[idx + 1] : null;

  if (prev) {
    const a = document.createElement("a");
    a.className = "pager-link";
    a.href = `?page=${encodeURIComponent(prev.path)}`;
    a.innerHTML = `<span class="pager-dir">← Trước</span><span class="pager-title">${escapeHtml(
      prev.navTitle
    )}</span>`;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      navigateTo(prev.path);
    });
    dEls.pagerNav.appendChild(a);
  } else {
    dEls.pagerNav.appendChild(document.createElement("div"));
  }

  if (next) {
    const a = document.createElement("a");
    a.className = "pager-link";
    a.style.textAlign = "right";
    a.href = `?page=${encodeURIComponent(next.path)}`;
    a.innerHTML = `<span class="pager-dir">Tiếp theo →</span><span class="pager-title">${escapeHtml(
      next.navTitle
    )}</span>`;
    a.addEventListener("click", (e) => {
      e.preventDefault();
      navigateTo(next.path);
    });
    dEls.pagerNav.appendChild(a);
  }
}

async function loadArticle(relPath) {
  docsState.currentPath = relPath;
  renderNav();

  try {
    const doc = await fetchJson(`/api/articles?path=${encodeURIComponent(relPath)}`);
    document.title = `${doc.title} — ${docsState.tree.site?.name || "DevOps Knowledge Base"}`;

    const tagsHtml = (doc.tags || []).length
      ? `<div class="article-tags">${doc.tags
          .map((t) => `<span class="tag-pill">${escapeHtml(t)}</span>`)
          .join("")}</div>`
      : "";

    const breadcrumb = `<div class="article-breadcrumb">${escapeHtml(
      doc.section_title
    )} / ${escapeHtml(doc.nav_title)}</div>`;

    const rendered = renderArticleMarkdown(doc.content || "", doc.path);
    const emptyHint = !String(doc.content || "").trim()
      ? `<div class="empty-article-note">Bài viết này hiện mới có tiêu đề. Bạn có thể tự viết nội dung trong <a href="${escapeHtml(
          docsState.meta.admin_url || "/"
        )}">Trang quản trị</a>.</div>`
      : "";

    dEls.articleBody.innerHTML =
      breadcrumb +
      tagsHtml +
      `<h1>${escapeHtml(doc.title)}</h1>` +
      rendered.html +
      emptyHint;

    dEls.articleBody.querySelectorAll("a[data-doc-path]").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        navigateTo(link.dataset.docPath);
      });
    });

    dEls.articleBody.querySelectorAll(".code-copy-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const code = btn.parentElement.querySelector("code")?.textContent || "";
        try {
          await navigator.clipboard.writeText(code);
          btn.textContent = "Đã copy";
          setTimeout(() => {
            btn.textContent = "Copy";
          }, 1500);
        } catch {
          btn.textContent = "Lỗi";
        }
      });
    });

    dEls.tocList.innerHTML = "";
    for (const h of rendered.headings) {
      const li = document.createElement("li");
      if (h.level === 3) li.className = "toc-h3";
      const a = document.createElement("a");
      a.href = `#${h.id}`;
      a.textContent = h.text;
      li.appendChild(a);
      dEls.tocList.appendChild(li);
    }

    renderPager(doc.path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (err) {
    dEls.articleBody.innerHTML = `<h1>Không tải được bài viết</h1><p>${escapeHtml(
      err.message
    )}</p>`;
  }
}

function navigateTo(relPath, push = true) {
  if (push) {
    const url = new URL(window.location.href);
    url.searchParams.set("page", relPath);
    window.history.pushState({ page: relPath }, "", url.toString());
  }
  loadArticle(relPath);
}

function setupSearch() {
  dEls.docsSearch.addEventListener("input", () => {
    const q = dEls.docsSearch.value.trim().toLowerCase();
    if (!q) {
      dEls.searchResults.classList.add("hidden");
      return;
    }
    const matches = docsState.flatPages
      .filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.navTitle.toLowerCase().includes(q) ||
          p.sectionTitle.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      )
      .slice(0, 12);

    dEls.searchResults.innerHTML = "";
    if (!matches.length) {
      dEls.searchResults.innerHTML = `<div class="search-item"><div class="search-item-meta">Không tìm thấy kết quả</div></div>`;
    } else {
      for (const m of matches) {
        const a = document.createElement("a");
        a.className = "search-item";
        a.href = `?page=${encodeURIComponent(m.path)}`;
        a.innerHTML = `<div class="search-item-title">${escapeHtml(
          m.title
        )}</div><div class="search-item-meta">${escapeHtml(m.sectionTitle)} · ${escapeHtml(
          m.path
        )}</div>`;
        a.addEventListener("click", (e) => {
          e.preventDefault();
          dEls.searchResults.classList.add("hidden");
          dEls.docsSearch.value = "";
          navigateTo(m.path);
        });
        dEls.searchResults.appendChild(a);
      }
    }
    dEls.searchResults.classList.remove("hidden");
  });

  document.addEventListener("click", (e) => {
    if (!dEls.docsSearch.contains(e.target) && !dEls.searchResults.contains(e.target)) {
      dEls.searchResults.classList.add("hidden");
    }
  });
}

function setupTheme() {
  const saved = localStorage.getItem("docs_theme");
  if (saved === "dark") {
    document.body.classList.add("dark");
  }
  dEls.btnThemeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");
    localStorage.setItem(
      "docs_theme",
      document.body.classList.contains("dark") ? "dark" : "light"
    );
  });
}

(async function init() {
  setupTheme();
  setupSearch();

  dEls.btnToggleMenu.addEventListener("click", () => {
    dEls.docsSidebar.classList.toggle("open");
  });

  dEls.brandLink.addEventListener("click", (e) => {
    e.preventDefault();
    navigateTo("index.md");
  });

  window.addEventListener("popstate", () => {
    const page = new URLSearchParams(window.location.search).get("page") || "index.md";
    loadArticle(page);
  });

  try {
    const [meta, tree] = await Promise.all([fetchJson("/api/meta"), fetchJson("/api/tree")]);
    docsState.meta = meta;
    docsState.tree = tree;
    docsState.flatPages = buildFlatPages(tree.sections);

    dEls.siteName.textContent = tree.site?.name || "DevOps Knowledge Base";
    dEls.siteCopyright.textContent = tree.site?.copyright || "";
    dEls.btnOpenAdmin.href = meta.admin_url || "/";

    const initialPage =
      new URLSearchParams(window.location.search).get("page") ||
      docsState.flatPages[0]?.path ||
      "index.md";
    await loadArticle(initialPage);
  } catch (err) {
    dEls.articleBody.innerHTML = `<h1>Lỗi tải trang Docs</h1><p>${escapeHtml(
      err.message
    )}</p>`;
  }
})();
