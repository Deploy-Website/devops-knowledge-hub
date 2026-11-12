---
tags:
  - terraform
  - backend
  - security
---


# Terraform state và remote backend

State lưu ánh xạ resource Terraform với tài nguyên thực tế và có thể chứa thông tin nhạy cảm.

## Ví dụ backend S3

```hcl title="backend.tf"
terraform {
  backend "s3" {
    bucket       = "my-tf-state-bucket"
    key          = "dev/network/terraform.tfstate"
    region       = "ap-northeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

Các giá trị trên là placeholder. `use_lockfile` yêu cầu Terraform và S3 backend hỗ trợ thuộc tính này; kiểm tra phiên bản đang dùng trước khi áp dụng.

## Best practices

- S3 bucket bật versioning; hạn chế IAM access và ghi CloudTrail.
- Bật encryption, block public access và lifecycle/retention phù hợp.
- Mỗi môi trường có state riêng; không chạy song song hai apply vào cùng state.
- Backend không lưu credential trực tiếp trong HCL.
- `terraform state` commands có thể thay đổi state: backup và review trước.

Nguồn: [S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3).
