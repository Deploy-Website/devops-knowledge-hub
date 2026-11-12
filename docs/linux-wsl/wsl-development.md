---
tags:
  - wsl
  - windows
---


# Phát triển và vận hành DevOps bằng WSL

Một cách triển khai thực tế: **VS Code trên Windows + source và toolchain trong WSL Ubuntu**.

## Kiểm tra từ PowerShell

```powershell
wsl --status
wsl -l -v
wsl -d Ubuntu
```

## Kiểm tra trong Ubuntu

```bash
cat /etc/os-release
ip -br address
command -v git docker python3
```

## Điều cần phân biệt

- **Windows localhost** và **WSL localhost** có thể kết nối khác nhau tùy NAT/mirrored networking và port forwarding.
- Docker Engine cài trực tiếp trong WSL không đồng nghĩa có Docker Desktop.
- Git nên thao tác cùng một checkout; hạn chế chạy đồng thời Git trên Windows và Linux tại `/mnt/c`.

Nếu website chạy ở WSL mà Windows không vào được, kiểm tra listener `0.0.0.0`/`127.0.0.1`, `wsl --status` và firewall trước khi mở cổng ra bên ngoài.

Nguồn: [Microsoft WSL networking](https://learn.microsoft.com/en-us/windows/wsl/networking).
