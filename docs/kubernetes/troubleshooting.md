---
tags:
  - kubernetes
  - runbook
---


# Troubleshooting Kubernetes workload

## Nhìn tổng quan

```bash
kubectl get pods -n app -o wide
kubectl get events -n app --sort-by=.lastTimestamp
kubectl describe pod <pod> -n app
```

## CrashLoopBackOff

```bash
kubectl logs <pod> -n app --previous
kubectl logs <pod> -n app --all-containers --tail=100
```

Kiểm tra exception, env, ConfigMap/Secret, permission, image command, OOMKilled và probe config.

## Pending

Kiểm tra scheduler events, node resources, taints/tolerations, affinity và PVC.

## Service không có endpoint

```bash
kubectl get endpointslices -n app -l kubernetes.io/service-name=my-api
kubectl get pods -n app --show-labels
```

Selector của Service cần khớp label Pod; readiness chưa đạt cũng khiến traffic chưa tới Pod.

Nguồn: [Kubernetes debugging](https://kubernetes.io/docs/tasks/debug/).
