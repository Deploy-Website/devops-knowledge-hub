---
tags:
  - docker
  - postgresql
  - compose
---


# Docker Compose: PostgreSQL cho môi trường phát triển

Compose phù hợp chạy nhiều service liên quan trên máy dev và thiết lập volume bền vững.

```yaml title="compose.yaml"
services:
  postgres:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD}
    ports:
      - "127.0.0.1:5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  pgdata:
```

```bash
export POSTGRES_PASSWORD='replace-with-local-secret'
docker compose up -d
docker compose ps
docker compose exec postgres psql -U app -d appdb -c 'select version();'
```

`127.0.0.1:5433:5432`: **host port 5433** → **container port 5432**. Dùng `docker compose config` để kiểm tra cấu hình đã render (cẩn thận: có thể hiển thị secret); đừng chia sẻ output chứa mật khẩu.

!!! warning "Dữ liệu"
    `docker compose down -v` xóa volumes; tránh khi cần giữ dữ liệu. Dùng secret manager và cấu hình bảo mật phù hợp khi triển khai production.

Nguồn: [Compose specification](https://docs.docker.com/compose/compose-file/).
