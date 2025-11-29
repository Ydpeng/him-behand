# AstraFlow

**基于 LLM 工作流生成与 MCP 工具调用的自动化任务执行系统**

---

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（编辑 config.py）
OPENROUTER_API_KEY = "your-api-key"

# 3. 运行演示
./run_demo.sh
# 或
python examples/demo_with_openrouter.py
```

## 📖 完整文档

**所有文档已整合到一个文件中：**

👉 **[查看完整文档：DOCUMENTATION.md](DOCUMENTATION.md)**

包含内容：
- ✅ 系统概述和架构
- ✅ 快速开始指南
- ✅ 核心功能详解
- ✅ 高级特性（LLM 工具、依赖验证）
- ✅ API 参考
- ✅ 应用场景示例
- ✅ 开发指南

## ✨ 核心特性

- 🤖 **LLM 自动规划** - 将自然语言任务转换为结构化工作流
- ⚙️ **灵活工具系统** - 支持 LLM 工具和专用软件
- 🔍 **智能依赖管理** - 自动检查软件安装，提供指导
- 🔗 **上下文管理** - 步骤间数据传递（`$context.variable`）
- 📊 **训练数据收集** - 生成 LLM 微调标签

## 📁 项目结构

```
mcp-aidd/
├── astraflow/              # 核心库
├── examples/               # 演示脚本
├── tests/                  # 单元测试
├── data/                   # 数据存储
├── config.py               # 配置文件
├── DOCUMENTATION.md        # 📖 完整文档
└── run_demo.sh            # 快捷启动
```

## 🎯 适用场景

- 🧬 **AI 药物设计** (AIDD)
- 🧪 **蛋白质结构预测**
- ⚛️ **量子化学计算**
- 📊 **数据分析流水线**

## 🔧 5 分钟示例

```python
from openai import OpenAI
from astraflow import *

# 初始化
client = OpenAI(api_key="...", base_url="https://openrouter.ai/api/v1")
registry = ToolRegistry()
generator = WorkflowGenerator(client, "anthropic/claude-3.5-sonnet")
mcp = MasterControlPlane(registry)

# 注册工具
registry.register(tool_schema, tool_function)

# 生成并执行工作流
workflow = generator.generate("查询 OpenAI 新闻并总结", registry.get_all_schemas())
logs, context = mcp.execute(workflow)
```

## 📞 获取帮助

- 📖 **完整文档**: [DOCUMENTATION.md](DOCUMENTATION.md)
- 💻 **演示代码**: `examples/` 目录
- 🧪 **测试用例**: `tests/` 目录

## 📄 许可证

MIT License

---

**详细使用说明请查看 [DOCUMENTATION.md](DOCUMENTATION.md)** 📖

