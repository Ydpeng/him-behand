#!/bin/bash
# AstraFlow 演示启动脚本

echo "========================================="
echo "AstraFlow 系统演示"
echo "========================================="
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "❌ Python 未安装"
    exit 1
fi

echo "✓ Python 版本: $(python --version)"
echo ""

# 检查依赖
echo "检查依赖..."
python -c "import pydantic; import openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  部分依赖未安装，正在安装..."
    pip install -q pydantic openai
    echo "✓ 依赖安装完成"
fi

echo ""
echo "========================================="
echo "请选择要运行的演示:"
echo "========================================="
echo "1. 基础演示（使用模拟 LLM）"
echo "2. OpenRouter API 演示（真实 LLM）"
echo "3. 高级功能演示（LLM 工具 + 依赖验证）"
echo "4. 运行测试"
echo "5. 查看生成的反馈标签"
echo "0. 退出"
echo ""

read -p "请输入选项 (0-5): " choice

case $choice in
    1)
        echo ""
        echo "运行基础演示..."
        python examples/demo.py
        ;;
    2)
        echo ""
        echo "运行 OpenRouter API 演示..."
        python examples/demo_with_openrouter.py
        ;;
    3)
        echo ""
        echo "运行高级功能演示..."
        python examples/demo_advanced.py
        ;;
    4)
        echo ""
        echo "运行测试..."
        python -m pytest tests/ -v
        ;;
    5)
        echo ""
        echo "查看反馈标签..."
        if [ -d "data/feedback_labels" ]; then
            echo "反馈标签文件:"
            ls -lh data/feedback_labels/
            echo ""
            echo "标签总数: $(ls data/feedback_labels/ | wc -l)"
        else
            echo "暂无反馈标签，请先运行演示"
        fi
        ;;
    0)
        echo "再见！"
        exit 0
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "演示完成！"
echo "========================================="
echo ""
echo "提示："
echo "- 查看文档: cat README.md"
echo "- 查看高级功能: cat ADVANCED_FEATURES.md"
echo "- 查看总结: cat SUMMARY.md"
echo ""

