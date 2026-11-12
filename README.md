# DevOps Knowledge Base — Zensical 0.1.1

Dự án docs **độc lập về DevOps**, nội dung tiếng Việt, sử dụng Zensical Modern. Có các phần Linux/WSL, Git, Docker, Networking, CI/CD, Kubernetes, Terraform, AWS, Observability, Security, Best Practices và Runbooks.

## Yêu cầu

- Python 3.11+ và `venv`.
- WSL Ubuntu, Linux hoặc macOS (có thể sử dụng Windows với lệnh kích hoạt venv tương ứng).
- Không cần cài Docker/Kubernetes/Terraform/AWS CLI để **build docs**. Chỉ cần công cụ tương ứng khi thực hành từng bài.

## Chạy project trên WSL Ubuntu

```bash
cd devops-zensical-docs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/validate_docs.py
zensical serve
```

Mở `http://127.0.0.1:8000/` từ browser.

## Kiểm tra production build

```bash
zensical build --strict
# output: site/
```

## Tùy biến

- Sửa menu trong `[project].nav` của `zensical.toml`.
- `theme.variant = "modern"` có thể đổi sang `classic`.
- Palette light/dark đã cấu hình; CSS bổ sung trong `docs/stylesheets/extra.css`.
- Tìm kiếm Zensical có sẵn, tags được bật và Mermaid/Admonitions đã cấu hình.
- Khi publish cần thêm `site_url` thực tế trong `[project]`, ví dụ `https://user.github.io/repository/`. URL không được đưa giá trị giả trong project để tránh canonical sai.

## Thêm bài viết mới

1. Tạo file Markdown trong đúng thư mục nhóm, ví dụ `docs/aws/my-topic.md`.
2. Thêm front matter `tags` và H1.
3. Thêm file vào `nav` trong `zensical.toml`.
4. Chạy `python scripts/validate_docs.py && zensical build --strict`.
5. Commit và tạo pull request; GitHub Actions sẽ xác minh build.

## Trang quản trị (Admin UI) & Trang hiển thị Docs

Dự án có sẵn trang quản trị web và trang hiển thị tài liệu viết bằng Python chuẩn (không cần cài thêm thư viện ngoài) để xem, thêm, sửa, xóa mục (`zensical.toml`) và bài viết (`docs/`):

```bash
python -m admin
# hoặc: python admin/app.py --port 8080 --docs-port 8000 --open
```

- **Trang quản trị (Admin):** `http://127.0.0.1:8080/`
- **Trang hiển thị Docs:** `http://127.0.0.1:8000/` (hoặc `http://127.0.0.1:8080/docs`)

Khi tạo mới mục hoặc bài viết, trang mặc định chỉ hiển thị tiêu đề (`# <Tiêu đề>`), phần nội dung để trống để bạn tự viết.

## Triển khai GitHub Pages

Dự án mặc định chỉ **validate**, không tự deploy. Khi có repo và URL thực:

1. Thiết lập `site_url` trong `zensical.toml` theo địa chỉ public.
2. Trong GitHub repository: Settings → Pages → Build and deployment → GitHub Actions.
3. Dùng workflow ví dụ trong `examples/github-pages.yml` (copy vào `.github/workflows/publish.yml`).
4. Bảo đảm repository/permissions đúng, thử publish trên nhánh test nếu cần.

## Ghi chú an toàn

Lệnh và cấu hình infrastructure trong tài liệu là ví dụ; placeholder như `ACCOUNT`, `example.com` hoặc image registry phải được thay bằng dữ liệu thật. Không chạy trực tiếp các lệnh thay đổi/xóa tài nguyên production khi chưa review tác động.

## Nguồn chính thức

- https://zensical.org/docs/
- https://zensical.org/docs/setup/navigation/
- https://zensical.org/docs/authoring/diagrams/
- https://zensical.org/docs/publish-your-site/
- https://pypi.org/project/zensical/
