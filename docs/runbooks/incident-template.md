---
tags:
  - runbook
  - template
---


# Template: Incident / Troubleshooting Note

Sao chép template bên dưới sang file riêng, ví dụ `docs/runbooks/2026-11-incident-api-timeout.md`, sau đó bổ sung mục menu nếu muốn.

```markdown
# Incident: <tên sự cố>

- Ngày/giờ (timezone):
- Môi trường / AWS account / region:
- Service liên quan:
- Severity / người phụ trách:
- Ảnh hưởng người dùng:

## Dấu hiệu và điều kiện kích hoạt

## Timeline

| Thời gian | Hành động | Kết quả |
| --- | --- | --- |

## Giả thuyết và bằng chứng

## Các bước xử lý đã thử

## Giải pháp cuối cùng / rollback

## Xác minh sau xử lý

## Nguyên nhân gốc (RCA) và phòng ngừa

## Nguồn tham khảo
```

!!! tip "Ghi cả phương án không hiệu quả"
    Việc ghi các bước thử nhưng thất bại giúp kỹ sư sau không lặp lại các thao tác rủi ro hoặc tốn thời gian.
