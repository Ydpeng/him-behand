#!/usr/bin/env python3
"""
测试所有必需的依赖是否已安装
"""

import importlib

def test_import(module_name):
    """测试模块是否能导入"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name}")
        return True
    except ImportError:
        print(f"✗ {module_name}")
        return False

def main():
    """测试所有核心依赖"""
    print("测试依赖安装情况:")
    print("=" * 40)
    
    dependencies = [
        "pydantic",
        "requests", 
        "fastapi",
        "uvicorn",
        "psycopg2",
        "oss2",
        "dashvector",
        "dashscope"
    ]
    
    results = []
    for dep in dependencies:
        results.append(test_import(dep))
    
    print("=" * 40)
    
    if all(results):
        print("✓ 所有依赖都已正确安装!")
        return True
    else:
        print("✗ 部分依赖未安装，请检查 requirements.txt")
        return False

if __name__ == "__main__":
    main()