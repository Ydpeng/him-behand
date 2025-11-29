#!/usr/bin/env python3
"""
AstraFlow API Server Startup Script

This script starts the FastAPI server with proper configuration
for production deployment.
"""

import os
import sys
import uvicorn
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_required_env_vars():
    """检查必要的环境变量"""
    required_vars = [
        'DASHVECTOR_API_KEY',
        'DASHSCOPE_API_KEY',
        'OPENROUTER_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True

def main():
    """启动API服务器"""
    logger.info("Starting AstraFlow API Server...")
    
    # 检查环境变量
    if not check_required_env_vars():
        logger.warning("Some required environment variables are missing")
        logger.warning("Server will start but some features may not work properly")
    
    # 获取主机和端口配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Server configured to run on {host}:{port}")
    logger.info("Starting uvicorn server...")
    
    # 直接导入并运行 api.py 中的 app
    # 这样确保所有的 FastAPI 路由和配置都被正确加载
    from astraflow.api import app
    
    # 启动 uvicorn 服务器
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # 生产环境禁用热重载
        workers=int(os.getenv("UVICORN_WORKERS", "1")),
        log_level="info"
    )

if __name__ == "__main__":
    main()