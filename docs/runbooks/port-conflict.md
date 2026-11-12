---
tags:
  - runbook
  - docker
  - wsl
---


# Runbook: Windows không vào được port Docker trong WSL

**Bối cảnh:** Docker daemon chạy trong Ubuntu WSL, container có dịch vụ PostgreSQL `5432`, Windows cần kết nối tới port `5433`.

## 1. Kiểm tra publish port trong WSL

```bash
docker ps --format 'table {{.Names}}	{{.Ports}}'
docker port postgres-dev
nc -vz 127.0.0.1 5433
```

Đúng hướng host-to-container là:

```text
127.0.0.1:5433->5432/tcp
```

Nếu là `127.0.0.1:5432->5433/tcp` thì đã đảo ngược mapping.

## 2. Kiểm tra Windows (PowerShell)

```powershell
Test-NetConnection 127.0.0.1 -Port 5433
wsl --status
```

## 3. Nếu WSL vào được nhưng Windows không vào được

Kiểm tra WSL NAT hay mirrored mode, forwarding của localhost, VPN/firewall và ứng dụng đang chiếm port Windows. Không mở firewall `0.0.0.0/0` chỉ để làm test thành công.

Nguồn: [WSL networking](https://learn.microsoft.com/en-us/windows/wsl/networking).
