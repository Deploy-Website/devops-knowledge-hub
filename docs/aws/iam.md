---
tags:
  - aws
  - iam
  - security
---


# AWS IAM và least privilege

IAM đánh giá yêu cầu dựa trên nhiều lớp: identity/resource policies, permissions boundary, SCP, session policies và explicit deny.

## Kiểm tra danh tính trước khi chạy lệnh

```bash
aws sts get-caller-identity
aws configure list
```

## Quy tắc sử dụng

- Ưu tiên IAM role hoặc IAM Identity Center cho người dùng.
- Không dùng root user hằng ngày; bật MFA và bảo vệ tài khoản.
- Giới hạn Resource và Condition thay vì dùng `"Resource": "*"` khi API hỗ trợ.
- Execution role của service phải có **trust policy** hợp lệ và quyền thực thi phù hợp; đó là hai phần riêng biệt.

!!! warning "Xác nhận AWS account và region"
    Trước script tự động có khả năng thay đổi/xóa tài nguyên, hiển thị account ID và region rồi yêu cầu review kế hoạch.

Nguồn: [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).
