"""
测试 LLM 工作流生成效果
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
from astraflow import *
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL

def test_workflow_generation():
    """测试不同场景下的工作流生成"""
    
    print("="*80)
    print("测试 LLM 工作流生成")
    print("="*80)
    print()
    
    # 初始化
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    registry = ToolRegistry()
    generator = WorkflowGenerator(client, DEFAULT_MODEL)
    
    # 注册简单工具
    def get_number() -> int:
        return 42
    
    def add(a: int, b: int) -> int:
        return a + b
    
    def multiply(a: int, b: int) -> int:
        return a * b
    
    registry.register(
        ToolSchema(
            name="get_number",
            description="获取一个数字，返回整数42",
            parameters=ToolParameters(properties={}, required=[]),
            returns=ToolReturns(type="integer")
        ),
        get_number
    )
    
    registry.register(
        ToolSchema(
            name="add",
            description="将两个数字相加",
            parameters=ToolParameters(
                properties={
                    "a": ToolParameter(type="integer", description="第一个数字"),
                    "b": ToolParameter(type="integer", description="第二个数字")
                },
                required=["a", "b"]
            ),
            returns=ToolReturns(type="integer")
        ),
        add
    )
    
    registry.register(
        ToolSchema(
            name="multiply",
            description="将两个数字相乘",
            parameters=ToolParameters(
                properties={
                    "a": ToolParameter(type="integer", description="第一个数字"),
                    "b": ToolParameter(type="integer", description="第二个数字")
                },
                required=["a", "b"]
            ),
            returns=ToolReturns(type="integer")
        ),
        multiply
    )
    
    # 测试场景
    test_cases = [
        "获取一个数字，然后加上10，最后乘以2",
        "获取一个数字并乘以3",
        "获取两个数字（都是调用get_number），然后相加"
    ]
    
    for i, request in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"测试场景 {i}: {request}")
        print(f"{'='*80}\n")
        
        try:
            # 生成工作流
            workflow = generator.generate(request, registry.get_all_schemas())
            
            print(f"✓ 生成成功！工作流 ID: {workflow.workflow_id}")
            print(f"  步骤数量: {len(workflow.steps)}")
            print()
            
            # 显示工作流步骤
            for step in workflow.steps:
                print(f"  Step {step.step_id}: {step.description}")
                print(f"    工具: {step.tool_name}")
                print(f"    参数: {step.parameters}")
                print(f"    输出: {step.output_variable}")
                print()
            
            # 执行工作流
            mcp = MasterControlPlane(tool_registry=registry)
            logs, context = mcp.execute(workflow)
            
            # 显示执行结果
            print("  执行结果:")
            all_success = True
            for log in logs:
                status_icon = "✓" if log.status == "success" else "✗"
                print(f"    {status_icon} Step {log.step_id}: {log.status}")
                if log.output is not None:
                    print(f"       输出: {log.output}")
                if log.error:
                    print(f"       错误: {log.error}")
                    all_success = False
            
            if all_success:
                final_var = workflow.steps[-1].output_variable
                print(f"\n  ✓ 工作流执行成功！最终结果: {context.get(final_var)}")
            else:
                print(f"\n  ✗ 工作流执行失败")
            
        except Exception as e:
            print(f"✗ 生成失败: {e}")
    
    print(f"\n{'='*80}")
    print("测试完成！")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_workflow_generation()

