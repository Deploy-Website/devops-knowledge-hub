---
tags:
  - security
  - sbom
  - ci-cd
---


# Bảo vệ software supply chain

Đường đi từ source → dependency → build → artifact → runtime có nhiều điểm cần kiểm soát.

## Checklist

- Bảo vệ branch, yêu cầu code review, bật MFA cho account quan trọng.
- Pin version/digest của dependencies và actions khi phù hợp.
- Bật dependency scanning, secret scanning; đánh giá CVE theo mức phơi nhiễm.
- Tạo SBOM và lưu cùng release metadata.
- Build image không chạy root khi không cần thiết.
- Ký/verify artifact theo khả năng của registry và pipeline.
- Sử dụng OIDC cho pipeline kết nối cloud.

Để giảm rủi ro, không truyền `docker.sock` vào container không tin cậy.

Nguồn: [SLSA](https://slsa.dev/) · [OpenSSF](https://openssf.org/).
