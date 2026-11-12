---
hide:
  - toc
---

# DevOps Knowledge Base

**Tài liệu DevOps thực chiến bằng tiếng Việt** — thiết kế cho kỹ sư backend, cloud, SRE và người vận hành hệ thống.

Nội dung tổ chức theo trục **Hiểu cơ chế → Thực hành → Tối ưu → Xử lý sự cố**, tối ưu cho tra cứu khi làm việc thực tế, không lẫn với tài liệu Java/Spring riêng.

## Chọn chủ đề

| Nhóm | Bạn sẽ học / tra cứu |
| --- | --- |
| [Linux & WSL](linux-wsl/index.md) | CLI, services, network, WSL Ubuntu |
| [Git](git/index.md) | PR workflow, merge conflict |
| [Docker](docker/index.md) | Docker Engine, Dockerfile, Compose, debug |
| [Networking](networking/index.md) | DNS, TCP, TLS, certificates |
| [CI/CD](ci-cd/index.md) | GitHub Actions, release, rollback |
| [Kubernetes](kubernetes/index.md) | Pod, Deployment, Service, troubleshooting |
| [Terraform](terraform/index.md) | IaC, plan/apply, remote state |
| [AWS](aws/index.md) | IAM, VPC, CloudWatch, EventBridge |
| [Observability](observability/index.md) | Metrics, logs, traces, alerts |
| [Security](security/index.md) | Credentials, secrets, supply chain |
| [Best Practices](best-practices/index.md) | Production checklist, Docs as Code |
| [Runbooks](runbooks/index.md) | Deployment failed, disk full, port, TLS renewal |

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
zensical serve
```

!!! info "Quy ước tài liệu"
    Lệnh có tác động hạ tầng/production cần được thay placeholder bằng tài nguyên của bạn và review trước khi thực thi. Ví dụ được viết để học và tham khảo, không coi là cấu hình an toàn mặc định cho mọi môi trường.

**Đường đi đề xuất:** [Bắt đầu](getting-started/index.md) → [Docker](docker/index.md) → [CI/CD](ci-cd/index.md) → [Observability](observability/index.md).
