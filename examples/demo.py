"""
Demonstration script for AstraFlow system
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from astraflow import (
    ToolRegistry,
    WorkflowGenerator,
    MasterControlPlane,
    FeedbackCollector,
    ToolSchema,
    ToolParameters,
    ToolParameter,
    ToolReturns,
    WorkflowEvaluation
)
from examples.example_tools import (
    search_web,
    fetch_url_content,
    summarize_text,
    send_email,
    calculate,
    get_weather,
    translate_text
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockLLMClient:
    """
    模拟 LLM 客户端，用于演示
    在实际应用中，应该使用真实的 LLM API（OpenAI, Anthropic 等）
    """
    
    def generate(self, prompt: str) -> str:
        """
        返回一个预定义的工作流 JSON
        """
        # 从 prompt 中提取用户请求（简化处理）
        if "A公司" in prompt or "财报" in prompt:
            return """{
  "original_request": "帮我查询A公司最近的财报，总结关键亮点。",
  "steps": [
    {
      "step_id": 1,
      "description": "搜索A公司的最新财报链接",
      "tool_name": "search_web",
      "parameters": {
        "query": "A公司 2025年最新财报",
        "num_results": 3
      },
      "output_variable": "search_results"
    },
    {
      "step_id": 2,
      "description": "从搜索结果中抓取财报页面的文本内容",
      "tool_name": "fetch_url_content",
      "parameters": {
        "url": "$context.search_results.results[0].url"
      },
      "output_variable": "report_content"
    },
    {
      "step_id": 3,
      "description": "总结财报文本的关键要点",
      "tool_name": "summarize_text",
      "parameters": {
        "text": "$context.report_content",
        "points_to_cover": ["营收", "利润", "增长点"]
      },
      "output_variable": "summary"
    }
  ]
}"""
        elif "天气" in prompt:
            return """{
  "original_request": "查询北京的天气，如果温度超过25度就发邮件提醒我。",
  "steps": [
    {
      "step_id": 1,
      "description": "查询北京的天气信息",
      "tool_name": "get_weather",
      "parameters": {
        "city": "北京",
        "unit": "celsius"
      },
      "output_variable": "weather_info"
    },
    {
      "step_id": 2,
      "description": "发送邮件提醒",
      "tool_name": "send_email",
      "parameters": {
        "to": "user@example.com",
        "subject": "天气提醒：北京温度较高",
        "body": "今天北京的温度超过了25度，请注意防暑降温。"
      },
      "output_variable": "email_result"
    }
  ]
}"""
        else:
            # 默认返回一个简单的工作流
            return """{
  "original_request": "执行默认任务",
  "steps": [
    {
      "step_id": 1,
      "description": "执行搜索",
      "tool_name": "search_web",
      "parameters": {
        "query": "示例查询"
      },
      "output_variable": "results"
    }
  ]
}"""


def register_all_tools(registry: ToolRegistry) -> None:
    """
    注册所有示例工具到注册中心
    """
    logger.info("Registering tools...")
    
    # 1. search_web
    registry.register(
        ToolSchema(
            name="search_web",
            description="用于在互联网上搜索信息并返回结果列表",
            parameters=ToolParameters(
                properties={
                    "query": ToolParameter(type="string", description="搜索的关键词或问题"),
                    "num_results": ToolParameter(type="integer", default=3, description="返回结果数量")
                },
                required=["query"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                                "snippet": {"type": "string"}
                            }
                        }
                    }
                }
            )
        ),
        search_web
    )
    
    # 2. fetch_url_content
    registry.register(
        ToolSchema(
            name="fetch_url_content",
            description="从指定 URL 抓取网页内容",
            parameters=ToolParameters(
                properties={
                    "url": ToolParameter(type="string", description="要抓取的 URL")
                },
                required=["url"]
            ),
            returns=ToolReturns(type="string")
        ),
        fetch_url_content
    )
    
    # 3. summarize_text
    registry.register(
        ToolSchema(
            name="summarize_text",
            description="总结文本内容的关键要点",
            parameters=ToolParameters(
                properties={
                    "text": ToolParameter(type="string", description="要摘要的文本"),
                    "points_to_cover": ToolParameter(
                        type="array",
                        description="需要关注的要点列表"
                    )
                },
                required=["text"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "summary": {"type": "string"},
                    "key_points": {"type": "array"}
                }
            )
        ),
        summarize_text
    )
    
    # 4. send_email
    registry.register(
        ToolSchema(
            name="send_email",
            description="发送电子邮件",
            parameters=ToolParameters(
                properties={
                    "to": ToolParameter(type="string", description="收件人邮箱地址"),
                    "subject": ToolParameter(type="string", description="邮件主题"),
                    "body": ToolParameter(type="string", description="邮件正文")
                },
                required=["to", "subject", "body"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "success": {"type": "boolean"},
                    "message_id": {"type": "string"}
                }
            )
        ),
        send_email
    )
    
    # 5. calculate
    registry.register(
        ToolSchema(
            name="calculate",
            description="执行数学计算",
            parameters=ToolParameters(
                properties={
                    "expression": ToolParameter(type="string", description="数学表达式")
                },
                required=["expression"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "result": {"type": "number"},
                    "expression": {"type": "string"}
                }
            )
        ),
        calculate
    )
    
    # 6. get_weather
    registry.register(
        ToolSchema(
            name="get_weather",
            description="查询指定城市的天气信息",
            parameters=ToolParameters(
                properties={
                    "city": ToolParameter(type="string", description="城市名称"),
                    "unit": ToolParameter(
                        type="string",
                        default="celsius",
                        description="温度单位 (celsius/fahrenheit)"
                    )
                },
                required=["city"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "temperature": {"type": "number"},
                    "condition": {"type": "string"},
                    "humidity": {"type": "number"}
                }
            )
        ),
        get_weather
    )
    
    # 7. translate_text
    registry.register(
        ToolSchema(
            name="translate_text",
            description="翻译文本到指定语言",
            parameters=ToolParameters(
                properties={
                    "text": ToolParameter(type="string", description="要翻译的文本"),
                    "target_language": ToolParameter(type="string", description="目标语言")
                },
                required=["text", "target_language"]
            ),
            returns=ToolReturns(
                type="object",
                properties={
                    "translated_text": {"type": "string"},
                    "source_language": {"type": "string"}
                }
            )
        ),
        translate_text
    )
    
    logger.info(f"Registered {len(registry.list_tools())} tools")


def run_demo():
    """
    运行完整的演示流程
    """
    print("=" * 80)
    print("AstraFlow 演示")
    print("=" * 80)
    print()
    
    # 1. 初始化组件
    logger.info("Step 1: Initializing components...")
    tool_registry = ToolRegistry()
    register_all_tools(tool_registry)
    
    mock_llm = MockLLMClient()
    workflow_generator = WorkflowGenerator(llm_client=mock_llm)
    
    mcp = MasterControlPlane(tool_registry=tool_registry, enable_retry=True, max_retries=2)
    
    feedback_collector = FeedbackCollector(datastore_path="./data/feedback_labels")
    
    print(f"✓ 已初始化系统组件")
    print(f"✓ 已注册 {len(tool_registry.list_tools())} 个工具")
    print()
    
    # 2. 用户请求
    user_request = "帮我查询A公司最近的财报，总结关键亮点。"
    print(f"用户请求: {user_request}")
    print()
    
    # 3. 生成工作流
    logger.info("Step 2: Generating workflow...")
    workflow = workflow_generator.generate(
        request=user_request,
        tool_schemas=tool_registry.get_all_schemas()
    )
    
    print(f"✓ 已生成工作流 (ID: {workflow.workflow_id})")
    print(f"  包含 {len(workflow.steps)} 个步骤:")
    for step in workflow.steps:
        print(f"    {step.step_id}. {step.description} [{step.tool_name}]")
    print()
    
    # 4. 执行工作流
    logger.info("Step 3: Executing workflow...")
    print("执行工作流...")
    execution_logs, context = mcp.execute(workflow)
    
    print()
    print("执行结果:")
    for log in execution_logs:
        status_icon = "✓" if log.status == "success" else "✗" if log.status == "failure" else "⊘"
        print(f"  {status_icon} Step {log.step_id} [{log.tool_name}]: {log.status}")
        if log.error:
            print(f"    错误: {log.error}")
        print(f"    耗时: {log.duration_ms:.2f} ms")
    print()
    
    # 5. 评估结果
    logger.info("Step 4: Evaluating workflow...")
    overall_success = all(log.status == "success" for log in execution_logs)
    
    evaluation = WorkflowEvaluation(
        overall_success=overall_success,
        final_output=context.get("summary") if overall_success else None,
        failure_reason=None if overall_success else "部分步骤执行失败",
        human_notes="演示运行，工作流按预期执行。" if overall_success else "需要改进错误处理。"
    )
    
    print(f"工作流评估: {'成功 ✓' if overall_success else '失败 ✗'}")
    if evaluation.final_output:
        print(f"最终输出: {evaluation.final_output}")
    print()
    
    # 6. 收集反馈
    logger.info("Step 5: Collecting feedback...")
    label = feedback_collector.create_label(
        workflow=workflow,
        logs=execution_logs,
        evaluation=evaluation
    )
    
    filepath = feedback_collector.save_to_datastore(label)
    print(f"✓ 已保存反馈标签: {filepath}")
    print()
    
    # 7. 显示统计
    stats = feedback_collector.get_statistics()
    print("数据存储统计:")
    print(f"  总标签数: {stats['total_labels']}")
    print(f"  成功工作流: {stats['successful_workflows']}")
    print(f"  失败工作流: {stats['failed_workflows']}")
    print()
    
    print("=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()

