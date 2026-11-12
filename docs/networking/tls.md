---
tags:
  - tls
  - certificate
  - dns
---


# TLS certificate và DNS validation

TLS xác thực danh tính server qua certificate chain; cấu hình certificate cần đúng hostname, chuỗi tin cậy và thời hạn hiệu lực.

## Kiểm tra certificate endpoint

```bash
openssl s_client -connect example.com:443 -servername example.com </dev/null
```

## Kiểm tra DNS CNAME của ACM

```bash
dig +short CNAME _validation-token.example.com
```

Với AWS Certificate Manager, nếu renewal dùng **DNS validation**, phải giữ record CNAME validation chính xác tại authoritative DNS; việc certificate gắn với Load Balancer không tự tạo DNS record nếu DNS không thuộc vùng được quản lý/tương ứng.

## Checklist

- Domain/SAN đúng.
- Certificate và intermediate chain hợp lệ.
- DNS validation CNAME còn tồn tại và resolve công khai.
- Clock hệ thống đúng; proxy SSL inspection có CA tin cậy.
- Certificate đang sử dụng bởi đúng endpoint/load balancer.

Nguồn: [ACM DNS validation](https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html).
