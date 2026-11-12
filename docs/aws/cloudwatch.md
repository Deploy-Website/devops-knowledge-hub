---
tags:
  - aws
  - cloudwatch
  - monitoring
---


# CloudWatch Logs, metrics và alarm

- **Logs:** lưu và tìm các bản ghi sự kiện.
- **Metrics:** số liệu có timestamp; dùng để lập dashboard và alarm.
- **Alarms:** đánh giá metric trong nhiều chu kỳ và kích hoạt action, ví dụ SNS.

## AWS CLI kiểm tra log group

```bash
aws logs describe-log-groups \
  --log-group-name-prefix '/aws/lambda/' \
  --region ap-northeast-1
```

## Quản trị chi phí

- Thiết lập retention cho log group (ví dụ 14, 30, 90 ngày theo chính sách).
- Giảm log debug không cần thiết trong production.
- Tránh high-cardinality custom metrics nếu không có yêu cầu giám sát cụ thể.
- Cân nhắc ingestion, storage, query và alarm pricing theo Region.

!!! tip "Cảnh báo có thể hành động"
    Alarm cần owner, cách xác minh, cách giảm thiểu và đường dẫn runbook; không chỉ gửi biểu đồ.

Nguồn: [CloudWatch concepts](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html).
