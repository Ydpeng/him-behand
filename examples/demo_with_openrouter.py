"""
Demo script using OpenRouter API
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
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
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, DEFAULT_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    print("AstraFlow 演示 - 使用 OpenRouter API")
    print("=" * 80)
    print()
    
    # 1. 初始化组件
    print("Step 1: 初始化系统组件...")
    tool_registry = ToolRegistry()
    register_all_tools(tool_registry)
    
    # 初始化 OpenRouter 客户端
    print(f"连接到 OpenRouter API...")
    print(f"使用模型: {DEFAULT_MODEL}")
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL
    )
    
    workflow_generator = WorkflowGenerator(
        llm_client=client,
        model_name=DEFAULT_MODEL
    )
    
    mcp = MasterControlPlane(
        tool_registry=tool_registry,
        enable_retry=True,
        max_retries=2
    )
    
    feedback_collector = FeedbackCollector(datastore_path="./data/feedback_labels")
    
    print(f"✓ 已初始化系统组件")
    print(f"✓ 已注册 {len(tool_registry.list_tools())} 个工具")
    print(f"✓ 已连接到 OpenRouter API")
    print()
    
    # 2. 用户请求
    user_request = "帮我查询 OpenAI 公司最近的新闻，总结关键信息。"
    print(f"用户请求: {user_request}")
    print()
    
    # 3. 生成工作流
    print("Step 2: 使用 LLM 生成工作流...")
    try:
        workflow = workflow_generator.generate(
            request=user_request,
            tool_schemas=tool_registry.get_all_schemas()
        )
        
        print(f"✓ 已生成工作流 (ID: {workflow.workflow_id})")
        print(f"  包含 {len(workflow.steps)} 个步骤:")
        for step in workflow.steps:
            print(f"    {step.step_id}. {step.description}")
            print(f"       工具: {step.tool_name}")
            print(f"       参数: {step.parameters}")
        print()
    except Exception as e:
        print(f"✗ 工作流生成失败: {e}")
        return
    
    # 4. 执行工作流
    print("Step 3: 执行工作流...")
    print("-" * 80)
    execution_logs, context = mcp.execute(workflow)
    print("-" * 80)
    print()
    
    print("执行结果:")
    for log in execution_logs:
        status_icon = "✓" if log.status == "success" else "✗" if log.status == "failure" else "⊘"
        print(f"  {status_icon} Step {log.step_id} [{log.tool_name}]: {log.status}")
        if log.error:
            print(f"    错误: {log.error}")
        if log.output and log.status == "success":
            # 简化输出显示
            output_str = str(log.output)
            if len(output_str) > 200:
                output_str = output_str[:200] + "..."
            print(f"    输出: {output_str}")
        print(f"    耗时: {log.duration_ms:.2f} ms")
    print()
    
    # 5. 评估结果
    print("Step 4: 评估工作流结果...")
    overall_success = all(log.status == "success" for log in execution_logs)
    
    # 获取最终输出
    final_output = None
    if overall_success and workflow.steps:
        last_step_var = workflow.steps[-1].output_variable
        final_output = context.get(last_step_var)
    
    evaluation = WorkflowEvaluation(
        overall_success=overall_success,
        final_output=final_output,
        failure_reason=None if overall_success else "部分步骤执行失败",
        human_notes="使用 OpenRouter API 生成的工作流" + 
                    ("，执行成功。" if overall_success else "，部分步骤失败。")
    )
    
    print(f"工作流评估: {'成功 ✓' if overall_success else '失败 ✗'}")
    if evaluation.final_output:
        print(f"最终输出:")
        output_str = str(evaluation.final_output)
        if len(output_str) > 500:
            output_str = output_str[:500] + "..."
        print(f"  {output_str}")
    print()
    
    # 6. 收集反馈
    print("Step 5: 收集反馈标签...")
    label = feedback_collector.create_label(
        workflow=workflow,
        logs=execution_logs,
        evaluation=evaluation
    )
    
    filepath = feedback_collector.save_to_datastore(label)
    print(f"✓ 已保存反馈标签")
    print(f"  文件: {filepath}")
    print()
    
    # 7. 显示统计
    stats = feedback_collector.get_statistics()
    print("数据存储统计:")
    print(f"  总标签数: {stats['total_labels']}")
    print(f"  成功工作流: {stats['successful_workflows']}")
    print(f"  失败工作流: {stats['failed_workflows']}")
    success_rate = (stats['successful_workflows'] / stats['total_labels'] * 100) if stats['total_labels'] > 0 else 0
    print(f"  成功率: {success_rate:.1f}%")
    print()
    
    print("=" * 80)
    print("演示完成！")
    print("=" * 80)
    print()
    print("提示:")
    print("- 查看生成的反馈标签: ls -lh data/feedback_labels/")
    print("- 运行更多测试: python examples/demo_with_openrouter.py")
    print("- 查看完整文档: cat README.md")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n演示已中断")
    except Exception as e:
        logger.error(f"演示执行出错: {e}", exc_info=True)
        print(f"\n✗ 错误: {e}")

