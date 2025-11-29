"""
高级演示：展示 LLM 工具和依赖验证功能
"""

import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
from astraflow import (
    ToolRegistry, MasterControlPlane, FeedbackCollector,
    ToolSchema, ToolParameters, ToolParameter, ToolReturns,
    Workflow, WorkflowStep, WorkflowEvaluation
)
from astraflow.llm_tools import LLMTool, create_llm_tool_function
from astraflow.tool_validator import ToolValidator, ToolDependency, print_dependency_report
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_llm_tools():
    """演示 LLM 驱动的工具"""
    print("\n" + "="*80)
    print("演示 1: LLM 驱动的工具")
    print("="*80 + "\n")
    
    # 初始化 LLM 客户端
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    
    # 创建 ToolRegistry
    registry = ToolRegistry()
    
    # 1. 注册 LLM 文本分析工具
    print("注册 LLM 工具...")
    llm_tool = LLMTool(client, DEFAULT_MODEL)
    
    registry.register(
        ToolSchema(
            name="llm_analyze_text",
            description="使用 LLM 分析文本内容",
            parameters=ToolParameters(
                properties={
                    "text": ToolParameter(type="string", description="要分析的文本"),
                    "task": ToolParameter(type="string", description="分析任务描述")
                },
                required=["text", "task"]
            ),
            returns=ToolReturns(type="string")
        ),
        llm_tool.analyze_text
    )
    
    registry.register(
        ToolSchema(
            name="llm_extract_info",
            description="使用 LLM 从文本中提取结构化信息",
            parameters=ToolParameters(
                properties={
                    "text": ToolParameter(type="string", description="源文本"),
                    "fields": ToolParameter(type="array", description="要提取的字段列表")
                },
                required=["text", "fields"]
            ),
            returns=ToolReturns(type="object")
        ),
        llm_tool.extract_information
    )
    
    registry.register(
        ToolSchema(
            name="llm_transform_text",
            description="使用 LLM 转换文本",
            parameters=ToolParameters(
                properties={
                    "text": ToolParameter(type="string", description="源文本"),
                    "transformation": ToolParameter(type="string", description="转换描述")
                },
                required=["text", "transformation"]
            ),
            returns=ToolReturns(type="string")
        ),
        llm_tool.transform_text
    )
    
    print(f"✓ 已注册 {len(registry.list_tools())} 个 LLM 工具\n")
    
    # 2. 创建使用 LLM 工具的工作流
    workflow = Workflow(
        original_request="分析一段产品评论并提取关键信息",
        steps=[
            WorkflowStep(
                step_id=1,
                description="提取评论中的关键信息",
                tool_name="llm_extract_info",
                parameters={
                    "text": "这款手机非常棒！电池续航能力强，可以用两天。相机质量也很好，拍照清晰。唯一的缺点是价格有点贵，要5999元。",
                    "fields": ["产品", "优点", "缺点", "价格"]
                },
                output_variable="extracted_info"
            ),
            WorkflowStep(
                step_id=2,
                description="生成评论总结",
                tool_name="llm_transform_text",
                parameters={
                    "text": "$context.extracted_info",
                    "transformation": "将提取的信息转换为简洁的一句话总结"
                },
                output_variable="summary"
            )
        ]
    )
    
    # 3. 执行工作流
    print("执行工作流...")
    mcp = MasterControlPlane(tool_registry=registry)
    logs, context = mcp.execute(workflow)
    
    # 4. 显示结果
    print("\n执行结果:")
    for log in logs:
        status = "✓" if log.status == "success" else "✗"
        print(f"  {status} Step {log.step_id}: {log.status} ({log.duration_ms:.0f}ms)")
        if log.output:
            print(f"     输出: {log.output}")
    
    print(f"\n最终总结: {context.get('summary', 'N/A')}")


def demo_tool_dependencies():
    """演示工具依赖验证"""
    print("\n" + "="*80)
    print("演示 2: 工具依赖验证")
    print("="*80 + "\n")
    
    validator = ToolValidator()
    
    # 示例 1: 检查 Python 数据科学工具
    print("场景 1: 数据科学工具（需要 numpy, pandas）")
    print("-" * 80)
    
    data_science_deps = [
        ToolDependency(
            name="NumPy",
            dependency_type="python_package",
            check_method="numpy",
            install_instructions="pip install numpy",
            required=True
        ),
        ToolDependency(
            name="Pandas",
            dependency_type="python_package",
            check_method="pandas",
            install_instructions="pip install pandas",
            required=True
        ),
        ToolDependency(
            name="Matplotlib",
            dependency_type="python_package",
            check_method="matplotlib",
            install_instructions="pip install matplotlib",
            required=False  # 可选依赖
        ),
    ]
    
    satisfied, messages = validator.validate_tool_dependencies("data_analysis_tool", data_science_deps)
    print_dependency_report("data_analysis_tool", messages)
    
    if satisfied:
        print("✓ 所有必需依赖已满足，工具可以使用\n")
    else:
        print("✗ 部分必需依赖未满足，请按照上述说明安装\n")
    
    # 示例 2: 检查分子动力学仿真工具（假设需要 OpenMM）
    print("\n场景 2: 分子动力学仿真工具（需要 OpenMM）")
    print("-" * 80)
    
    md_simulation_deps = [
        ToolDependency(
            name="OpenMM",
            dependency_type="python_package",
            check_method="openmm",
            install_instructions="""
# 使用 conda 安装 OpenMM:
conda install -c conda-forge openmm

# 或访问官方网站: http://openmm.org/
            """,
            required=True
        ),
        ToolDependency(
            name="MDTraj",
            dependency_type="python_package",
            check_method="mdtraj",
            install_instructions="conda install -c conda-forge mdtraj",
            required=False
        ),
    ]
    
    satisfied, messages = validator.validate_tool_dependencies("md_simulation_tool", md_simulation_deps)
    print_dependency_report("md_simulation_tool", messages)
    
    if not satisfied:
        print("⚠️  警告: 此工具需要专用软件，请先安装依赖再使用")
        print("    如果您已在特定环境中安装（如 conda 环境），请确保已激活该环境\n")
    
    # 示例 3: 检查外部可执行文件
    print("\n场景 3: 需要外部可执行文件的工具")
    print("-" * 80)
    
    external_tool_deps = [
        ToolDependency(
            name="GROMACS",
            dependency_type="executable",
            check_method="gmx",
            install_instructions="""
# 安装 GROMACS (分子动力学软件):
# Ubuntu/Debian: sudo apt-get install gromacs
# macOS: brew install gromacs
# 或从官网下载: http://www.gromacs.org/
            """,
            required=True
        ),
        ToolDependency(
            name="VMD (可视化)",
            dependency_type="executable",
            check_method="vmd",
            install_instructions="Download from: https://www.ks.uiuc.edu/Research/vmd/",
            required=False
        ),
    ]
    
    satisfied, messages = validator.validate_tool_dependencies("gromacs_simulation", external_tool_deps)
    print_dependency_report("gromacs_simulation", messages)
    
    # 示例 4: 检查模型文件
    print("\n场景 4: 需要预训练模型的工具")
    print("-" * 80)
    
    model_deps = [
        ToolDependency(
            name="ESM2 蛋白质语言模型",
            dependency_type="file",
            check_method="~/models/esm2_t33_650M_UR50D.pt",
            install_instructions="""
# 下载 ESM2 模型:
mkdir -p ~/models
cd ~/models
wget https://dl.fbaipublicfiles.com/fair-esm/models/esm2_t33_650M_UR50D.pt

# 或使用 Hugging Face:
# from transformers import AutoModel
# model = AutoModel.from_pretrained("facebook/esm2_t33_650M_UR50D")
            """,
            required=True
        ),
    ]
    
    satisfied, messages = validator.validate_tool_dependencies("protein_structure_prediction", model_deps)
    print_dependency_report("protein_structure_prediction", messages)


def demo_integrated_workflow():
    """演示整合的工作流：自动检查依赖 + 执行"""
    print("\n" + "="*80)
    print("演示 3: 整合工作流（依赖检查 + 执行）")
    print("="*80 + "\n")
    
    # 定义一个需要特殊依赖的工具
    def molecular_analysis(pdb_file: str) -> dict:
        """分析蛋白质结构（假设需要 MDAnalysis）"""
        try:
            import MDAnalysis as mda
            # 这里是实际的分析逻辑
            return {
                "status": "success",
                "message": f"分析了 {pdb_file}",
                "num_atoms": 1234,
                "num_residues": 156
            }
        except ImportError:
            raise ImportError("MDAnalysis is required but not installed")
    
    # 定义工具的依赖
    tool_dependencies = [
        ToolDependency(
            name="MDAnalysis",
            dependency_type="python_package",
            check_method="MDAnalysis",
            install_instructions="pip install MDAnalysis",
            required=True
        ),
    ]
    
    # 在注册工具前验证依赖
    validator = ToolValidator()
    satisfied, messages = validator.validate_tool_dependencies("molecular_analysis", tool_dependencies)
    
    print("工具依赖检查:")
    for msg in messages:
        print(f"  {msg}")
    print()
    
    if not satisfied:
        print("⚠️  工具依赖未满足，无法注册和使用此工具")
        print("    请按照上述说明安装依赖后重试\n")
        return
    
    # 依赖满足，注册并使用工具
    registry = ToolRegistry()
    registry.register(
        ToolSchema(
            name="molecular_analysis",
            description="分析蛋白质结构",
            parameters=ToolParameters(
                properties={
                    "pdb_file": ToolParameter(type="string", description="PDB 文件路径")
                },
                required=["pdb_file"]
            ),
            returns=ToolReturns(type="object")
        ),
        molecular_analysis
    )
    
    print("✓ 工具已注册并可以使用")


def main():
    """运行所有演示"""
    print("\n" + "="*80)
    print("AstraFlow 高级功能演示")
    print("="*80)
    
    try:
        # 演示 1: LLM 工具
        demo_llm_tools()
        
        # 演示 2: 依赖验证
        demo_tool_dependencies()
        
        # 演示 3: 整合工作流
        demo_integrated_workflow()
        
        print("\n" + "="*80)
        print("所有演示完成！")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n演示已中断")
    except Exception as e:
        logger.error(f"演示执行出错: {e}", exc_info=True)
        print(f"\n✗ 错误: {e}")


if __name__ == "__main__":
    main()

