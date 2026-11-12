"""HTTP server and REST API for the DevOps Docs Hub Admin UI."""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlparse
import webbrowser

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admin.cms import CMSError, DocsCMS

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}


def make_handler(
    cms: DocsCMS,
    static_dir: Path = STATIC_DIR,
    mode: str = "admin",
    peer_url: str = "",
) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to a specific DocsCMS instance.

    mode: "admin" serves the admin UI at / and docs viewer at /docs;
          "docs" serves the read-only docs viewer at /.
    """

    class AdminRequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            sys.stderr.write(f"[{mode}] {self.address_string()} - {format % args}\n")

        def _send_bytes(
            self, status: int, content_type: str, data: bytes
        ) -> None:
            try:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _send_json(self, status: int, payload: dict) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status, "application/json; charset=utf-8", raw)

        def _read_json_body(self) -> dict:
            length_str = self.headers.get("Content-Length", "0")
            try:
                length = int(length_str)
            except ValueError as exc:
                raise CMSError("Content-Length không hợp lệ") from exc
            if length > 5 * 1024 * 1024:
                raise CMSError("Dữ liệu gửi lên quá lớn (tối đa 5MB)", 413)
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise CMSError("Dữ liệu JSON không hợp lệ") from exc
            if not isinstance(data, dict):
                raise CMSError("Payload JSON phải là object")
            return data

        def _serve_static(self, rel_name: str) -> None:
            target = (static_dir / rel_name).resolve()
            if not target.is_relative_to(static_dir.resolve()) or not target.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Không tìm thấy tài nguyên"})
                return
            mime = MIME_TYPES.get(target.suffix.lower(), "application/octet-stream")
            self._send_bytes(HTTPStatus.OK, mime, target.read_bytes())

        def _handle_error(self, exc: Exception) -> None:
            if isinstance(exc, CMSError):
                self._send_json(exc.status_code, {"error": exc.message})
            else:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"Lỗi hệ thống: {exc}"},
                )

        def _ensure_write_allowed(self) -> bool:
            if mode != "admin":
                self._send_json(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    {"error": "Trang hiển thị Docs chỉ hỗ trợ đọc. Vui lòng dùng Trang quản trị."},
                )
                return False
            return True

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            try:
                if path in ("/", "/index.html"):
                    self._serve_static("docs.html" if mode == "docs" else "index.html")
                    return
                if path in ("/docs", "/docs/", "/docs.html"):
                    self._serve_static("docs.html")
                    return
                if path in ("/styles.css", "/app.js", "/docs.css", "/docs.js"):
                    self._serve_static(path.lstrip("/"))
                    return
                if path == "/api/meta":
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "mode": mode,
                            "admin_url": peer_url if mode == "docs" else "/",
                            "docs_url": "/" if mode == "docs" else (peer_url or "/docs"),
                        },
                    )
                    return
                if path == "/api/tree":
                    self._send_json(HTTPStatus.OK, cms.get_tree())
                    return
                if path == "/api/validate":
                    self._send_json(HTTPStatus.OK, cms.validate_docs())
                    return
                if path == "/api/articles":
                    rel_path = (query.get("path") or [""])[0]
                    if not rel_path:
                        raise CMSError("Thiếu tham số path")
                    self._send_json(HTTPStatus.OK, cms.get_article(rel_path))
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "API không tồn tại"})
            except Exception as exc:  # noqa: BLE001
                self._handle_error(exc)

        def do_POST(self) -> None:  # noqa: N802
            if not self._ensure_write_allowed():
                return
            parsed = urlparse(self.path)
            path = parsed.path

            try:
                if path == "/api/build":
                    zensical_bin = shutil.which("zensical")
                    if not zensical_bin:
                        raise CMSError(
                            "Chưa tìm thấy lệnh 'zensical' trong môi trường Python hiện tại.",
                            400,
                        )
                    proc = subprocess.run(
                        [zensical_bin, "build", "--strict"],
                        cwd=cms.root,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=120,
                    )
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "ok": proc.returncode == 0,
                            "returncode": proc.returncode,
                            "stdout": proc.stdout,
                            "stderr": proc.stderr,
                        },
                    )
                    return

                data = self._read_json_body()

                if path == "/api/sections":
                    result = cms.create_section(
                        title=str(data.get("title", "")),
                        slug=data.get("slug"),
                        kind=str(data.get("kind", "group")),
                        tags=data.get("tags"),
                        content=str(data.get("content", "")),
                        position=data.get("position"),
                    )
                    self._send_json(HTTPStatus.CREATED, result)
                    return

                move_sec = re.fullmatch(r"/api/sections/(\d+)/move", path)
                if move_sec:
                    sec_idx = int(move_sec.group(1))
                    result = cms.move_section(sec_idx, str(data.get("direction", "")))
                    self._send_json(HTTPStatus.OK, result)
                    return

                if path == "/api/articles":
                    sec_raw = data.get("section_index")
                    if sec_raw is None:
                        raise CMSError("Vui lòng chọn mục cho bài viết")
                    result = cms.create_article(
                        section_index=int(sec_raw),
                        title=str(data.get("title", "")),
                        nav_title=data.get("nav_title"),
                        slug=data.get("slug"),
                        tags=data.get("tags"),
                        content=str(data.get("content", "")),
                    )
                    self._send_json(HTTPStatus.CREATED, result)
                    return

                if path == "/api/articles/move":
                    result = cms.move_article(
                        rel_path=str(data.get("path", "")),
                        direction=str(data.get("direction", "")),
                    )
                    self._send_json(HTTPStatus.OK, result)
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"error": "API không tồn tại"})
            except Exception as exc:  # noqa: BLE001
                self._handle_error(exc)

        def do_PUT(self) -> None:  # noqa: N802
            if not self._ensure_write_allowed():
                return
            parsed = urlparse(self.path)
            path = parsed.path

            try:
                data = self._read_json_body()

                sec_match = re.fullmatch(r"/api/sections/(\d+)", path)
                if sec_match:
                    sec_idx = int(sec_match.group(1))
                    result = cms.update_section(
                        section_index=sec_idx,
                        title=data.get("title"),
                    )
                    self._send_json(HTTPStatus.OK, result)
                    return

                if path == "/api/articles":
                    target_sec = data.get("target_section_index")
                    result = cms.update_article(
                        rel_path=str(data.get("path", "")),
                        title=data.get("title"),
                        nav_title=data.get("nav_title"),
                        tags=data.get("tags"),
                        content=data.get("content"),
                        target_section_index=(
                            int(target_sec) if target_sec is not None else None
                        ),
                    )
                    self._send_json(HTTPStatus.OK, result)
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"error": "API không tồn tại"})
            except Exception as exc:  # noqa: BLE001
                self._handle_error(exc)

        def do_DELETE(self) -> None:  # noqa: N802
            if not self._ensure_write_allowed():
                return
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            try:
                sec_match = re.fullmatch(r"/api/sections/(\d+)", path)
                if sec_match:
                    sec_idx = int(sec_match.group(1))
                    result = cms.delete_section(sec_idx)
                    self._send_json(HTTPStatus.OK, result)
                    return

                if path == "/api/articles":
                    rel_path = (query.get("path") or [""])[0]
                    if not rel_path:
                        raise CMSError("Thiếu tham số path")
                    result = cms.delete_article(rel_path)
                    self._send_json(HTTPStatus.OK, result)
                    return

                self._send_json(HTTPStatus.NOT_FOUND, {"error": "API không tồn tại"})
            except Exception as exc:  # noqa: BLE001
                self._handle_error(exc)

    return AdminRequestHandler


class ExclusiveHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that prevents silent port hijacking on Windows."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def create_server(
    host: str = "127.0.0.1",
    port: int = 8080,
    root: Path | str = DEFAULT_ROOT,
    docs_url: str = "",
) -> ThreadingHTTPServer:
    """Instantiate the admin ThreadingHTTPServer without starting its loop."""
    cms = DocsCMS(root)
    handler = make_handler(cms, mode="admin", peer_url=docs_url)
    return ExclusiveHTTPServer((host, port), handler)


def create_docs_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    root: Path | str = DEFAULT_ROOT,
    admin_url: str = "http://127.0.0.1:8080/",
) -> ThreadingHTTPServer:
    """Instantiate the read-only docs display ThreadingHTTPServer."""
    cms = DocsCMS(root)
    handler = make_handler(cms, mode="docs", peer_url=admin_url)
    return ExclusiveHTTPServer((host, port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trang quản trị và hiển thị tài liệu Python cho DevOps Docs Hub."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ bind (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Cổng trang quản trị (mặc định: 8080)")
    parser.add_argument(
        "--docs-port",
        type=int,
        default=8000,
        help="Cổng trang hiển thị Docs (mặc định: 8000; đặt 0 để tắt)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Thư mục gốc project chứa zensical.toml và docs/",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Tự động mở trình duyệt khi khởi động",
    )
    args = parser.parse_args(argv)

    admin_url = f"http://{args.host}:{args.port}/"
    docs_server: ThreadingHTTPServer | None = None
    docs_url = ""
    if args.docs_port > 0:
        docs_server = create_docs_server(
            host=args.host,
            port=args.docs_port,
            root=args.root,
            admin_url=admin_url,
        )
        docs_url = f"http://{args.host}:{docs_server.server_port}/"
        docs_thread = threading.Thread(target=docs_server.serve_forever, daemon=True)
        docs_thread.start()

    server = create_server(
        host=args.host,
        port=args.port,
        root=args.root,
        docs_url=docs_url or f"http://{args.host}:{args.port}/docs",
    )
    actual_admin_url = f"http://{args.host}:{server.server_port}/"
    print(f"Trang quản trị (Admin) đang chạy tại: {actual_admin_url}")
    if docs_url:
        print(f"Trang hiển thị Docs đang chạy tại:  {docs_url}")
    else:
        print(f"Trang hiển thị Docs đang chạy tại:  {actual_admin_url}docs")
    print("Nhấn Ctrl+C để dừng server.")
    if args.open:
        webbrowser.open(docs_url or actual_admin_url)
        webbrowser.open(actual_admin_url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
    finally:
        server.server_close()
        if docs_server is not None:
            docs_server.shutdown()
            docs_server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
