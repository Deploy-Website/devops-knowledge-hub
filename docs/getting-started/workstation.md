---
tags:
  - wsl
  - linux
  - tools
---


# Workstation DevOps trên WSL Ubuntu

Mục tiêu là có một môi trường Linux nhất quán dù editor chạy trên Windows.

## Cài các công cụ nền tảng

```bash
sudo apt update
sudo apt install -y git curl ca-certificates jq unzip python3 python3-venv
uname -a
git --version
python3 --version
```

Cài Docker, `kubectl`, Terraform và AWS CLI theo tài liệu chính thức, phù hợp kiến trúc CPU của máy; không chạy script tải từ Internet nếu chưa xác minh nguồn và checksum.

## Lưu dự án đúng filesystem

```bash
mkdir -p ~/workspace/devops
cd ~/workspace/devops
code .  # VS Code + WSL extension, khi đã tích hợp lệnh code
```

Ưu tiên `~/workspace/...` (filesystem Linux) thay vì `/mnt/c/...` đối với repository chạy nhiều thao tác file. Git và công cụ build sử dụng bản Linux để tránh khác biệt line endings, permission và file watcher.

## Bảo vệ thông tin đăng nhập

- Không commit `.env`, SSH private key, access key hoặc kubeconfig chứa token.
- Ưu tiên AWS IAM Identity Center/SSO, credential ngắn hạn và Git credential helper.
- Kiểm tra `git status` và `.gitignore` trước khi commit.

Xem thêm: [WSL development](../linux-wsl/wsl-development.md) và [Secrets](../security/secrets.md).
