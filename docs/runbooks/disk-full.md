---
tags:
  - runbook
  - linux
  - docker
---


# Runbook: filesystem gần đầy

## Thu thập bằng chứng trước khi xóa

```bash
df -h
df -i
sudo du -xhd1 /var 2>/dev/null | sort -h
sudo journalctl --disk-usage
docker system df
```

`df -i` giúp phát hiện hết inode dù còn dung lượng trống.

## Các hướng xử lý có kiểm soát

- Xác định log group/container/path chiếm dung lượng.
- Điều chỉnh log retention và rotation, kiểm tra ứng dụng spam log.
- Nếu cần dọn Docker build cache, kiểm tra thứ đang sử dụng trước.

```bash
docker image ls
docker volume ls
# Chỉ chạy sau khi đánh giá tác động:
docker builder prune
```

!!! danger "Tránh xóa dữ liệu khó khôi phục"
    Không chạy `docker system prune --volumes` hoặc `rm -rf` trên production khi chưa có kế hoạch backup và xác minh volume không cần thiết.

## Sau khôi phục

Tạo cảnh báo về dung lượng/inode, xác định tốc độ tăng và lập chính sách retention.
