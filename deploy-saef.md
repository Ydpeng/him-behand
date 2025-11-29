# AstraFlow SAE 部署指南

## 1. 构建Docker镜像

```bash
# 构建镜像
docker build -t astraflow:latest .

# 测试镜像
docker run -it --rm \
  -e DASHVECTOR_API_KEY="your_dashvector_api_key" \
  -e DASHSCOPE_API_KEY="your_dashscope_api_key" \
  -e OPENROUTER_API_KEY="your_openrouter_api_key" \
  astraflow:latest
```

## 2. 推送到镜像仓库

```bash
# 登录阿里云容器镜像服务
docker login --username=your_username registry.cn-hangzhou.aliyuncs.com

# 标记镜像
docker tag astraflow:latest registry.cn-hangzhou.aliyuncs.com/your_namespace/astraflow:latest

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/your_namespace/astraflow:latest
```

## 3. SAE 部署配置

### 环境变量配置示例：

```yaml
# SAE 应用配置
dashvector_api_key: "sk-your-dashvector-key"
dashvector_endpoint: "your-dashvector-endpoint"
dashscope_api_key: "sk-your-dashscope-key"
openrouter_api_key: "sk-or-v1-your-openrouter-key"
postgres_host: "pgm-your-postgres-instance.pg.rds.aliyuncs.com"
postgres_database: "your_database"
postgres_user: "your_username"
postgres_password: "your_password"
oss_access_key_id: "your_access_key_id"
oss_access_key_secret: "your_access_key_secret"
oss_endpoint: "https://oss-cn-region.aliyuncs.com"
oss_bucket_name: "your-bucket-name"
```

### SAE 部署 YAML 配置示例：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: astraflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app: astraflow
  template:
    metadata:
      labels:
        app: astraflow
    spec:
      containers:
      - name: astraflow
        image: registry.cn-hangzhou.aliyuncs.com/your_namespace/astraflow:latest
        ports:
        - containerPort: 8000
        env:
        - name: DASHVECTOR_API_KEY
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: dashvector_api_key
        - name: DASHSCOPE_API_KEY
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: dashscope_api_key
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: openrouter_api_key
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: postgres_host
        - name: POSTGRES_DATABASE
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: postgres_database
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: postgres_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: postgres_password
        - name: OSS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: oss_access_key_id
        - name: OSS_ACCESS_KEY_SECRET
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: oss_access_key_secret
        - name: OSS_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: oss_endpoint
        - name: OSS_BUCKET_NAME
          valueFrom:
            secretKeyRef:
              name: astraflow-secrets
              key: oss_bucket_name
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## 4. 健康检查配置

SAE 支持以下健康检查配置：

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 5. 监控和日志

- **日志收集**: SAE 自动收集容器标准输出日志
- **监控指标**: CPU、内存使用情况自动监控
- **自定义指标**: 可通过环境变量 `METRICS_PORT` 暴露自定义指标

## 6. 安全建议

1. 使用阿里云KMS加密敏感配置
2. 定期轮换API密钥
3. 配置网络访问控制
4. 启用日志审计
5. 使用最小权限原则配置数据库和OSS访问权限