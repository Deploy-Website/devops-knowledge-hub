---
tags:
  - runbook
  - deployment
  - incident
---


# Runbook: deployment thất bại

**Mục tiêu:** khôi phục service nhanh và lưu lại bằng chứng cho hậu kiểm.

## 1. Xác định tác động

- Người dùng có bị ảnh hưởng không? Khu vực, version, bắt đầu lúc nào?
- Dashboard error rate, p95 latency, trạng thái health/ready.

## 2. Thu thập bằng chứng

```bash
kubectl rollout status deployment/my-api -n production --timeout=60s
kubectl get pods -n production -o wide
kubectl describe deployment/my-api -n production
kubectl get events -n production --sort-by=.lastTimestamp
```

## 3. Quyết định rollback

Nếu lỗi liên quan thay đổi mới và rollback an toàn về mặt dữ liệu:

```bash
kubectl rollout undo deployment/my-api -n production
kubectl rollout status deployment/my-api -n production --timeout=180s
```

Không rollback mù khi migration DB không tương thích hoặc sự cố hạ tầng đang diễn ra.

## 4. Xác minh

Kiểm tra alert hồi phục, synthetic test, traffic và error rate; ghi lại timeline, thay đổi, nguyên nhân và hành động phòng ngừa.

**Liên quan:** [Release strategy](../ci-cd/release.md).
