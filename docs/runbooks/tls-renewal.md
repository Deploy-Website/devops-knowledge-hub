---
tags:
  - runbook
  - aws
  - tls
---


# Runbook: ACM certificate không tự gia hạn

## Xác minh tình trạng

```bash
aws acm describe-certificate \
  --certificate-arn 'arn:aws:acm:REGION:ACCOUNT:certificate/UUID' \
  --query 'Certificate.{Status:Status,Renewal:RenewalSummary,DomainValidation:DomainValidationOptions}'
```

## Kiểm tra DNS validation

1. Lấy chính xác CNAME Name/Value từ `DomainValidationOptions`.
2. Xác định DNS provider và authoritative zone thật của tên miền.
3. Dùng `dig` kiểm tra CNAME từ resolver tin cậy (và có thể truy vấn nameserver authoritative).
4. Đảm bảo CNAME không bị thay đổi bởi hệ thống tự động hay proxy DNS.
5. Kiểm tra certificate và tài nguyên đang sử dụng certificate.

```bash
dig +short CNAME _token.example.com
```

**Không** tạo CNAME bằng cách đoán token. Nếu CNAME đã có nhưng renewal lỗi, kiểm tra `RenewalStatusReason`, timing và yêu cầu trong tài liệu AWS.

Nguồn: [ACM managed renewal](https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html).
