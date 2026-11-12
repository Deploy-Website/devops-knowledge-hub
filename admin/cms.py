"""Core CMS engine for managing sections (muc) and articles (bai viet) in Zensical docs."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import threading
import tomllib
import unicodedata
from urllib.parse import unquote, urlsplit


class CMSError(Exception):
    """Domain error with an HTTP-friendly status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def slugify(text: str) -> str:
    """Convert Vietnamese or ASCII text into a URL/filename-safe slug."""
    value = text.strip().replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "untitled"


def _toml_str(value: str) -> str:
    """Escape a Python string as a valid TOML basic string."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\f", "\\f")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def _skip_string(text: str, idx: int) -> int:
    """Advance index past a TOML basic/literal/multiline string starting at idx."""
    quote = text[idx]
    if text[idx : idx + 3] == quote * 3:
        delim = quote * 3
        pos = idx + 3
        while pos < len(text):
            if quote == '"' and text[pos] == "\\":
                pos += 2
                continue
            if text[pos : pos + 3] == delim:
                return pos + 3
            pos += 1
        raise CMSError("Không thể đọc chuỗi multiline trong zensical.toml", 500)

    pos = idx + 1
    while pos < len(text):
        ch = text[pos]
        if quote == '"' and ch == "\\":
            pos += 2
            continue
        if ch == quote:
            return pos + 1
        pos += 1
    raise CMSError("Không thể đọc chuỗi trong zensical.toml", 500)


def _find_nav_span(toml_text: str) -> tuple[int, int]:
    """Locate the exact character span of `nav = [...]` under `[project]`."""
    n = len(toml_text)
    i = 0
    in_project_table = False
    bracket_depth = 0
    line_start = True

    while i < n:
        ch = toml_text[i]

        if ch == "#" and bracket_depth == 0:
            nl = toml_text.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            line_start = True
            continue

        if ch in ('"', "'"):
            i = _skip_string(toml_text, i)
            line_start = False
            continue

        if line_start and ch in (" ", "\t"):
            i += 1
            continue

        if line_start and ch == "[" and bracket_depth == 0:
            # Table header line such as [project] or [[project.theme.palette]]
            end_line = toml_text.find("\n", i)
            header = toml_text[i : end_line if end_line != -1 else n].split("#", 1)[0].strip()
            in_project_table = header == "[project]"
            i = (end_line + 1) if end_line != -1 else n
            line_start = True
            continue

        if in_project_table and line_start and bracket_depth == 0:
            match = re.match(r"nav\s*=\s*\[", toml_text[i:])
            if match:
                start = i
                pos = i + match.end() - 1  # points to '['
                depth = 0
                while pos < n:
                    c = toml_text[pos]
                    if c == "#":
                        nl = toml_text.find("\n", pos)
                        pos = (nl + 1) if nl != -1 else n
                        continue
                    if c in ('"', "'"):
                        pos = _skip_string(toml_text, pos)
                        continue
                    if c == "[":
                        depth += 1
                    elif c == "]":
                        depth -= 1
                        if depth == 0:
                            return start, pos + 1
                    pos += 1
                raise CMSError("Cấu trúc `nav = [...]` trong zensical.toml không đóng ngoặc", 500)

        if ch == "\n":
            line_start = True
        else:
            line_start = False
        i += 1

    raise CMSError("Không tìm thấy cấu hình `nav = [...]` trong [project] của zensical.toml", 500)


def _format_nav_toml(nav_entries: list[dict]) -> str:
    """Serialize nav list using the project's existing zensical.toml style."""
    lines = ["nav = ["]
    for entry in nav_entries:
        for title, target in entry.items():
            if isinstance(target, str):
                lines.append(f"  {{ {_toml_str(title)} = {_toml_str(target)} }},")
            elif isinstance(target, list):
                lines.append(f"  {{ {_toml_str(title)} = [")
                for child in target:
                    for child_title, child_path in child.items():
                        lines.append(
                            f"    {{ {_toml_str(child_title)} = {_toml_str(child_path)} }},"
                        )
                lines.append("  ] },")
            else:
                raise CMSError(f"Kiểu mục nav không được hỗ trợ: {target!r}", 500)
    lines.append("]")
    return "\n".join(lines)


@dataclass
class ParsedDoc:
    """Structured representation of a Markdown document."""

    title: str
    content: str
    tags: list[str]
    extra_front_matter: list[str]


def parse_markdown_doc(raw: str, fallback_title: str = "") -> ParsedDoc:
    """Split front matter, H1 title, and body content from a Markdown file."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    tags: list[str] = []
    extra_front_matter: list[str] = []
    body_source = text

    if text.startswith("---\n"):
        end_idx = text.find("\n---\n", 4)
        closing_len = 5
        if end_idx == -1 and text.endswith("\n---"):
            end_idx = len(text) - 4
            closing_len = 4
        if end_idx != -1:
            fm_lines = text[4:end_idx].splitlines()
            body_source = text[end_idx + closing_len :]
            i = 0
            while i < len(fm_lines):
                line = fm_lines[i]
                stripped = line.strip()
                if stripped.startswith("tags:"):
                    rest = stripped[5:].strip()
                    if rest.startswith("[") and rest.endswith("]"):
                        for item in rest[1:-1].split(","):
                            cleaned = item.strip().strip("\"'")
                            if cleaned:
                                tags.append(cleaned)
                        i += 1
                    else:
                        i += 1
                        while i < len(fm_lines) and (
                            fm_lines[i].startswith("  ")
                            or fm_lines[i].startswith("\t")
                            or fm_lines[i].strip().startswith("-")
                        ):
                            item = fm_lines[i].strip()
                            if item.startswith("-"):
                                cleaned = item[1:].strip().strip("\"'")
                                if cleaned:
                                    tags.append(cleaned)
                            i += 1
                else:
                    extra_front_matter.append(line)
                    i += 1

    lines = body_source.splitlines()
    title = ""
    h1_index: int | None = None
    in_fence = False
    fence_marker = ""
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if not in_fence and line.startswith("# "):
            title = line[2:].strip()
            h1_index = idx
            break

    if h1_index is not None:
        before = [l for l in lines[:h1_index] if l.strip()]
        after = lines[h1_index + 1 :]
        body_lines = before + after
    else:
        title = fallback_title
        body_lines = lines

    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    content = "\n".join(body_lines)
    return ParsedDoc(
        title=title or fallback_title,
        content=content,
        tags=tags,
        extra_front_matter=extra_front_matter,
    )


def render_markdown_doc(
    title: str,
    content: str = "",
    tags: list[str] | None = None,
    extra_front_matter: list[str] | None = None,
) -> str:
    """Render a Markdown document. By default only writes the title if content is empty."""
    clean_title = title.strip()
    if not clean_title:
        raise CMSError("Tiêu đề bài viết không được để trống")

    clean_tags = [t.strip() for t in (tags or []) if t and t.strip()]
    extra = [l for l in (extra_front_matter or [])]
    while extra and not extra[0].strip():
        extra.pop(0)
    while extra and not extra[-1].strip():
        extra.pop()

    parts: list[str] = []
    if clean_tags or extra:
        fm = ["---"]
        fm.extend(extra)
        if clean_tags:
            fm.append("tags:")
            for tag in clean_tags:
                fm.append(f"  - {tag}")
        fm.append("---")
        parts.append("\n".join(fm))

    parts.append(f"# {clean_title}")

    clean_content = content.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if clean_content.strip():
        parts.append(clean_content.rstrip())

    return "\n\n".join(parts) + "\n"


def normalize_tags(raw_tags: object) -> list[str]:
    """Normalize tags from either a list or comma-separated string."""
    if raw_tags is None:
        return []
    if isinstance(raw_tags, str):
        items = [part.strip() for part in raw_tags.split(",")]
    elif isinstance(raw_tags, list):
        items = [str(part).strip() for part in raw_tags]
    else:
        raise CMSError("Định dạng tags không hợp lệ")

    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


class DocsCMS:
    """Thread-safe manager for `zensical.toml` navigation and `docs/` Markdown files."""

    PROTECTED_PATHS = {"index.md"}

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        self.docs_dir = (self.root / "docs").resolve()
        self.config_path = (self.root / "zensical.toml").resolve()
        self._lock = threading.RLock()

    def _safe_doc_path(self, rel_path: str) -> tuple[str, Path]:
        clean = rel_path.strip().replace("\\", "/").lstrip("/")
        if not clean or not clean.endswith(".md"):
            raise CMSError("Đường dẫn bài viết phải là file .md hợp lệ")
        resolved = (self.docs_dir / clean).resolve()
        if not resolved.is_relative_to(self.docs_dir):
            raise CMSError("Đường dẫn không hợp lệ (vượt ra ngoài thư mục docs/)", 403)
        normalized_rel = resolved.relative_to(self.docs_dir).as_posix()
        return normalized_rel, resolved

    def _read_config(self) -> tuple[str, dict]:
        if not self.config_path.is_file():
            raise CMSError("Không tìm thấy file zensical.toml", 500)
        text = self.config_path.read_text(encoding="utf-8")
        data = tomllib.loads(text)
        return text, data

    def _load_nav(self) -> list[dict]:
        _, data = self._read_config()
        nav = data.get("project", {}).get("nav", [])
        if not isinstance(nav, list):
            raise CMSError("Mục nav trong zensical.toml không hợp lệ", 500)
        return nav

    def _save_nav(self, nav_entries: list[dict]) -> None:
        text, _ = self._read_config()
        start, end = _find_nav_span(text)
        new_nav_block = _format_nav_toml(nav_entries)
        updated_text = text[:start] + new_nav_block + text[end:]
        try:
            tomllib.loads(updated_text)
        except tomllib.TOMLDecodeError as exc:
            raise CMSError(f"Lỗi kiểm tra cú pháp zensical.toml: {exc}", 500) from exc

        tmp_path = self.config_path.with_suffix(".toml.tmp")
        tmp_path.write_text(updated_text, encoding="utf-8", newline="\n")
        os.replace(tmp_path, self.config_path)

    def _infer_section_slug(self, title: str, items: list[dict]) -> str:
        for item in items:
            path = next(iter(item.values()))
            if "/" in path:
                return path.split("/", 1)[0]
        return slugify(title)

    def _all_nav_paths(self, nav: list[dict]) -> set[str]:
        paths: set[str] = set()
        for entry in nav:
            for val in entry.values():
                if isinstance(val, str):
                    paths.add(val)
                elif isinstance(val, list):
                    for child in val:
                        paths.update(child.values())
        return paths

    def _find_incoming_links(self, deleted_paths: set[str]) -> list[str]:
        """Find remaining Markdown files that still contain local links to deleted_paths."""
        warnings: list[str] = []
        if not deleted_paths:
            return warnings
        for md_file in sorted(self.docs_dir.rglob("*.md")):
            rel = md_file.relative_to(self.docs_dir).as_posix()
            if rel in deleted_paths:
                continue
            text = md_file.read_text(encoding="utf-8")
            text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
            for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
                url = match.group(1).strip().split(' "', 1)[0]
                parts = urlsplit(url)
                if parts.scheme or url.startswith(("//", "#", "mailto:")):
                    continue
                dest = unquote(parts.path)
                if not dest:
                    continue
                target = (md_file.parent / dest).resolve()
                if target.is_relative_to(self.docs_dir):
                    target_rel = target.relative_to(self.docs_dir).as_posix()
                    if target_rel in deleted_paths:
                        warnings.append(f"{rel} đang có liên kết tới {target_rel}")
        return warnings

    def get_tree(self) -> dict:
        """Return full navigation tree enriched with document metadata and validation."""
        with self._lock:
            _, cfg = self._read_config()
            proj = cfg.get("project", {})
            nav = proj.get("nav", [])
            if not isinstance(nav, list):
                raise CMSError("Mục nav trong zensical.toml không hợp lệ", 500)
            sections = []
            total_articles = 0
            empty_articles = 0

            for idx, entry in enumerate(nav):
                nav_title, target = next(iter(entry.items()))
                if isinstance(target, str):
                    meta = self._article_summary(nav_title, target)
                    total_articles += 1
                    if not meta["has_content"]:
                        empty_articles += 1
                    sections.append(
                        {
                            "index": idx,
                            "type": "page",
                            "title": nav_title,
                            "slug": target[:-3] if target.endswith(".md") else target,
                            "path": target,
                            "protected": target in self.PROTECTED_PATHS,
                            "items": [meta],
                        }
                    )
                elif isinstance(target, list):
                    items = []
                    for child_idx, child in enumerate(target):
                        child_title, child_path = next(iter(child.items()))
                        meta = self._article_summary(child_title, child_path)
                        meta["item_index"] = child_idx
                        items.append(meta)
                        total_articles += 1
                        if not meta["has_content"]:
                            empty_articles += 1
                    sections.append(
                        {
                            "index": idx,
                            "type": "group",
                            "title": nav_title,
                            "slug": self._infer_section_slug(nav_title, target),
                            "protected": False,
                            "items": items,
                        }
                    )

            validation = self.validate_docs()
            return {
                "site": {
                    "name": proj.get("site_name", "DevOps Knowledge Base"),
                    "description": proj.get("site_description", ""),
                    "copyright": proj.get("copyright", ""),
                },
                "sections": sections,
                "stats": {
                    "total_sections": len(sections),
                    "total_articles": total_articles,
                    "empty_articles": empty_articles,
                },
                "validation": validation,
                "zensical_available": shutil.which("zensical") is not None,
            }

    def _article_summary(self, nav_title: str, rel_path: str) -> dict:
        try:
            norm_path, file_path = self._safe_doc_path(rel_path)
        except CMSError:
            return {
                "nav_title": nav_title,
                "title": nav_title,
                "path": rel_path,
                "tags": [],
                "has_content": False,
                "exists": False,
                "protected": rel_path in self.PROTECTED_PATHS,
            }
        exists = file_path.is_file()
        if not exists:
            return {
                "nav_title": nav_title,
                "title": nav_title,
                "path": norm_path,
                "tags": [],
                "has_content": False,
                "exists": False,
                "protected": norm_path in self.PROTECTED_PATHS,
            }
        parsed = parse_markdown_doc(
            file_path.read_text(encoding="utf-8"), fallback_title=nav_title
        )
        return {
            "nav_title": nav_title,
            "title": parsed.title,
            "path": norm_path,
            "tags": parsed.tags,
            "has_content": bool(parsed.content.strip()),
            "exists": True,
            "protected": norm_path in self.PROTECTED_PATHS,
        }

    def create_section(
        self,
        title: str,
        slug: str | None = None,
        kind: str = "group",
        tags: list[str] | str | None = None,
        content: str = "",
        position: int | None = None,
    ) -> dict:
        """Create a new category (group) or top-level standalone page."""
        with self._lock:
            clean_title = title.strip()
            if not clean_title:
                raise CMSError("Tên mục không được để trống")
            if kind not in ("group", "page"):
                raise CMSError("Loại mục phải là 'group' hoặc 'page'")

            nav = self._load_nav()
            existing_titles = {next(iter(e.keys())).lower() for e in nav}
            if clean_title.lower() in existing_titles:
                raise CMSError(f"Mục '{clean_title}' đã tồn tại trong menu", 409)

            raw_slug = slug.strip() if slug and slug.strip() else clean_title
            clean_slug = slugify(raw_slug)
            clean_tags = normalize_tags(tags)
            existing_paths = self._all_nav_paths(nav)

            if kind == "group":
                rel_path = f"{clean_slug}/index.md"
                target_file = self.docs_dir / clean_slug / "index.md"
                if rel_path in existing_paths or target_file.exists():
                    raise CMSError(f"Thư mục hoặc file '{rel_path}' đã tồn tại", 409)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(
                    render_markdown_doc(clean_title, content=content, tags=clean_tags),
                    encoding="utf-8",
                    newline="\n",
                )
                new_entry = {clean_title: [{"Tổng quan": rel_path}]}
            else:
                rel_path = f"{clean_slug}.md"
                target_file = self.docs_dir / rel_path
                if rel_path in existing_paths or target_file.exists():
                    raise CMSError(f"File '{rel_path}' đã tồn tại", 409)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(
                    render_markdown_doc(clean_title, content=content, tags=clean_tags),
                    encoding="utf-8",
                    newline="\n",
                )
                new_entry = {clean_title: rel_path}

            if position is not None and 0 <= position <= len(nav):
                insert_idx = position
            elif nav and next(iter(nav[-1].values())) == "references.md":
                insert_idx = len(nav) - 1
            else:
                insert_idx = len(nav)

            nav.insert(insert_idx, new_entry)
            self._save_nav(nav)
            return {
                "index": insert_idx,
                "type": kind,
                "title": clean_title,
                "slug": clean_slug,
                "path": rel_path,
            }

    def update_section(self, section_index: int, title: str | None = None) -> dict:
        """Rename a section in zensical.toml nav."""
        with self._lock:
            nav = self._load_nav()
            if not (0 <= section_index < len(nav)):
                raise CMSError("Không tìm thấy mục cần sửa", 404)

            entry = nav[section_index]
            old_title, target = next(iter(entry.items()))
            new_title = title.strip() if title is not None else old_title
            if not new_title:
                raise CMSError("Tên mục không được để trống")

            for idx, other in enumerate(nav):
                if idx != section_index:
                    other_title = next(iter(other.keys()))
                    if other_title.lower() == new_title.lower():
                        raise CMSError(f"Mục '{new_title}' đã tồn tại trong menu", 409)

            nav[section_index] = {new_title: target}
            self._save_nav(nav)
            return {"index": section_index, "title": new_title}

    def move_section(self, section_index: int, direction: str) -> dict:
        """Move a section up or down in zensical.toml nav."""
        with self._lock:
            nav = self._load_nav()
            if not (0 <= section_index < len(nav)):
                raise CMSError("Không tìm thấy mục", 404)
            delta = -1 if direction == "up" else 1 if direction == "down" else 0
            if delta == 0:
                raise CMSError("Hướng di chuyển phải là 'up' hoặc 'down'")
            new_index = section_index + delta
            if not (0 <= new_index < len(nav)):
                return {"index": section_index, "moved": False}
            nav[section_index], nav[new_index] = nav[new_index], nav[section_index]
            self._save_nav(nav)
            return {"index": new_index, "moved": True}

    def delete_section(self, section_index: int) -> dict:
        """Delete a section from nav and remove its Markdown files."""
        with self._lock:
            nav = self._load_nav()
            if not (0 <= section_index < len(nav)):
                raise CMSError("Không tìm thấy mục cần xóa", 404)

            title, target = next(iter(nav[section_index].items()))
            paths_to_delete: list[str] = []
            if isinstance(target, str):
                paths_to_delete.append(target)
            elif isinstance(target, list):
                for child in target:
                    paths_to_delete.extend(child.values())

            if any(p in self.PROTECTED_PATHS for p in paths_to_delete):
                raise CMSError("Không thể xóa Trang chủ (index.md)", 400)

            deleted_set = set(paths_to_delete)
            warnings = self._find_incoming_links(deleted_set)

            nav.pop(section_index)
            self._save_nav(nav)

            dirs_to_check: set[Path] = set()
            for rel_path in paths_to_delete:
                _, file_path = self._safe_doc_path(rel_path)
                if file_path.is_file():
                    file_path.unlink()
                    if file_path.parent != self.docs_dir:
                        dirs_to_check.add(file_path.parent)

            for folder in dirs_to_check:
                if folder.is_dir() and not any(folder.iterdir()):
                    folder.rmdir()

            return {
                "deleted_title": title,
                "deleted_files": paths_to_delete,
                "warnings": warnings,
            }

    def get_article(self, rel_path: str) -> dict:
        """Read full article details for editing."""
        with self._lock:
            norm_path, file_path = self._safe_doc_path(rel_path)
            nav = self._load_nav()
            located = self._locate_path_in_nav(nav, norm_path)
            if located is None:
                raise CMSError(f"Không tìm thấy bài viết '{norm_path}' trong menu", 404)
            section_idx, item_idx, nav_title = located

            if not file_path.is_file():
                raise CMSError(f"Không tìm thấy file '{norm_path}' trên đĩa", 404)

            raw = file_path.read_text(encoding="utf-8")
            parsed = parse_markdown_doc(raw, fallback_title=nav_title)
            section_title = next(iter(nav[section_idx].keys()))
            return {
                "path": norm_path,
                "section_index": section_idx,
                "section_title": section_title,
                "item_index": item_idx,
                "nav_title": nav_title,
                "title": parsed.title,
                "tags": parsed.tags,
                "extra_front_matter": parsed.extra_front_matter,
                "content": parsed.content,
                "protected": norm_path in self.PROTECTED_PATHS,
            }

    def _locate_path_in_nav(
        self, nav: list[dict], norm_path: str
    ) -> tuple[int, int | None, str] | None:
        for sec_idx, entry in enumerate(nav):
            nav_title, target = next(iter(entry.items()))
            if isinstance(target, str) and target == norm_path:
                return sec_idx, None, nav_title
            if isinstance(target, list):
                for item_idx, child in enumerate(target):
                    child_title, child_path = next(iter(child.items()))
                    if child_path == norm_path:
                        return sec_idx, item_idx, child_title
        return None

    def create_article(
        self,
        section_index: int,
        title: str,
        nav_title: str | None = None,
        slug: str | None = None,
        tags: list[str] | str | None = None,
        content: str = "",
    ) -> dict:
        """Create a new article inside a group section.

        By default, `content` is empty so the created Markdown displays only `# <title>`.
        """
        with self._lock:
            clean_title = title.strip()
            if not clean_title:
                raise CMSError("Tiêu đề bài viết không được để trống")
            clean_nav_title = nav_title.strip() if nav_title and nav_title.strip() else clean_title

            nav = self._load_nav()
            if not (0 <= section_index < len(nav)):
                raise CMSError("Không tìm thấy mục được chọn", 404)

            sec_title, target = next(iter(nav[section_index].items()))
            if not isinstance(target, list):
                raise CMSError(
                    f"Mục '{sec_title}' là trang đơn, không thể thêm bài viết con", 400
                )

            folder_slug = self._infer_section_slug(sec_title, target)
            folder_dir = self.docs_dir / folder_slug
            folder_dir.mkdir(parents=True, exist_ok=True)

            explicit_slug = bool(slug and slug.strip())
            base_slug = slugify(slug.strip() if explicit_slug else clean_title)
            existing_paths = self._all_nav_paths(nav)

            candidate_slug = base_slug
            counter = 2
            while True:
                rel_path = f"{folder_slug}/{candidate_slug}.md"
                file_path = self.docs_dir / rel_path
                if rel_path not in existing_paths and not file_path.exists():
                    break
                if explicit_slug:
                    raise CMSError(f"Bài viết '{rel_path}' đã tồn tại", 409)
                candidate_slug = f"{base_slug}-{counter}"
                counter += 1

            clean_tags = normalize_tags(tags)
            markdown = render_markdown_doc(clean_title, content=content, tags=clean_tags)
            file_path.write_text(markdown, encoding="utf-8", newline="\n")

            target.append({clean_nav_title: rel_path})
            self._save_nav(nav)
            return {
                "path": rel_path,
                "section_index": section_index,
                "nav_title": clean_nav_title,
                "title": clean_title,
                "tags": clean_tags,
                "content": content.strip("\n"),
            }

    def update_article(
        self,
        rel_path: str,
        title: str | None = None,
        nav_title: str | None = None,
        tags: list[str] | str | None = None,
        content: str | None = None,
        target_section_index: int | None = None,
    ) -> dict:
        """Update an existing article's title, menu label, tags, content, or section."""
        with self._lock:
            norm_path, file_path = self._safe_doc_path(rel_path)
            nav = self._load_nav()
            located = self._locate_path_in_nav(nav, norm_path)
            if located is None:
                raise CMSError(f"Không tìm thấy bài viết '{norm_path}' trong menu", 404)
            sec_idx, item_idx, current_nav_title = located

            if not file_path.is_file():
                raise CMSError(f"Không tìm thấy file '{norm_path}'", 404)

            parsed = parse_markdown_doc(
                file_path.read_text(encoding="utf-8"), fallback_title=current_nav_title
            )
            new_title = title.strip() if title is not None else parsed.title
            if not new_title:
                raise CMSError("Tiêu đề bài viết không được để trống")
            new_nav_title = (
                nav_title.strip() if nav_title is not None else current_nav_title
            )
            if not new_nav_title:
                raise CMSError("Tên bài viết trên menu không được để trống")

            new_tags = parsed.tags if tags is None else normalize_tags(tags)
            new_content = parsed.content if content is None else content

            final_path = norm_path
            final_file = file_path
            final_sec_idx = sec_idx

            # Handle moving article to another group section if requested
            if (
                target_section_index is not None
                and target_section_index != sec_idx
                and item_idx is not None
            ):
                if norm_path in self.PROTECTED_PATHS:
                    raise CMSError("Không thể di chuyển Trang chủ", 400)
                if not (0 <= target_section_index < len(nav)):
                    raise CMSError("Mục đích không tồn tại", 404)
                dest_title, dest_target = next(iter(nav[target_section_index].items()))
                if not isinstance(dest_target, list):
                    raise CMSError(
                        f"Mục '{dest_title}' là trang đơn, không thể chuyển bài viết vào đây",
                        400,
                    )

                dest_folder = self._infer_section_slug(dest_title, dest_target)
                (self.docs_dir / dest_folder).mkdir(parents=True, exist_ok=True)
                stem = file_path.stem
                if stem == "index":
                    stem = slugify(new_title)
                existing_paths = self._all_nav_paths(nav)
                candidate = stem
                counter = 2
                while True:
                    candidate_rel = f"{dest_folder}/{candidate}.md"
                    candidate_file = self.docs_dir / candidate_rel
                    if candidate_rel not in existing_paths and not candidate_file.exists():
                        break
                    candidate = f"{stem}-{counter}"
                    counter += 1

                # Remove from old section list, add to destination section list
                _, old_target = next(iter(nav[sec_idx].items()))
                assert isinstance(old_target, list)
                old_target.pop(item_idx)
                dest_target.append({new_nav_title: candidate_rel})
                final_path = candidate_rel
                final_file = candidate_file
                final_sec_idx = target_section_index
            else:
                if item_idx is None:
                    nav[sec_idx] = {new_nav_title: norm_path}
                else:
                    _, sec_target = next(iter(nav[sec_idx].items()))
                    assert isinstance(sec_target, list)
                    sec_target[item_idx] = {new_nav_title: norm_path}

            rendered = render_markdown_doc(
                new_title,
                content=new_content,
                tags=new_tags,
                extra_front_matter=parsed.extra_front_matter,
            )
            final_file.write_text(rendered, encoding="utf-8", newline="\n")
            if final_file != file_path and file_path.is_file():
                file_path.unlink()

            self._save_nav(nav)
            return {
                "path": final_path,
                "section_index": final_sec_idx,
                "nav_title": new_nav_title,
                "title": new_title,
                "tags": new_tags,
                "content": new_content.replace("\r\n", "\n").strip("\n"),
            }

    def move_article(self, rel_path: str, direction: str) -> dict:
        """Move an article up or down within its section."""
        with self._lock:
            norm_path, _ = self._safe_doc_path(rel_path)
            nav = self._load_nav()
            located = self._locate_path_in_nav(nav, norm_path)
            if located is None:
                raise CMSError(f"Không tìm thấy bài viết '{norm_path}'", 404)
            sec_idx, item_idx, _ = located
            if item_idx is None:
                return self.move_section(sec_idx, direction)

            delta = -1 if direction == "up" else 1 if direction == "down" else 0
            if delta == 0:
                raise CMSError("Hướng di chuyển phải là 'up' hoặc 'down'")
            _, items = next(iter(nav[sec_idx].items()))
            assert isinstance(items, list)
            new_idx = item_idx + delta
            if not (0 <= new_idx < len(items)):
                return {"moved": False, "item_index": item_idx}
            items[item_idx], items[new_idx] = items[new_idx], items[item_idx]
            self._save_nav(nav)
            return {"moved": True, "item_index": new_idx}

    def delete_article(self, rel_path: str) -> dict:
        """Delete an article from zensical.toml nav and docs/."""
        with self._lock:
            norm_path, file_path = self._safe_doc_path(rel_path)
            if norm_path in self.PROTECTED_PATHS:
                raise CMSError("Không thể xóa Trang chủ (index.md)", 400)

            nav = self._load_nav()
            located = self._locate_path_in_nav(nav, norm_path)
            if located is None:
                raise CMSError(f"Không tìm thấy bài viết '{norm_path}' trong menu", 404)
            sec_idx, item_idx, nav_title = located

            warnings = self._find_incoming_links({norm_path})

            if item_idx is None:
                nav.pop(sec_idx)
            else:
                _, items = next(iter(nav[sec_idx].items()))
                assert isinstance(items, list)
                items.pop(item_idx)
                if not items:
                    nav.pop(sec_idx)

            self._save_nav(nav)
            if file_path.is_file():
                file_path.unlink()
                if file_path.parent != self.docs_dir and not any(file_path.parent.iterdir()):
                    file_path.parent.rmdir()

            return {
                "deleted_path": norm_path,
                "deleted_title": nav_title,
                "warnings": warnings,
            }

    def validate_docs(self) -> dict:
        """Run the same structural and link checks as scripts/validate_docs.py."""
        with self._lock:
            errors: list[str] = []
            nav = self._load_nav()
            md_files = sorted(self.docs_dir.rglob("*.md"))

            referenced: list[str] = []
            for entry in nav:
                for child in entry.values():
                    if isinstance(child, str):
                        referenced.append(child)
                    elif isinstance(child, list):
                        for item in child:
                            referenced.extend(item.values())

            for entry in referenced:
                if not (self.docs_dir / entry).is_file():
                    errors.append(f"Menu link missing: {entry}")

            listed = set(referenced)
            for file in md_files:
                relative = file.relative_to(self.docs_dir).as_posix()
                if relative not in listed:
                    errors.append(f"File missing from nav: {relative}")
                text = file.read_text(encoding="utf-8")
                text = re.sub(r"(?ms)^(```|~~~).*?^\1[^\n]*$", "", text)
                for match in re.finditer(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
                    url = match.group(1).strip().split(' "', 1)[0]
                    parts = urlsplit(url)
                    if parts.scheme or url.startswith(("//", "#", "mailto:")):
                        continue
                    dest = unquote(parts.path)
                    if not dest:
                        continue
                    local = (file.parent / dest).resolve()
                    if not local.is_relative_to(self.docs_dir):
                        errors.append(f"Link escapes docs root in {relative}: {url}")
                        continue
                    if not local.is_file():
                        errors.append(f"Broken link in {relative}: {url}")

            if len(referenced) != len(set(referenced)):
                errors.append("Duplicate menu targets")

            return {
                "ok": len(errors) == 0,
                "total_pages": len(md_files),
                "total_links": len(referenced),
                "errors": errors,
            }
