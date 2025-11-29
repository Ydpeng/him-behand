FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先安装系统依赖（PostgreSQL客户端库等）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装Python依赖（分步安装，先安装核心依赖）
RUN pip install --no-cache-dir \
    pydantic>=2.0.0 \
    requests>=2.31.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    python-multipart>=0.0.6 \
    psycopg2-binary>=2.9.0 \
    oss2>=2.18.0 \
    && pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data/feedback_labels

# 设置环境变量默认值
ENV DASHVECTOR_API_KEY=""
ENV DASHVECTOR_ENDPOINT=""
ENV DASHSCOPE_API_KEY=""
ENV OPENROUTER_API_KEY=""
ENV OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
ENV DEFAULT_MODEL="anthropic/claude-sonnet-4.5"
ENV POSTGRES_HOST=""
ENV POSTGRES_PORT=5432
ENV POSTGRES_DATABASE=""
ENV POSTGRES_USER=""
ENV POSTGRES_PASSWORD=""
ENV OSS_ACCESS_KEY_ID=""
ENV OSS_ACCESS_KEY_SECRET=""
ENV OSS_ENDPOINT=""
ENV OSS_REGION=""
ENV OSS_BUCKET_NAME=""

# 设置entrypoint脚本为可执行
RUN chmod +x /app/entrypoint.sh

# 暴露端口（如果需要）
EXPOSE 8000

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]

# 设置默认启动命令
CMD ["python", "astraflow/api.py"]