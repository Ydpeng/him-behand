#!/bin/bash

# AstraFlow 构建和部署脚本

echo "========================================="
echo "AstraFlow Docker 构建和部署"
echo "========================================="
echo ""

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 版本: $(docker --version)${NC}"

# 读取镜像仓库配置
read -p "请输入阿里云镜像仓库地址 (例如: registry.cn-hangzhou.aliyuncs.com/your_namespace/astraflow): " REGISTRY_URL

if [ -z "$REGISTRY_URL" ]; then
    echo -e "${YELLOW}⚠️  未提供镜像仓库地址，仅构建本地镜像${NC}"
    IMAGE_NAME="astraflow:latest"
else
    IMAGE_NAME="$REGISTRY_URL:latest"
fi

# 构建镜像
echo ""
echo "开始构建Docker镜像..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker 构建失败${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 镜像构建成功: $IMAGE_NAME${NC}"

# 如果提供了镜像仓库地址，则推送镜像
if [ ! -z "$REGISTRY_URL" ]; then
    echo ""
    echo "推送镜像到阿里云镜像仓库..."
    
    # 检查是否已登录
    if ! docker info | grep -q "Registry: registry.cn-hangzhou.aliyuncs.com"; then
        echo -e "${YELLOW}⚠️  请先登录阿里云镜像仓库:${NC}"
        echo "docker login --username=your_username registry.cn-hangzhou.aliyuncs.com"
        echo ""
        read -p "按回车键继续（镜像将仅保存在本地）..."
    else
        docker push $IMAGE_NAME
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 镜像推送失败${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✓ 镜像推送成功${NC}"
        echo ""
        echo "镜像地址: $IMAGE_NAME"
    fi
fi

# 显示部署说明
echo ""
echo "========================================="
echo "部署说明"
echo "========================================="
echo ""
echo "1. 在SAE控制台创建应用"
echo "2. 使用镜像: $IMAGE_NAME"
echo "3. 配置环境变量:"
echo "   - DASHVECTOR_API_KEY"
echo "   - DASHSCOPE_API_KEY"
echo "   - OPENROUTER_API_KEY"
echo "   - POSTGRES_HOST, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_PASSWORD"
echo "   - OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_ENDPOINT, OSS_BUCKET_NAME"
echo ""
echo "详细部署指南请查看: deploy-saef.md"
echo ""
echo -e "${GREEN}✅ 构建和部署准备完成！${NC}"