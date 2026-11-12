---
tags:
  - git
  - troubleshooting
---


# Xử lý merge conflict an toàn

## Tình huống

Cùng một block trong `application.yml` được thay đổi trên hai nhánh.

```bash
git status
git diff --name-only --diff-filter=U
git diff --check
```

Mở file xung đột, so sánh **ý định thay đổi** của cả hai bên, không mặc định chọn ours/theirs. Nếu đang trong merge, sau khi sửa:

```bash
git add path/to/application.yml
git status
git commit   # nếu Git chưa tự hoàn tất merge
```

Nếu đang rebase, dùng `git rebase --continue` thay vì `git commit` để tiếp tục quy trình rebase.

## Khi cần hủy

```bash
git merge --abort   # trong merge
git rebase --abort  # trong rebase
```

!!! warning "Không bỏ qua kiểm thử"
    Conflict đã hết chỉ xác nhận cú pháp Git, không xác nhận logic ứng dụng đúng. Chạy test, lint và build trước khi push.
