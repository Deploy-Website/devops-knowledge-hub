---
tags:
  - docker
  - troubleshooting
---


# Debug container không chạy hoặc không truy cập được

## 1. Xác định trạng thái

```bash
docker ps -a
docker logs --tail 100 <container-name>
docker inspect <container-name> --format '{{json .State}}'
```

## 2. Xác nhận publish port

```bash
docker port <container-name>
sudo ss -lntp | grep ':5433'
nc -vz 127.0.0.1 5433
```

`docker ps` hiển thị `5432/tcp` chỉ phản ánh port trong container; cần có dạng `127.0.0.1:5433->5432/tcp` khi muốn client trên host truy cập qua port 5433.

## 3. Kiểm tra healthcheck và mạng

```bash
docker inspect <container-name> --format '{{json .State.Health}}'
docker network ls
```

Nếu ứng dụng chỉ listen `127.0.0.1` **bên trong container**, container khác hoặc publish port có thể không tới được; với HTTP app thường listen `0.0.0.0` trong container nhưng chỉ publish `127.0.0.1` trên host nếu cần dùng local.

Xem thêm [runbook lỗi port](../runbooks/port-conflict.md).
