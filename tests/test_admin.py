"""Unit and HTTP handler integration tests for the DevOps Docs Hub Admin CMS."""
from __future__ import annotations

import io
import json
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest

from admin.app import make_handler
from admin.cms import CMSError, DocsCMS, parse_markdown_doc, render_markdown_doc, slugify

REPO_ROOT = Path(__file__).resolve().parents[1]


class _FakeSocket:
    """In-memory socket wrapper for testing BaseHTTPRequestHandler without network."""

    def __init__(self, raw_request: bytes) -> None:
        self._rfile = io.BytesIO(raw_request)
        self._wfile = io.BytesIO()

    def makefile(self, mode: str, *args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        if "r" in mode:
            return self._rfile
        return self._wfile

    def sendall(self, data: bytes) -> None:
        self._wfile.write(data)

    def close(self) -> None:
        pass


class TestMarkdownAndSlug(unittest.TestCase):
    def test_slugify_vietnamese(self) -> None:
        self.assertEqual(slugify("Triển khai ArgoCD trên K8s"), "trien-khai-argocd-tren-k8s")
        self.assertEqual(slugify("Đường đi & Lộ trình"), "duong-di-lo-trinh")

    def test_render_default_title_only(self) -> None:
        md = render_markdown_doc("Bài viết mới")
        self.assertEqual(md, "# Bài viết mới\n")

    def test_parse_and_preserve_extra_front_matter(self) -> None:
        raw = "---\nhide:\n  - toc\ntags:\n  - devops\n  - aws\n---\n\n# Tiêu đề\n\nNội dung mẫu.\n"
        parsed = parse_markdown_doc(raw)
        self.assertEqual(parsed.title, "Tiêu đề")
        self.assertEqual(parsed.tags, ["devops", "aws"])
        self.assertEqual(parsed.extra_front_matter, ["hide:", "  - toc"])
        self.assertEqual(parsed.content, "Nội dung mẫu.")

        re_rendered = render_markdown_doc(
            parsed.title,
            content=parsed.content,
            tags=parsed.tags,
            extra_front_matter=parsed.extra_front_matter,
        )
        self.assertIn("hide:\n  - toc", re_rendered)
        self.assertIn("tags:\n  - devops\n  - aws", re_rendered)
        self.assertIn("# Tiêu đề\n\nNội dung mẫu.\n", re_rendered)


class TestDocsCMS(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copy2(REPO_ROOT / "zensical.toml", self.root / "zensical.toml")
        shutil.copytree(REPO_ROOT / "docs", self.root / "docs")
        self.cms = DocsCMS(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_section_and_article_crud_preserves_config(self) -> None:
        # 1. Create a new group section
        created_sec = self.cms.create_section("Helm & GitOps", tags=["helm", "gitops"])
        self.assertEqual(created_sec["slug"], "helm-gitops")
        index_file = self.root / "docs" / "helm-gitops" / "index.md"
        self.assertTrue(index_file.is_file())
        self.assertEqual(
            index_file.read_text(encoding="utf-8"),
            "---\ntags:\n  - helm\n  - gitops\n---\n\n# Helm & GitOps\n",
        )

        # 2. Rename the section
        self.cms.update_section(created_sec["index"], title="GitOps & Helm")

        # 3. Create an article with default empty content (displays title only)
        created_art = self.cms.create_article(
            section_index=created_sec["index"],
            title="Cài đặt ArgoCD",
        )
        self.assertEqual(created_art["path"], "helm-gitops/cai-dat-argocd.md")
        art_file = self.root / "docs" / created_art["path"]
        self.assertEqual(art_file.read_text(encoding="utf-8"), "# Cài đặt ArgoCD\n")

        # 4. Edit article to write custom content
        self.cms.update_article(
            rel_path=created_art["path"],
            title="Cài đặt ArgoCD Production",
            nav_title="ArgoCD Production",
            tags=["gitops", "argocd"],
            content="## Cài đặt\n\n```bash\nkubectl create namespace argocd\n```",
        )
        updated = self.cms.get_article(created_art["path"])
        self.assertEqual(updated["title"], "Cài đặt ArgoCD Production")
        self.assertEqual(updated["nav_title"], "ArgoCD Production")
        self.assertIn("kubectl create namespace argocd", updated["content"])

        # Validate structure & links
        validation = self.cms.validate_docs()
        self.assertTrue(validation["ok"], validation["errors"])

        # Ensure other zensical.toml sections and comments were preserved verbatim
        toml_text = (self.root / "zensical.toml").read_text(encoding="utf-8")
        self.assertIn("# DevOps Knowledge Base - Zensical 0.1.1", toml_text)
        self.assertIn("[project.theme]", toml_text)
        self.assertIn("[project.plugins.tags]", toml_text)
        parsed_toml = tomllib.loads(toml_text)
        self.assertEqual(parsed_toml["project"]["theme"]["variant"], "modern")

        # 5. Delete article
        del_art = self.cms.delete_article(created_art["path"])
        self.assertEqual(del_art["deleted_path"], created_art["path"])
        self.assertFalse(art_file.exists())

        # 6. Delete section
        del_sec = self.cms.delete_section(created_sec["index"])
        self.assertEqual(del_sec["deleted_title"], "GitOps & Helm")
        self.assertFalse((self.root / "docs" / "helm-gitops").exists())
        self.assertTrue(self.cms.validate_docs()["ok"])

    def test_move_article_between_sections_and_reorder(self) -> None:
        sec_a = self.cms.create_section("Mục A")
        sec_b = self.cms.create_section("Mục B")
        art = self.cms.create_article(sec_a["index"], "Bài viết chuyển mục")
        moved = self.cms.update_article(
            rel_path=art["path"],
            target_section_index=sec_b["index"],
        )
        self.assertTrue(moved["path"].startswith("muc-b/"))
        self.assertFalse((self.root / "docs" / art["path"]).exists())
        self.assertTrue((self.root / "docs" / moved["path"]).is_file())
        self.assertEqual(self.cms.move_article(moved["path"], "up")["moved"], True)
        self.assertTrue(self.cms.validate_docs()["ok"])

    def test_protected_home_cannot_be_deleted(self) -> None:
        with self.assertRaises(CMSError):
            self.cms.delete_article("index.md")
        with self.assertRaises(CMSError):
            self.cms.delete_section(0)


class TestAdminHTTPHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copy2(REPO_ROOT / "zensical.toml", self.root / "zensical.toml")
        shutil.copytree(REPO_ROOT / "docs", self.root / "docs")
        self.cms = DocsCMS(self.root)
        self.handler_cls = make_handler(self.cms)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _req(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b""
        lines = [f"{method} {path} HTTP/1.1", "Host: localhost", "Connection: close"]
        if body is not None:
            lines.append("Content-Type: application/json")
            lines.append(f"Content-Length: {len(payload)}")
        raw_req = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + payload

        fake_sock = _FakeSocket(raw_req)
        self.handler_cls(fake_sock, ("127.0.0.1", 12345), None)
        raw_resp = fake_sock._wfile.getvalue()
        head, _, resp_body = raw_resp.partition(b"\r\n\r\n")
        status_line = head.splitlines()[0].decode("ascii")
        status_code = int(status_line.split(" ")[1])
        text = resp_body.decode("utf-8")
        if b"application/json" in head:
            return status_code, json.loads(text)
        return status_code, text

    def test_http_crud_flow(self) -> None:
        status, html = self._req("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("DevOps Docs Hub", html)

        status, tree = self._req("GET", "/api/tree")
        self.assertEqual(status, 200)
        self.assertTrue(tree["validation"]["ok"])

        # Add section
        status, sec = self._req("POST", "/api/sections", {"title": "Platform Engineering"})
        self.assertEqual(status, 201)
        sec_idx = sec["index"]

        # Rename section
        status, renamed = self._req("PUT", f"/api/sections/{sec_idx}", {"title": "Platform Ops"})
        self.assertEqual(status, 200)
        self.assertEqual(renamed["title"], "Platform Ops")

        # Create article with default empty content (only title)
        status, art = self._req(
            "POST",
            "/api/articles",
            {"section_index": sec_idx, "title": "Internal Developer Portal"},
        )
        self.assertEqual(status, 201)
        self.assertEqual(art["content"], "")

        # Read article
        status, fetched = self._req("GET", f"/api/articles?path={art['path']}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["title"], "Internal Developer Portal")
        self.assertEqual(fetched["content"], "")

        # Update article with user-written content
        status, updated = self._req(
            "PUT",
            "/api/articles",
            {"path": art["path"], "content": "Nội dung do người dùng tự viết."},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["content"], "Nội dung do người dùng tự viết.")

        # Path traversal blocked
        status, _ = self._req("GET", "/api/articles?path=../zensical.toml")
        self.assertIn(status, (400, 403))

        # Delete article & section
        status, _ = self._req("DELETE", f"/api/articles?path={art['path']}")
        self.assertEqual(status, 200)
        status, _ = self._req("DELETE", f"/api/sections/{sec_idx}")
        self.assertEqual(status, 200)

        # Docs viewer route on admin server
        status, docs_html = self._req("GET", "/docs")
        self.assertEqual(status, 200)
        self.assertIn("DevOps Knowledge Base", docs_html)

    def test_docs_mode_is_read_only(self) -> None:
        docs_handler = make_handler(self.cms, mode="docs", peer_url="http://127.0.0.1:8080/")
        orig_handler = self.handler_cls
        self.handler_cls = docs_handler
        try:
            status, html = self._req("GET", "/")
            self.assertEqual(status, 200)
            self.assertIn("docs.js", html)

            status, meta = self._req("GET", "/api/meta")
            self.assertEqual(status, 200)
            self.assertEqual(meta["mode"], "docs")
            self.assertEqual(meta["admin_url"], "http://127.0.0.1:8080/")

            status, _ = self._req("POST", "/api/sections", {"title": "Blocked"})
            self.assertEqual(status, 405)
        finally:
            self.handler_cls = orig_handler


if __name__ == "__main__":
    unittest.main()
