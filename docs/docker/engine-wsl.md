---
tags:
  - docker
  - wsl
---


# Docker Engine trực tiếp trong WSL Ubuntu

Mô hình: Docker CLI và daemon chạy trong WSL; browser/IDE trên Windows truy cập qua kết nối localhost theo cơ chế mạng hiện hành.

## Kiểm tra Docker Engine đã cài

```bash
docker version
docker info
docker compose version
```

Nếu chưa cài, thực hiện theo [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) và [Linux post-install](https://docs.docker.com/engine/install/linux-postinstall/). Không trộn package `docker.io` cũ với bộ `docker-ce` khi không có kế hoạch chuyển đổi.

## Dùng service trong WSL

Với WSL đã bật systemd:

```bash
sudo systemctl enable --now docker
sudo systemctl status docker --no-pager
```

Thêm user vào group `docker` làm user đó có quyền tương đương root đối với Docker daemon: chỉ làm trong môi trường tin cậy.

## Kiểm tra kết nối

```bash
docker run --rm hello-world
docker ps
```

!!! note "Không bắt buộc Docker Desktop"
    Cấu hình này phục vụ máy phát triển chỉ cần Docker Engine trong Ubuntu. Không bật remote Docker TCP daemon không có xác thực/TLS.
