---
tags:
  - linux
  - cli
---


# Linux CLI, tiến trình và permission

## Kiểm tra hệ thống

```bash
pwd && ls -lah
whoami && id
ps aux --sort=-%mem | head
free -h
df -h
du -sh /var/log 2>/dev/null
```

## Quyền trên file

- `r` (read), `w` (write), `x` (execute) áp dụng cho owner/group/others.
- Permission của directory quyết định khả năng truy cập/duyệt tên file.
- Chỉ cấp quyền tối thiểu cần thiết, tránh `chmod -R 777`.

```bash
install -d -m 700 "$HOME/.ssh"
chmod 600 "$HOME/.ssh/config"  # nếu file tồn tại
stat -c '%a %U:%G %n' "$HOME/.ssh"
```

## Xử lý tiến trình

```bash
pgrep -af java
sudo ss -lntp | grep ':8080'
kill -TERM <PID>  # thay PID bằng tiến trình thực tế
```

Ưu tiên `SIGTERM` để ứng dụng shutdown có kiểm soát trước khi cân nhắc `SIGKILL`.

Nguồn: [GNU Coreutils](https://www.gnu.org/software/coreutils/manual/) · [Linux man-pages](https://man7.org/linux/man-pages/).
