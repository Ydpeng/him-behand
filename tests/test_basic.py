"""
Basic tests for AstraFlow components
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from astraflow import (
    ToolRegistry,
    ToolSchema,
    ToolParameters,
    ToolParameter,
    ToolReturns,
    Workflow,
    WorkflowStep,
    MasterControlPlane,
    FeedbackCollector,
    WorkflowEvaluation
)


def test_tool_registry():
    """测试工具注册中心"""
    registry = ToolRegistry()
    
    # 定义一个简单的工具
    def add(a: int, b: int) -> int:
        return a + b
    
    # 注册工具
    schema = ToolSchema(
        name="add",
        description="Add two numbers",
        parameters=ToolParameters(
            properties={
                "a": ToolParameter(type="integer", description="First number"),
                "b": ToolParameter(type="integer", description="Second number")
            },
            required=["a", "b"]
        ),
        returns=ToolReturns(type="integer")
    )
    
    registry.register(schema, add)
    
    # 测试调用
    result = registry.invoke("add", {"a": 2, "b": 3})
    assert result == 5
    
    # 测试工具列表
    assert "add" in registry.list_tools()
    assert registry.has_tool("add")


def test_workflow_execution():
    """测试工作流执行"""
    registry = ToolRegistry()
    
    # 注册测试工具
    def get_value() -> dict:
        return {"value": 10}
    
    def multiply(value: int, factor: int) -> int:
        return value * factor
    
    registry.register(
        ToolSchema(
            name="get_value",
            description="Get a value",
            parameters=ToolParameters(properties={}, required=[]),
            returns=ToolReturns(type="object")
        ),
        get_value
    )
    
    registry.register(
        ToolSchema(
            name="multiply",
            description="Multiply a value",
            parameters=ToolParameters(
                properties={
                    "value": ToolParameter(type="integer"),
                    "factor": ToolParameter(type="integer")
                },
                required=["value", "factor"]
            ),
            returns=ToolReturns(type="integer")
        ),
        multiply
    )
    
    # 创建工作流
    workflow = Workflow(
        original_request="Get a value and multiply it by 5",
        steps=[
            WorkflowStep(
                step_id=1,
                description="Get initial value",
                tool_name="get_value",
                parameters={},
                output_variable="initial"
            ),
            WorkflowStep(
                step_id=2,
                description="Multiply by 5",
                tool_name="multiply",
                parameters={
                    "value": "$context.initial.value",
                    "factor": 5
                },
                output_variable="result"
            )
        ]
    )
    
    # 执行工作流
    mcp = MasterControlPlane(tool_registry=registry)
    logs, context = mcp.execute(workflow)
    
    # 验证结果
    assert len(logs) == 2
    assert all(log.status == "success" for log in logs)
    assert context["result"] == 50


def test_feedback_collector():
    """测试反馈收集器"""
    import tempfile
    import shutil
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        collector = FeedbackCollector(datastore_path=temp_dir)
        
        # 创建一个简单的工作流
        workflow = Workflow(
            original_request="Test request",
            steps=[
                WorkflowStep(
                    step_id=1,
                    description="Test step",
                    tool_name="test_tool",
                    parameters={},
                    output_variable="result"
                )
            ]
        )
        
        # 创建标签
        from astraflow.models import StepExecutionLog
        logs = [
            StepExecutionLog(
                step_id=1,
                tool_name="test_tool",
                status="success",
                output={"test": "data"},
                duration_ms=100.0
            )
        ]
        
        evaluation = WorkflowEvaluation(
            overall_success=True,
            final_output={"test": "data"}
        )
        
        label = collector.create_label(workflow, logs, evaluation)
        
        # 保存标签
        filepath = collector.save_to_datastore(label)
        assert os.path.exists(filepath)
        
        # 加载标签
        loaded_label = collector.load_label(label.label_id)
        assert loaded_label is not None
        assert loaded_label.label_id == label.label_id
        
        # 统计信息
        stats = collector.get_statistics()
        assert stats["total_labels"] == 1
        assert stats["successful_workflows"] == 1
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

