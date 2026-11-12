---
tags:
  - kubernetes
  - yaml
  - deployment
---


# Kubernetes Deployment và Service

Ví dụ triển khai API đã có image trong registry. Thay `registry.example.com/my-api:1.0.0` bằng image thực tế trước khi áp dụng.

```yaml title="deployment.yaml"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
spec:
  replicas: 2
  selector:
    matchLabels: { app: my-api }
  template:
    metadata:
      labels: { app: my-api }
    spec:
      containers:
        - name: api
          image: registry.example.com/my-api:1.0.0
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet: { path: /health, port: 8080 }
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests: { cpu: 100m, memory: 256Mi }
            limits: { memory: 512Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: my-api
spec:
  selector: { app: my-api }
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

`/health` phải là endpoint thật, không yêu cầu login, phản ánh readiness của ứng dụng. Khi deploy:

```bash
kubectl apply --dry-run=server -f deployment.yaml
kubectl apply -f deployment.yaml
kubectl rollout status deployment/my-api --timeout=180s
```

Nguồn: [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/).
