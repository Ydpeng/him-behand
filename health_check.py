#!/usr/bin/env python3
"""
Health check script for SAE deployment
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """检查必要的环境变量配置"""
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


def check_dependencies():
    """检查Python依赖是否正常"""
    try:
        import pydantic
        import requests
        # 可选依赖，不强制检查
        # DashVector和DashScope是可选依赖，如果未安装也不会影响核心功能
        
        logger.info("Core dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing core dependency: {e}")
        return False


def health_check():
    """综合健康检查"""
    checks = [
        ("Environment variables", check_environment()),
        ("Dependencies", check_dependencies()),
    ]
    
    all_healthy = True
    for check_name, status in checks:
        if status:
            logger.info(f"✓ {check_name}: OK")
        else:
            logger.error(f"✗ {check_name}: FAILED")
            all_healthy = False
    
    return all_healthy


if __name__ == "__main__":
    logger.info("Running AstraFlow health check...")
    
    if health_check():
        logger.info("Health check PASSED")
        sys.exit(0)
    else:
        logger.error("Health check FAILED")
        sys.exit(1)