---
tags:
  - slo
  - alerting
  - runbook
---


# Thiết kế alert có ý nghĩa

Alert tốt phản ánh **ảnh hưởng với người dùng**, có người chịu trách nhiệm và hành động rõ ràng.

## Ví dụ dịch vụ API

- Dashboard: request rate, error rate, p95 latency.
- SLO mẫu: 99.9% request thành công trong 30 ngày (cần định nghĩa tiêu chuẩn thành công rõ).
- Alert nhanh: error rate tăng mạnh kèm traffic đủ lớn.
- Alert chậm: burn rate tiêu thụ error budget liên tục.

Tránh alert dựa trên CPU 80% đơn lẻ nếu không phản ánh sự cố hoặc chưa có hướng xử lý.

## Template alert

| Trường | Giá trị ví dụ |
| --- | --- |
| Điều kiện | Error rate cao 10 phút |
| Ảnh hưởng | Người dùng nhận HTTP 5xx |
| Đầu mối | On-call backend |
| Dashboard | Link trang giám sát |
| Runbook | [Deploy failed](../runbooks/deployment-failed.md) |

Nguồn: [Google SRE workbook](https://sre.google/workbook/alerting-on-slos/).
