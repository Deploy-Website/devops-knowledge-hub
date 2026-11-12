---
tags:
  - docker
  - java
  - best-practices
---


# Dockerfile multi-stage cho Spring Boot

Multi-stage build tách công cụ compile khỏi runtime, giúp image cuối gọn và hạn chế bề mặt tấn công.

```dockerfile title="Dockerfile"
# Ví dụ minh họa với Maven Wrapper đã có trong project
FROM eclipse-temurin:17-jdk AS build
WORKDIR /workspace
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN chmod +x mvnw
COPY src/ src/
RUN ./mvnw -B -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app
RUN useradd --system --uid 10001 appuser
COPY --from=build /workspace/target/*.jar /app/app.jar
USER 10001
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

**Điều kiện:** dự án có Maven Wrapper; `target/` chỉ sinh ra một JAR chạy được. Trong CI cần chạy test ở bước riêng trước khi đóng image.

```text title=".dockerignore"
.git
.idea
.vscode
node_modules
**/target
**/build
.env
```

## Tối ưu thêm

- Pin base image bằng digest khi yêu cầu reproducible build cao.
- Không đưa credential qua `ARG`/`ENV` tại build time; dùng secret mounts nếu cần.
- Dùng image scan và gắn tag bất biến (commit SHA) khi push registry.

Nguồn: [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/).
