#!/usr/bin/env python3
"""
测试 AstraFlow API 服务是否正常启动
"""

import os
import sys
import time
import requests
import subprocess
import threading

def start_server():
    """启动 API 服务器"""
    print("启动 API 服务器...")
    # 设置环境变量以避免依赖外部服务
    env = os.environ.copy()
    env.update({
        "DASHVECTOR_API_KEY": "test_key",
        "DASHSCOPE_API_KEY": "test_key", 
        "OPENROUTER_API_KEY": "test_key",
        "HOST": "127.0.0.1",
        "PORT": "8000"
    })
    
    # 启动服务器进程
    process = subprocess.Popen(
        [sys.executable, "astraflow/api.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 给服务器一些启动时间
    time.sleep(3)
    
    return process

def test_api_health():
    """测试 API 健康状态"""
    try:
        # 测试基础端点
        response = requests.get("http://127.0.0.1:8000/docs")
        if response.status_code == 200:
            print("✓ API 文档端点正常")
            return True
        else:
            print(f"✗ API 文档端点异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ API 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("AstraFlow API 服务测试")
    print("=" * 50)
    
    # 启动服务器
    server_process = start_server()
    
    try:
        # 测试 API
        if test_api_health():
            print("\n✓ API 服务启动成功！")
            print("\n可用的端点:")
            print("- http://127.0.0.1:8000/docs - API 文档")
            print("- POST /register/api - 注册 API 工具")
            print("- POST /tools/search - 工具搜索")
            print("- POST /list/tools - 获取工具列表")
        else:
            print("\n✗ API 服务启动失败")
            
        # 输出服务器日志
        stdout, stderr = server_process.communicate()
        if stdout:
            print(f"\n服务器输出:\n{stdout.decode()}")
        if stderr:
            print(f"\n服务器错误:\n{stderr.decode()}")
            
    finally:
        # 确保清理进程
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()