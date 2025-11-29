"""
演示如何使用 API 工具（适合在线服务如 AlphaFold3、OpenMM 等）
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from astraflow import (
    ToolRegistry, APIConfig,
    ToolSchema, ToolParameters, ToolParameter, ToolReturns
)

def main():
    print("="*80)
    print("API 工具注册示例")
    print("="*80)
    print()
    
    registry = ToolRegistry()
    
    # ========================================
    # 1. 注册本地工具
    # ========================================
    print("1. 注册本地工具（传统方式）")
    
    def local_validate(sequence: str) -> dict:
        """验证蛋白质序列"""
        valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
        is_valid = all(aa in valid_aa for aa in sequence.upper())
        return {"valid": is_valid, "length": len(sequence)}
    
    registry.register(
        ToolSchema(
            name="validate_sequence",
            description="验证蛋白质序列",
            parameters=ToolParameters(
                properties={"sequence": ToolParameter(type="string")},
                required=["sequence"]
            ),
            returns=ToolReturns(type="object")
        ),
        tool_function=local_validate
    )
    print("   ✓ validate_sequence (local)")
    print()
    
    # ========================================
    # 2. 注册 API 工具 - AlphaFold3
    # ========================================
    print("2. 注册 API 工具 - AlphaFold3 结构预测")
    
    registry.register(
        ToolSchema(
            name="alphafold3_predict",
            description="使用 AlphaFold3 预测蛋白质结构",
            parameters=ToolParameters(
                properties={
                    "sequence": ToolParameter(type="string", description="蛋白质序列"),
                    "model_type": ToolParameter(type="string", default="monomer_ptm")
                },
                required=["sequence"]
            ),
            returns=ToolReturns(type="object")
        ),
        api_config=APIConfig(
            url="https://api.alphafold.com/v3/predict",
            method="POST",
            auth_type="api_key",
            auth_token="your-api-key-here",
            timeout=600
        )
    )
    print("   ✓ alphafold3_predict (API)")
    print("     URL: https://api.alphafold.com/v3/predict")
    print()
    
    # ========================================
    # 3. 注册 API 工具 - OpenMM 模拟
    # ========================================
    print("3. 注册 API 工具 - OpenMM 分子动力学")
    
    registry.register(
        ToolSchema(
            name="openmm_simulation",
            description="运行 OpenMM 分子动力学模拟",
            parameters=ToolParameters(
                properties={
                    "pdb_file": ToolParameter(type="string", description="PDB 文件"),
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
            auth_token="your-bearer-token",
            timeout=1800
        )
    )
    print("   ✓ openmm_simulation (API)")
    print("     URL: https://openmm-cloud.example.com/api/simulate")
    print()
    
    # ========================================
    # 4. 注册 API 工具 - 分子对接
    # ========================================
    print("4. 注册 API 工具 - AutoDock Vina 分子对接")
    
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
    print("   ✓ molecular_docking (API)")
    print("     URL: https://docking-api.example.com/v1/dock")
    print()
    
    # ========================================
    # 查看注册的工具
    # ========================================
    print("="*80)
    print("已注册的工具列表:")
    print("="*80)
    print()
    
    for tool_name in registry.list_tools():
        tool_type = registry.get_tool_type(tool_name)
        schema = registry.get_tool_schema(tool_name)
        
        icon = "🔧" if tool_type == "local" else "🌐"
        print(f"{icon} {tool_name} ({tool_type})")
        print(f"   {schema.description}")
        
        if tool_type == "api":
            api_info = registry.get_api_info(tool_name)
            print(f"   API: {api_info['method']} {api_info['url']}")
            print(f"   超时: {api_info['timeout']}s")
        print()
    
    print("="*80)
    print("使用方式:")
    print("="*80)
    print()
    print("# 在工作流中使用（MCP 会自动调用相应的 API）")
    print("from astraflow import WorkflowGenerator, MasterControlPlane")
    print("from openai import OpenAI")
    print()
    print("client = OpenAI(api_key='...', base_url='https://openrouter.ai/api/v1')")
    print("generator = WorkflowGenerator(client, 'anthropic/claude-3.5-sonnet')")
    print("mcp = MasterControlPlane(tool_registry=registry)")
    print()
    print("# LLM 自动生成使用 API 工具的工作流")
    print("workflow = generator.generate(")
    print("    '预测这个序列的结构: MKTAYIAKQRQ...',")
    print("    registry.get_all_schemas()")
    print(")")
    print()
    print("# MCP 会自动判断并调用 API")
    print("logs, context = mcp.execute(workflow)")
    print()
    print("="*80)


if __name__ == "__main__":
    main()

