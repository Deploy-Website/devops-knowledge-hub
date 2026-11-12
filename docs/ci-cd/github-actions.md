---
tags:
  - github-actions
  - ci-cd
---


# GitHub Actions: CI cơ bản cho Maven

File dưới đây chạy khi có push và pull request; giả sử repository là dự án Java có `mvnw`.

```yaml title=".github/workflows/ci.yml"
name: CI
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
          cache: maven
      - name: Test
        run: |
          chmod +x ./mvnw
          ./mvnw -B verify
```

## Mở rộng lên production

- Sử dụng OIDC federation khi workflow cần đăng nhập AWS; tránh lưu AWS access key dài hạn.
- Pin action SHA khi yêu cầu supply-chain security ở mức cao.
- Dùng environment protection rules cho production.
- Không cho workflow từ pull request không tin cậy truy cập deploy credentials.

Nguồn: [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
