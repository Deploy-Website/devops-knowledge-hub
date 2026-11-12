---
tags:
  - terraform
  - iac
---


# Terraform: cấu hình hạ tầng dạng mã

Terraform quản lý tài nguyên theo **desired state** và state file. Thay đổi hạ tầng cần qua review giống code ứng dụng.

```hcl title="versions.tf"
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}
```

Đây chỉ là cấu hình khởi đầu; pin và nâng provider có kiểm thử theo phiên bản thực tế.

```bash
terraform fmt -check
terraform init
terraform validate
terraform plan -out=tfplan
# Chỉ thực hiện sau review và xác nhận account/region:
terraform apply tfplan
```

## Nguyên tắc

- Không commit state, `tfplan`, `.terraform/` hoặc credentials.
- Không dùng `terraform apply -auto-approve` cho production trừ khi có policy và pipeline kiểm soát.
- Review mục sẽ tạo/sửa/xóa trong `plan`, nhất là resource dữ liệu.

Nguồn: [Terraform CLI](https://developer.hashicorp.com/terraform/cli).
