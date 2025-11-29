# AstraFlow 完整文档

**基于 LLM 工作流生成与 MCP 工具调用的自动化任务执行系统**

---

## 目录

1. [系统概述](#1-系统概述)
2. [快速开始](#2-快速开始)
3. [核心架构](#3-核心架构)
4. [基础使用](#4-基础使用)
5. [高级特性](#5-高级特性)
6. [项目结构](#6-项目结构)
7. [应用场景](#7-应用场景)
8. [开发指南](#8-开发指南)
9. [API 参考](#9-api-参考)

---

## 1. 系统概述

### 1.1 什么是 AstraFlow？

AstraFlow 是一个智能工作流执行系统，能够：
- 📝 **接收自然语言任务** - 用户用日常语言描述需求
- 🤖 **LLM 自动规划** - 将复杂任务分解为结构化的工作流
- ⚙️ **自动执行** - MCP 引擎按步骤调用工具完成任务
- 📊 **收集反馈** - 记录执行过程，生成 LLM 微调数据

### 1.2 核心特性

- ✅ **LLM 工作流生成** - 支持 OpenAI、Anthropic、OpenRouter 等
- ✅ **灵活的工具系统** - 既支持 LLM 驱动的工具，也支持专用软件
- ✅ **智能依赖管理** - 自动检查软件/模型是否安装，提供安装指南
- ✅ **上下文管理** - 步骤间数据传递，支持 `$context.variable` 引用
- ✅ **错误处理** - 自动重试、详细日志、失败回滚
- ✅ **训练数据收集** - 为 LLM 微调生成高质量标签数据

### 1.3 系统架构图

**示例场景：靶向 EGFR 激酶的小分子抑制剂设计**

```
┌─────────────────────────────────────────────────────────────┐
│ 用户请求                                                      │
│ "设计针对 EGFR 激酶的小分子抑制剂，验证其结合能力和稳定性"      │
└──────┬──────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ WorkflowGenerator (LLM)                                      │
│ - 分析药物设计任务                                             │
│ - 查询可用工具 (结构预测、分子对接、MD模拟等)                    │
│ - 生成结构化工作流 (JSON)                                      │
└──────┬───────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ Workflow (JSON) - 药物设计流程                                 │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Step 1: fetch_protein_structure("EGFR", "PDB")        │  │
│ │         → 获取靶标蛋白 EGFR 的 3D 结构                   │  │
│ │                                                        │  │
│ │ Step 2: prepare_receptor($context.protein_pdb)        │  │
│ │         → 预处理受体，添加氢原子，定义活性位点             │  │
│ │                                                        │  │
│ │ Step 3: molecular_docking(                            │  │
│ │             receptor=$context.prepared_receptor,      │  │
│ │             ligand="candidate_drug.mol2"              │  │
│ │         )                                             │  │
│ │         → 分子对接，计算结合构象和亲和力                  │  │
│ │                                                        │  │
│ │ Step 4: md_simulation(                                │  │
│ │             complex=$context.docking_result.top_pose, │  │
│ │             time=100ns, temperature=300K              │  │
│ │         )                                             │  │
│ │         → 分子动力学模拟，验证复合物稳定性                │  │
│ │                                                        │  │
│ │ Step 5: analyze_trajectory(                           │  │
│ │             trajectory=$context.md_traj               │  │
│ │         )                                             │  │
│ │         → 分析 RMSD、RMSF、氢键等                       │  │
│ └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ MasterControlPlane (MCP)                                     │
│ - 按顺序执行药物设计的每一步                                    │
│ - 管理计算上下文 (蛋白结构、对接结果、模拟轨迹等)                 │
│ - 解析步骤间依赖 ($context.protein_pdb → 对接 → 模拟)         │
│ - 调用 ToolRegistry 中的工具                                 │
│ - 记录每步执行状态和结果                                       │
└──────┬───────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ ToolRegistry (混合工具)                                       │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ 本地函数工具:                                           │  │
│ │  - fetch_protein_structure()  (从 PDB 下载)           │  │
│ │  - prepare_receptor()         (预处理蛋白)            │  │
│ │  - analyze_trajectory()       (轨迹分析)              │  │
│ │                                                        │  │
│ │ API 工具 (在线服务):                                    │  │
│ │  - alphafold3_predict()       (结构预测 API)          │  │
│ │  - molecular_docking()        (AutoDock Vina API)     │  │
│ │  - md_simulation()            (OpenMM 云端 API)       │  │
│ │                                                        │  │
│ │ LLM 工具 (辅助):                                       │  │
│ │  - summarize_results()        (生成分析报告)           │  │
│ └────────────────────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ 执行结果 + 详细日志                                            │
│ - 对接打分: -9.8 kcal/mol                                    │
│ - RMSD: 1.2 Å (稳定)                                         │
│ - 氢键数量: 3 个关键氢键                                      │
│ - 每步执行状态: success/failure                               │
└──────┬───────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│ FeedbackCollector                                            │
│ - 聚合完整工作流、执行日志、计算结果                             │
│ - 用户标注: 候选药物是否满足需求 (✓/✗)                         │
│ - 生成 FeedbackLabel (JSON)                                  │
│ - 保存用于 WorkflowGenerator LLM 的微调数据                   │
│   (让 LLM 学习如何更好地生成药物设计工作流)                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 快速开始

### 2.1 安装

```bash
cd /Users/guangyongchen/Research/mcp-aidd
pip install -r requirements.txt
```

### 2.2 配置 API Key

编辑 `config.py`：

```python
# OpenRouter API Configuration
OPENROUTER_API_KEY = "your-api-key-here"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
```

### 2.3 运行演示

```bash
# 方式 1: 使用快捷脚本
./run_demo.sh

# 方式 2: 直接运行
python examples/demo_with_openrouter.py  # 真实 LLM
python examples/demo_advanced.py         # 高级功能
python examples/demo.py                  # 基础演示（模拟 LLM）
```

### 2.4 5 分钟示例

```python
from openai import OpenAI
from astraflow import *

# 1. 初始化
client = OpenAI(api_key="your-key", base_url="https://openrouter.ai/api/v1")
registry = ToolRegistry()
generator = WorkflowGenerator(client, "anthropic/claude-sonnet-4.5")
mcp = MasterControlPlane(tool_registry=registry)

# 2. 注册工具
def search_web(query: str) -> dict:
    return {"results": [...]}

registry.register(
    ToolSchema(
        name="search_web",
        description="搜索网络信息",
        parameters=ToolParameters(
            properties={"query": ToolParameter(type="string")},
            required=["query"]
        ),
        returns=ToolReturns(type="object")
    ),
    search_web
)

# 3. 生成并执行工作流
workflow = generator.generate(
    request="搜索 OpenAI 最新新闻并总结",
    tool_schemas=registry.get_all_schemas()
)

logs, context = mcp.execute(workflow)

# 4. 查看结果
for log in logs:
    print(f"Step {log.step_id}: {log.status}")
```

---

## 3. 核心架构

### 3.1 数据模型

#### ToolSchema - 工具定义

```python
ToolSchema(
    name="search_web",
    description="在互联网上搜索信息",
    parameters=ToolParameters(
        properties={
            "query": ToolParameter(type="string", description="搜索关键词"),
            "num_results": ToolParameter(type="integer", default=3)
        },
        required=["query"]
    ),
    returns=ToolReturns(type="object")
)
```

#### Workflow - 工作流

```json
{
  "workflow_id": "wf-uuid-12345",
  "original_request": "用户的原始请求",
  "steps": [
    {
      "step_id": 1,
      "description": "步骤描述",
      "tool_name": "search_web",
      "parameters": {"query": "搜索内容"},
      "output_variable": "search_results"
    }
  ]
}
```

#### FeedbackLabel - 训练标签

```json
{
  "label_id": "label-uuid-67890",
  "workflow_id": "wf-uuid-12345",
  "original_request": "...",
  "generated_workflow": {...},
  "step_execution_logs": [
    {
      "step_id": 1,
      "tool_name": "search_web",
      "status": "success",
      "output": {...},
      "duration_ms": 1200
    }
  ],
  "workflow_evaluation": {
    "overall_success": true,
    "final_output": {...}
  }
}
```

### 3.2 核心组件

#### 3.2.1 ToolRegistry - 工具注册中心

```python
class ToolRegistry:
    def register(self, tool_schema: ToolSchema, tool_function: Callable)
    def invoke(self, tool_name: str, args: dict) -> Any
    def get_all_schemas(self) -> List[ToolSchema]
    def has_tool(self, tool_name: str) -> bool
```

#### 3.2.2 WorkflowGenerator - 工作流生成器

```python
class WorkflowGenerator:
    def __init__(self, llm_client: Any, model_name: str)
    def generate(self, request: str, tool_schemas: List[ToolSchema]) -> Workflow
```

支持的 LLM 客户端：
- OpenAI (GPT-4, GPT-3.5 等)
- OpenRouter (推荐，支持多种模型的统一接口)
- 任何兼容 OpenAI API 格式的服务

**注意**：系统使用 OpenAI API 风格，所有客户端需要支持 `chat.completions.create()` 接口。

#### 3.2.3 MasterControlPlane (MCP) - 执行引擎

```python
class MasterControlPlane:
    def __init__(self, tool_registry: ToolRegistry, enable_retry: bool = False)
    def execute(self, workflow: Workflow) -> Tuple[List[StepExecutionLog], Dict]
```

**核心功能**：
- 按顺序执行工作流步骤
- 管理执行上下文 (context)
- 解析 `$context` 引用
- 处理错误和重试
- 生成详细执行日志

#### 3.2.4 FeedbackCollector - 反馈收集器

```python
class FeedbackCollector:
    def __init__(self, datastore_path: str)
    def create_label(self, workflow, logs, evaluation) -> FeedbackLabel
    def save_to_datastore(self, label: FeedbackLabel) -> str
    def export_for_training(self, output_file: str) -> int
```

---

## 4. 基础使用

### 4.1 创建和注册工具

```python
from astraflow import *

# 定义工具函数
def calculate(expression: str) -> dict:
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result, "success": True}
    except Exception as e:
        raise ValueError(f"Invalid expression: {expression}")

# 创建工具 schema
tool_schema = ToolSchema(
    name="calculate",
    description="执行数学计算",
    parameters=ToolParameters(
        properties={
            "expression": ToolParameter(type="string", description="数学表达式")
        },
        required=["expression"]
    ),
    returns=ToolReturns(type="object")
)

# 注册工具
registry = ToolRegistry()
registry.register(tool_schema, calculate)
```

### 4.2 手动创建工作流

```python
workflow = Workflow(
    original_request="计算 (10 + 20) * 3",
    steps=[
        WorkflowStep(
            step_id=1,
            description="计算表达式",
            tool_name="calculate",
            parameters={"expression": "(10 + 20) * 3"},
            output_variable="result"
        )
    ]
)

# 执行
mcp = MasterControlPlane(tool_registry=registry)
logs, context = mcp.execute(workflow)
print(context["result"])  # {"result": 90, "success": True}
```

### 4.3 使用上下文引用

```python
workflow = Workflow(
    original_request="获取数字并加倍",
    steps=[
        WorkflowStep(
            step_id=1,
            description="获取初始数字",
            tool_name="get_number",
            parameters={},
            output_variable="number"
        ),
        WorkflowStep(
            step_id=2,
            description="将数字加倍",
            tool_name="double",
            parameters={"value": "$context.number"},  # 引用上一步输出
            output_variable="doubled"
        )
    ]
)
```

**支持的引用语法**：
- `$context.variable` - 简单属性
- `$context.variable.property` - 嵌套属性
- `$context.variable[0]` - 数组索引
- `$context.variable.array[0].property` - 复杂嵌套

### 4.4 收集反馈数据

```python
collector = FeedbackCollector(datastore_path="./data/feedback_labels")

# 执行工作流
logs, context = mcp.execute(workflow)

# 评估结果
evaluation = WorkflowEvaluation(
    overall_success=True,
    final_output=context.get("result"),
    human_notes="工作流执行顺利"
)

# 保存标签
label = collector.create_label(workflow, logs, evaluation)
filepath = collector.save_to_datastore(label)

# 导出训练数据
collector.export_for_training("training_data.json", filter_successful_only=True)
```

---

## 5. 高级特性

### 5.1 工具的三种类型

AstraFlow 支持三种类型的工具，可以在一个工作流中混合使用：

| 类型 | 说明 | 适用场景 | 示例 |
|------|------|---------|------|
| **本地函数** | Python 函数 | 简单计算、数据处理 | 序列验证、格式转换 |
| **API 工具** | 远程 HTTP 服务 | 在线计算服务 | AlphaFold3 API、OpenMM 云端 |
| **LLM 工具** ⚠️ | 让 LLM 执行任务 | 文本处理（不精确） | 文本总结、信息提取 |

#### 5.1.1 本地函数工具（最常用）

**适合**：你自己写的计算函数、数据处理逻辑

```python
def calculate_rmsd(structure1: str, structure2: str) -> float:
    """计算两个结构的 RMSD"""
    # 你的计算逻辑
    rmsd = ...
    return rmsd

registry.register(
    ToolSchema(name="calculate_rmsd", ...),
    tool_function=calculate_rmsd  # 本地函数
)
```

#### 5.1.2 API 工具（调用在线服务）

**适合**：在线的 AlphaFold3、OpenMM、分子对接等服务

**为什么需要 API 工具？**
- ✅ 无需本地安装复杂软件（如 AlphaFold3）
- ✅ 云端计算资源更强大
- ✅ 使用官方维护的最新服务

**示例**：注册在线 AlphaFold3

```python
from astraflow import APIConfig

registry.register(
    ToolSchema(
        name="alphafold3_predict",
        description="使用 AlphaFold3 预测蛋白质结构",
        parameters=ToolParameters(
            properties={"sequence": ToolParameter(type="string")},
            required=["sequence"]
        ),
        returns=ToolReturns(type="object")
    ),
    api_config=APIConfig(
        url="https://api.alphafold.com/v3/predict",
        method="POST",
        auth_type="api_key",
        auth_token="your-api-key",
        timeout=600
    )
)
```

**API 配置参数**

```python
APIConfig(
    url="https://api.example.com/endpoint",  # API 端点 URL
    method="POST",                            # HTTP 方法：GET 或 POST
    headers={"Custom-Header": "value"},       # 自定义请求头（可选）
    timeout=300,                               # 超时时间（秒）
    auth_type="bearer",                        # 认证类型：bearer, api_key, basic
    auth_token="your-token"                    # 认证令牌
)
```

**认证方式**：
- `bearer` → `Authorization: Bearer token`
- `api_key` → `X-API-Key: token`  
- 自定义 → 通过 `headers` 参数

**更多示例**：

**OpenMM 云端模拟**

```python
# OpenMM 云端模拟
registry.register(
    ToolSchema(
        name="openmm_simulation",
        description="运行 OpenMM 分子动力学模拟",
        parameters=ToolParameters(
            properties={
                "pdb_file": ToolParameter(type="string"),
                "simulation_time": ToolParameter(type="number", default=1.0),
                "temperature": ToolParameter(type="number", default=300)
            },
            required=["pdb_file"]
        ),
        returns=ToolReturns(type="object")
    ),
    api_config=APIConfig(
        url="https://openmm-cloud.example.com/api/simulate",
        method="POST",
        auth_type="bearer",
        auth_token="your-openmm-token",
        timeout=1800  # 30分钟
    )
)

# AutoDock Vina 分子对接
registry.register(
    ToolSchema(
        name="molecular_docking",
        description="分子对接计算",
        parameters=ToolParameters(
            properties={
                "receptor": ToolParameter(type="string"),
                "ligand": ToolParameter(type="string"),
                "center_x": ToolParameter(type="number"),
                "center_y": ToolParameter(type="number"),
                "center_z": ToolParameter(type="number")
            },
            required=["receptor", "ligand", "center_x", "center_y", "center_z"]
        ),
        returns=ToolReturns(type="object")
    ),
    api_config=APIConfig(
        url="https://docking-api.example.com/v1/dock",
        method="POST",
        timeout=300
    )
)
```

#### 5.1.3 LLM 工具 ⚠️（谨慎使用）

**警告**：LLM 工具让 LLM 直接执行任务，**容易出错，不适合需要精确结果的场景**。

**✅ 适合**：
- 文本总结、改写
- 从文本提取大致信息
- 生成描述性内容

**❌ 不适合**：
- 精确计算
- 结构化数据处理
- 关键决策

**示例**：文本分析

```python
from astraflow import LLMTool
from openai import OpenAI

client = OpenAI(api_key="your-key")
llm_tool = LLMTool(client, "gpt-4")

# 注册 LLM 工具
registry.register(
    ToolSchema(
        name="analyze_sentiment",
        description="分析文本情感",
        parameters=ToolParameters(
            properties={
                "text": ToolParameter(type="string"),
                "task": ToolParameter(type="string")
            },
            required=["text", "task"]
        ),
        returns=ToolReturns(type="string")
    ),
    llm_tool.analyze_text
)
```

**LLM 工具方法**：
- `analyze_text()` - 文本分析
- `extract_information()` - 信息提取 
- `transform_text()` - 文本转换
- `generate_content()` - 内容生成

**建议**：尽量使用本地函数或 API 工具，LLM 工具仅用于辅助性的文本处理。

### 5.2 依赖检查（可选功能）

**作用**：注册工具前，检查需要的软件/包是否已安装，并提示用户安装。

**什么时候需要**：
- 使用本地安装的软件（如 OpenMM、GROMACS）
- 调用 Python 包（如 rdkit、biopython）

**示例**：

```python
from astraflow import ToolValidator, ToolDependency

# 定义 OpenMM 工具的依赖
openmm_dep = ToolDependency(
    name="OpenMM",
    dependency_type="python_package",
    check_method="openmm",
    install_instructions="conda install -c conda-forge openmm",
    required=True
)

# 检查依赖
validator = ToolValidator()
satisfied, messages = validator.validate_tool_dependencies(
    "openmm_simulation", [openmm_dep]
)

if satisfied:
    registry.register(schema, my_openmm_function)
else:
    print("⚠️ OpenMM 未安装，请运行：")
    print("   conda install -c conda-forge openmm")
```

### 5.3 完整示例：混合使用多种工具

以下示例展示了如何在一个工作流中结合不同类型的工具：

```python
from astraflow import ToolRegistry, APIConfig, WorkflowGenerator, MasterControlPlane
from openai import OpenAI

registry = ToolRegistry()

# 1. 本地函数工具 - 序列验证
def validate_sequence(sequence: str) -> dict:
    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    is_valid = all(aa in valid_aa for aa in sequence.upper())
    return {"valid": is_valid, "length": len(sequence)}

registry.register(
    ToolSchema(name="validate_sequence", ...),
    tool_function=validate_sequence
)

# 2. API 工具 - AlphaFold3 结构预测
registry.register(
    ToolSchema(name="alphafold3_predict", ...),
    api_config=APIConfig(
        url="https://api.alphafold.com/v3/predict",
        auth_type="api_key",
        auth_token="your-key"
    )
)

# 3. LLM 工具 - 文本分析（可选，谨慎使用）
from astraflow import LLMTool
llm_tool = LLMTool(OpenAI(...), "gpt-4")
registry.register(
    ToolSchema(name="analyze_structure", ...),
    tool_function=llm_tool.analyze_text
)

# 使用 - LLM 自动生成工作流
client = OpenAI(
    api_key="sk-or-v1-...",
    base_url="https://openrouter.ai/api/v1"
)
generator = WorkflowGenerator(client, "anthropic/claude-3.5-sonnet")
mcp = MasterControlPlane(tool_registry=registry)

# 生成并执行工作流
workflow = generator.generate(
    "验证这个序列，预测结构，并分析其稳定性",
    registry.get_all_schemas()
)

logs, context = mcp.execute(workflow)
print(f"最终结果: {context}")
```

---

## 6. 项目结构

```
mcp-aidd/
├── astraflow/                    # 核心库
│   ├── __init__.py              # 包导出
│   ├── models.py                # 数据模型（Pydantic）
│   ├── tool_registry.py         # 工具注册和管理
│   ├── workflow_generator.py    # LLM 工作流生成
│   ├── mcp.py                   # 主控程序（执行引擎）
│   ├── feedback_collector.py    # 反馈收集和存储
│   ├── llm_tools.py            # LLM 驱动的工具
│   ├── tool_validator.py        # 工具依赖验证
│   └── utils.py                 # 工具函数
│
├── examples/                     # 示例和演示
│   ├── demo.py                  # 基础演示（模拟 LLM）
│   ├── demo_with_openrouter.py # OpenRouter API 演示
│   ├── demo_advanced.py         # 高级功能演示
│   └── example_tools.py         # 示例工具实现
│
├── tests/                        # 测试
│   └── test_basic.py            # 基础单元测试
│
├── data/                         # 数据目录（自动创建）
│   └── feedback_labels/         # 反馈标签 JSON 文件
│
├── config.py                     # 配置文件（API keys）
├── requirements.txt              # Python 依赖
├── run_demo.sh                  # 快捷启动脚本
└── DOCUMENTATION.md             # 本文件
```

---

## 7. 应用场景

### 7.1 AI 药物设计 (AIDD)

```python
# 药物分子分析流水线
Workflow:
  1. [LLM] 文献分析 - 提取靶点和已知抑制剂
  2. [专用软件] 分子对接 - AutoDock Vina
  3. [专用软件] 分子动力学 - OpenMM/GROMACS
  4. [LLM] 性质预测 - 基于结构特征
  5. [LLM] 生成报告 - 总结分析结果
```

### 7.2 蛋白质结构预测

```python
Workflow:
  1. [依赖检查] 验证 AlphaFold2/ESMFold 是否安装
  2. [专用模型] 结构预测
  3. [LLM] 分析预测置信度
  4. [专用软件] 结构优化 - Rosetta
  5. [LLM] 生成结构分析报告
```

### 7.3 量子化学计算

```python
Workflow:
  1. [LLM] 解析分子式，生成输入文件
  2. [专用软件] DFT 计算 - Quantum ESPRESSO
  3. [LLM] 分析电子结构
  4. [专用软件] 激发态计算 - ORCA
  5. [LLM] 生成计算报告
```

### 7.4 数据分析流水线

```python
Workflow:
  1. [工具] 数据读取 - pandas
  2. [工具] 数据清洗和转换
  3. [LLM] 异常检测和解释
  4. [工具] 统计分析 - scipy
  5. [LLM] 生成可读的分析报告
```

---

## 8. 开发指南

### 8.1 创建自定义工具

#### 步骤 1: 实现工具函数

```python
def my_tool(param1: str, param2: int) -> dict:
    """工具功能描述"""
    # 实现逻辑
    result = process(param1, param2)
    return {"result": result}
```

#### 步骤 2: 定义工具 Schema

```python
tool_schema = ToolSchema(
    name="my_tool",
    description="工具的详细描述",
    parameters=ToolParameters(
        properties={
            "param1": ToolParameter(type="string", description="参数1说明"),
            "param2": ToolParameter(type="integer", description="参数2说明", default=10)
        },
        required=["param1"]
    ),
    returns=ToolReturns(type="object")
)
```

#### 步骤 3: 注册工具

```python
registry.register(tool_schema, my_tool)
```

### 8.2 最佳实践

#### 工具设计
- ✅ 单一职责原则
- ✅ 清晰的输入/输出定义
- ✅ 完善的错误处理
- ✅ 详细的文档字符串

#### 何时使用 LLM 工具

**✅ 适合使用**：
- 文本分析、总结、翻译
- 信息提取和结构化
- 自然语言理解任务
- 不需要精确计算的任务

**❌ 不适合使用**：
- 需要精确数值计算
- 需要专业领域知识（如量子化学）
- 需要调用特定软件/模型
- 性能敏感的任务

#### 错误处理

```python
try:
    result = run_specialized_tool()
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行依赖检查获取安装说明")
except RuntimeError as e:
    print(f"工具执行失败: {e}")
```

### 8.3 测试工作流

```python
# 创建测试工作流
workflow = Workflow(...)

# 执行
mcp = MasterControlPlane(tool_registry=registry, enable_retry=True)
logs, context = mcp.execute(workflow)

# 验证结果
assert all(log.status == "success" for log in logs)
assert "expected_key" in context
```

### 8.4 数据收集和微调

#### 收集训练数据

```python
collector = FeedbackCollector()

for task in tasks:
    # 生成并执行工作流
    workflow = generator.generate(task, tool_schemas)
    logs, context = mcp.execute(workflow)
    
    # 评估（人工或自动）
    evaluation = evaluate_workflow(logs, context)
    
    # 保存标签
    label = collector.create_label(workflow, logs, evaluation)
    collector.save_to_datastore(label)
```

#### 导出和分析

```python
# 导出所有标签
collector.export_for_training("all_data.json")

# 只导出成功的
collector.export_for_training("successful.json", filter_successful_only=True)

# 查看统计
stats = collector.get_statistics()
print(f"成功率: {stats['successful_workflows']/stats['total_labels']*100:.1f}%")
```

---

## 9. API 参考

### 9.1 核心类

#### ToolRegistry

```python
class ToolRegistry:
    def __init__(self)
    def register(self, tool_schema: ToolSchema, tool_function: Callable) -> None
    def invoke(self, tool_name: str, args: Dict[str, Any]) -> Any
    def get_all_schemas(self) -> List[ToolSchema]
    def get_tool_schema(self, tool_name: str) -> ToolSchema
    def has_tool(self, tool_name: str) -> bool
    def list_tools(self) -> List[str]
```

#### WorkflowGenerator

```python
class WorkflowGenerator:
    def __init__(self, llm_client: Any, model_name: Optional[str] = None)
    def generate(self, request: str, tool_schemas: List[ToolSchema]) -> Workflow
```

#### MasterControlPlane

```python
class MasterControlPlane:
    def __init__(self, 
                 tool_registry: ToolRegistry, 
                 enable_retry: bool = False, 
                 max_retries: int = 3)
    def execute(self, workflow: Workflow) -> Tuple[List[StepExecutionLog], Dict[str, Any]]
```

#### FeedbackCollector

```python
class FeedbackCollector:
    def __init__(self, datastore_path: Optional[str] = None)
    def create_label(self, workflow: Workflow, logs: List[StepExecutionLog], 
                     evaluation: WorkflowEvaluation) -> FeedbackLabel
    def save_to_datastore(self, label: FeedbackLabel) -> str
    def load_label(self, label_id: str) -> Optional[FeedbackLabel]
    def list_labels(self, limit: Optional[int] = None) -> List[str]
    def get_statistics(self) -> Dict[str, Any]
    def export_for_training(self, output_file: str, 
                           filter_successful_only: bool = False) -> int
```

### 9.2 高级类

#### LLMTool

```python
class LLMTool:
    def __init__(self, llm_client: Any, model_name: Optional[str] = None)
    def analyze_text(self, text: str, task: str) -> str
    def extract_information(self, text: str, fields: list) -> Dict[str, Any]
    def transform_text(self, text: str, transformation: str) -> str
    def answer_question(self, context: str, question: str) -> str
    def generate_content(self, task: str, context: Optional[str] = None) -> str
```

#### ToolValidator

```python
class ToolValidator:
    def __init__(self)
    def validate_tool_dependencies(self, tool_name: str, 
                                   dependencies: List[ToolDependency]) -> Tuple[bool, List[str]]
    def check_python_package(self, package_name: str, 
                            version_requirement: Optional[str] = None) -> Tuple[bool, str]
    def check_executable(self, executable_name: str) -> Tuple[bool, str]
    def check_file_exists(self, file_path: str) -> Tuple[bool, str]
    def clear_cache(self)
```

### 9.3 数据模型

#### ToolSchema

```python
@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: ToolParameters
    returns: ToolReturns
```

#### Workflow

```python
@dataclass
class Workflow:
    workflow_id: str
    original_request: str
    steps: List[WorkflowStep]
    created_at: datetime
```

#### FeedbackLabel

```python
@dataclass
class FeedbackLabel:
    label_id: str
    workflow_id: str
    original_request: str
    generated_workflow: Workflow
    step_execution_logs: List[StepExecutionLog]
    workflow_evaluation: WorkflowEvaluation
    created_at: datetime
```

---

## 附录

### A. 常见问题

**Q: 如何切换不同的 LLM？**

系统使用 OpenAI API 风格，推荐使用 OpenRouter 作为统一接口：

```python
from openai import OpenAI

# OpenRouter (推荐 - 支持所有主流模型)
client = OpenAI(
    api_key="your-openrouter-key",
    base_url="https://openrouter.ai/api/v1"
)
generator = WorkflowGenerator(client, "anthropic/claude-3.5-sonnet")

# 直接使用 OpenAI
client = OpenAI(api_key="your-openai-key")
generator = WorkflowGenerator(client, "gpt-4")
```

**查看 OpenRouter 可用模型**：
- 🌐 模型列表：https://openrouter.ai/models
- 📖 API 文档：https://openrouter.ai/docs
- 支持的模型：GPT-4、Claude、Gemini、Llama、Mistral 等
- 使用方法：复制模型 ID（如 `anthropic/claude-3.5-sonnet`）

**Q: 如何处理工具执行失败？**

MCP 会自动记录错误并中止后续步骤。可以启用重试：

```python
mcp = MasterControlPlane(tool_registry=registry, enable_retry=True, max_retries=3)
```

**Q: 如何查看生成的反馈数据？**

```bash
# 查看所有标签文件
ls -lh data/feedback_labels/

# 查看某个标签内容
cat data/feedback_labels/label-xxx.json | jq .
```

**Q: 上下文引用不工作？**

确保：
1. 引用的变量名与 `output_variable` 一致
2. 前面的步骤执行成功
3. 语法正确：`$context.variable_name`

### B. 技术栈

- **Python**: 3.8+
- **Pydantic**: 2.0+ (数据验证)
- **LLM API**: OpenAI / Anthropic / OpenRouter
- **存储**: JSON 文件（可扩展到数据库）

### C. 贡献指南

欢迎提交 Issue 和 Pull Request！

### D. 许可证

MIT License

---

**AstraFlow - 让 AI 工作流自动化变得简单而强大** 🚀

版本: 0.1.0 | 最后更新: 2025-11-10

