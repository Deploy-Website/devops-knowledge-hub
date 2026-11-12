---
tags:
  - security
  - secrets
---


# Quản lý secrets trong DevOps

Secret bao gồm mật khẩu DB, API token, private key, signing key và credentials truy cập cloud.

## Nguyên tắc

1. Không commit secret vào Git hoặc Docker image.
2. Ưu tiên cấp credential ngắn hạn qua IAM role/OIDC.
3. Đặt secret trong secret manager có audit và rotation.
4. Phân quyền theo application, environment và mục đích cụ thể.
5. Không in biến môi trường chứa secret trong log CI.

```gitignore title=".gitignore"
.env
.env.*
!.env.example
*.pem
*.key
```

```dotenv title=".env.example"
# Không điền mật khẩu thật trong file mẫu
POSTGRES_PASSWORD=change-me-locally
```

Nếu secret bị lộ: **thu hồi/rotate ngay**, kiểm tra access logs, thay thế tại các service phụ thuộc. Chỉ xóa khỏi lịch sử Git không đủ vì credential có thể đã bị sao chép.

Nguồn: [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).
