#!/bin/bash

# AstraFlow Docker Entrypoint Script

echo "========================================="
echo "AstraFlow Container Startup"
echo "========================================="
echo ""

# 检查必要的环境变量
if [ -z "$DASHVECTOR_API_KEY" ]; then
    echo "⚠️  警告: DASHVECTOR_API_KEY 未设置"
fi

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "⚠️  警告: DASHSCOPE_API_KEY 未设置"
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  警告: OPENROUTER_API_KEY 未设置"
fi

# 检查PostgreSQL配置
if [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_DATABASE" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    echo "⚠️  警告: PostgreSQL配置不完整"
fi

# 检查OSS配置
if [ -z "$OSS_ACCESS_KEY_ID" ] || [ -z "$OSS_ACCESS_KEY_SECRET" ] || [ -z "$OSS_ENDPOINT" ] || [ -z "$OSS_BUCKET_NAME" ]; then
    echo "⚠️  警告: OSS配置不完整"
fi

echo ""
echo "环境变量配置:"
echo "- DASHVECTOR_API_KEY: ${DASHVECTOR_API_KEY:0:10}..."
echo "- DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY:0:10}..."
echo "- OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:10}..."
echo "- POSTGRES_HOST: $POSTGRES_HOST"
echo "- OSS_ENDPOINT: $OSS_ENDPOINT"
echo ""

# 创建数据目录
mkdir -p /app/data/feedback_labels

# 设置Python路径
export PYTHONPATH=/app:$PYTHONPATH

echo "启动AstraFlow API服务..."
echo "========================================="

# 检查是否安装了FastAPI依赖
echo "检查FastAPI依赖..."
if python -c "import fastapi" 2>/dev/null; then
    echo "✓ FastAPI依赖已安装"
else
    echo "⚠️  FastAPI依赖未安装，正在安装..."
    pip install fastapi uvicorn
    echo "✓ FastAPI依赖安装完成"
fi

echo ""
echo "启动AstraFlow API服务器..."
echo "========================================="

# 执行默认命令
if [ $# -eq 0 ]; then
    # 如果没有传入参数，直接运行 api.py 文件
    # 这样确保所有的 FastAPI 路由都被正确加载
    echo "直接运行 astraflow/api.py..."
    # 设置Python路径，确保模块导入正确
    export PYTHONPATH=/app:$PYTHONPATH
    exec python astraflow/api.py
else
    # 执行传入的命令
    exec "$@"
fi