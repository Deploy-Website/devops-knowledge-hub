---
tags:
  - documentation
  - zensical
  - best-practices
---


# Docs as Code với Zensical

Tài liệu được lưu cùng Git workflow: Markdown, review, kiểm tra link, build và publish.

## Cấu trúc chuẩn một bài viết

1. **Bối cảnh:** vấn đề, phạm vi, điều kiện tiên quyết.
2. **Cơ chế:** giải thích vì sao xảy ra.
3. **Thực hành:** lệnh và cấu hình có thể kiểm tra.
4. **Xác minh:** expected output và chỉ số thành công.
5. **Rollback/edge cases:** làm gì nếu sai.
6. **Nguồn:** liên kết official docs có phiên bản/ngày khi cần.

```text
my-topic.md
├── Bối cảnh
├── Cơ chế hoạt động
├── Các bước thực hiện
├── Kiểm tra kết quả
├── Troubleshooting
└── Nguồn tham khảo
```

Thêm trang Markdown trong `docs/`, sau đó cập nhật `nav` của `zensical.toml`. Kiểm tra `zensical build --strict` và script `scripts/validate_docs.py` trước khi merge.

Nguồn: [Zensical docs](https://zensical.org/docs/).
