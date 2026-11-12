---
tags:
  - best-practices
  - production
---


# Production readiness checklist

Dùng checklist trước khi đưa một service vào production.

## Availability và rollout

- [ ] Có health/readiness endpoint kiểm chứng được.
- [ ] Có giới hạn tài nguyên và timeout rõ ràng.
- [ ] Có backup, restore test và kế hoạch RTO/RPO.
- [ ] Có rollback procedure; database migration tương thích.

## Security

- [ ] Secrets lấy từ hệ thống quản lý phù hợp.
- [ ] Least privilege, network policy và TLS hợp lệ.
- [ ] Không in PII/token trong log.
- [ ] Dependency scan và image scan đã chạy.

## Operability

- [ ] Metrics, log correlation và dashboard đã cấu hình.
- [ ] Alert có owner và link runbook.
- [ ] Document kiến trúc, dependency, change history.
- [ ] Có kịch bản kiểm thử failure hoặc recovery.

Điều kiện hoàn thành checklist phải được đánh giá theo mức độ quan trọng của service, không chỉ tick ô.
