FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app/

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

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
CMD ["python", "start_api.py"]