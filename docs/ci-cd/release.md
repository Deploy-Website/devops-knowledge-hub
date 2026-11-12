---
tags:
  - deployment
  - rollback
  - ci-cd
---


# Release strategy và rollback

## Các cách triển khai

| Phương án | Đặc điểm |
| --- | --- |
| Rolling update | Thay dần instances, ít cần tăng tài nguyên |
| Blue/green | Hai môi trường độc lập, đổi traffic nhanh |
| Canary | Chuyển tỷ lệ traffic nhỏ, theo dõi trước khi mở rộng |

## Checklist trước release

- Đã có artifact được kiểm thử và tham chiếu bằng digest/tag bất biến.
- Database migration tương thích ngược (expand → migrate → contract).
- Health/readiness probe phù hợp, có đo error rate/latency.
- Xác định owner, cửa sổ triển khai và điểm quyết định rollback.

## Sau release

```bash
kubectl rollout status deployment/my-app -n production --timeout=180s
kubectl rollout history deployment/my-app -n production
# Khi cần rollback bản Deployment trước:
kubectl rollout undo deployment/my-app -n production
```

Rollback image **không tự rollback schema/data**; migration DB phải có kế hoạch riêng.
