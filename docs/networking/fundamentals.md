---
tags:
  - dns
  - tcp
  - http
---


# Phân biệt lỗi DNS, TCP, HTTP

Một request phải đi qua nhiều lớp: phân giải hostname → tạo TCP connection → TLS (nếu HTTPS) → HTTP → ứng dụng.

```bash
getent ahosts example.com
curl -vI --connect-timeout 5 https://example.com
openssl s_client -connect example.com:443 -servername example.com </dev/null
```

| Dấu hiệu | Hướng điều tra |
| --- | --- |
| Không resolve tên | DNS resolver, VPN, suffix |
| Connection refused | Port không có listener hoặc bị reject |
| Connection timed out | Routing/firewall/proxy, đường truyền |
| TLS verify failed | CA trust, chain, tên miền, proxy inspection |
| HTTP 502/503 | Reverse proxy, upstream/healthcheck |

Không tắt certificate verification để giải quyết lỗi TLS; phải tìm đúng trust root hoặc sửa cấu hình certificate.

Nguồn: [RFC 9110 HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html).
