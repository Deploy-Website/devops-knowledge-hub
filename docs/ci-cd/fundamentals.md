---
tags:
  - ci-cd
  - pipeline
---


# CI/CD fundamentals

**Continuous Integration:** kiểm tra từng thay đổi bằng build, lint, unit test và security checks.

**Continuous Delivery:** tạo artifact sẵn sàng triển khai; production có thể cần bước phê duyệt. **Continuous Deployment:** tự động đưa bản đạt kiểm tra ra production.

```mermaid
flowchart LR
  A[Pull request] --> B[Lint và test]
  B --> C[Build artifact]
  C --> D[Scan / SBOM]
  D --> E[Staging]
  E --> F[Approval hoặc policy]
  F --> G[Production]
  G --> H[Smoke test và monitor]
```

## Nguyên tắc cốt lõi

- Build một artifact bất biến, promote cùng artifact giữa môi trường.
- Tách quyền build và deploy; giới hạn production secrets.
- Tránh deploy khi test hoặc kiểm tra bảo mật thất bại.
- Có health check, timeout và rollback plan.
- Log pipeline không được in credential.

Xem [GitHub Actions](github-actions.md) và [release](release.md).
