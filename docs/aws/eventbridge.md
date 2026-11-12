---
tags:
  - aws
  - eventbridge
  - scheduler
---


# EventBridge Scheduler gọi Lambda

EventBridge Scheduler cần **execution role** mà service có quyền assume, và role đó cần quyền `lambda:InvokeFunction` đến target.

## Trust policy

```json title="trust-policy.json"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "scheduler.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
```

## Permission policy của role

```json title="invoke-policy.json"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "lambda:InvokeFunction",
    "Resource": "arn:aws:lambda:ap-northeast-1:111122223333:function:my-function"
  }]
}
```

## Debug `ValidationException`

```bash
aws iam get-role --role-name MySchedulerExecutionRole \
  --query 'Role.AssumeRolePolicyDocument'
aws iam list-role-policies --role-name MySchedulerExecutionRole
```

**Lưu ý:** trust policy đúng chưa đủ; caller tạo schedule cũng cần quyền phù hợp (bao gồm `iam:PassRole` với role target). Sử dụng condition để giới hạn ai có thể pass role.

Nguồn: [Scheduler execution role](https://docs.aws.amazon.com/scheduler/latest/UserGuide/setting-up.html).
