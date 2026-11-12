---
tags:
  - git
  - workflow
---


# Git branching và pull request

## Quy trình đơn giản cho đội nhỏ

```bash
git switch main
git pull --ff-only
git switch -c feat/healthcheck
# Chỉnh sửa, chạy test
git add .
git diff --cached
git commit -m "feat: add health endpoint"
git push -u origin feat/healthcheck
```

Tạo pull request, yêu cầu review và CI xanh trước khi merge. Ưu tiên branch tồn tại ngắn, commit dễ kiểm tra và tránh force-push nhánh chia sẻ.

## Chọn merge strategy

| Strategy | Khi dùng |
| --- | --- |
| Squash merge | PR nhiều commit thử nghiệm, cần lịch sử đơn giản |
| Merge commit | Muốn lưu topology và quan hệ nhánh |
| Rebase | Làm sạch commit riêng trước khi chia sẻ |

Không rebase tùy tiện lịch sử chung đã có người khác dựa vào.

Nguồn: [Git book](https://git-scm.com/book/en/v2).
