"""
Workflow Generator using LLM
"""
import sys
import os
# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import List, Any, Optional
import json
import logging
from .models import ToolSchema, Workflow
from .utils import parse_json_from_llm_response

logger = logging.getLogger(__name__)


class WorkflowGenerator:
    """
    使用 LLM 将用户请求转换为结构化工作流
    """
    
    def __init__(self, llm_client: Any, model_name: Optional[str] = None):
        """
        初始化 WorkflowGenerator
        
        Args:
            llm_client: LLM 客户端 (例如 OpenAI client, Anthropic client 等)
            model_name: 使用的模型名称 (可选)
        """
        self.llm_client = llm_client
        self.model_name = model_name
        logger.info(f"Initialized WorkflowGenerator with model: {model_name}")
    
    def generate(self, request: str, tool_schemas: List[ToolSchema]) -> Workflow:
        """
        根据用户请求和可用工具生成工作流
        
        Args:
            request: 用户的原始请求
            tool_schemas: 所有可用工具的 schema 列表
            
        Returns:
            生成的 Workflow 对象
        """
        logger.info(f"Generating workflow for request: {request}")
        
        # 构建 prompt
        prompt = self._build_prompt(request, tool_schemas)
        
        # 调用 LLM
        llm_response = self._call_llm(prompt)
        
        # 解析 LLM 返回的 JSON
        workflow_dict = parse_json_from_llm_response(llm_response)
        
        # 确保包含 original_request
        if "original_request" not in workflow_dict:
            workflow_dict["original_request"] = request
        
        # 构建 Workflow 对象
        workflow = Workflow(**workflow_dict)
        
        logger.info(f"Generated workflow with {len(workflow.steps)} steps (ID: {workflow.workflow_id})")
        return workflow
    
    def _build_prompt(self, request: str, tool_schemas: List[ToolSchema]) -> str:
        """
        构建发送给 LLM 的 prompt
        
        Args:
            request: 用户请求
            tool_schemas: 可用工具列表
            
        Returns:
            格式化的 prompt 字符串
        """
        # 将工具 schemas 转换为易读格式
        tools_description = self._format_tools(tool_schemas)
        
        prompt = f"""You are a workflow planner. Your task is to break down a user's complex request into a structured, step-by-step workflow using the available tools.

                **User Request:**
                {request}

                **Available Tools:**
                {tools_description}

                **Instructions:**
                1. Analyze the user's request and determine what steps are needed.
                2. For each step, select the most appropriate tool from the available tools.
                3. Define the parameters for each tool call. Use the syntax "$context.variable_name" to reference outputs from previous steps.
                4. Assign each step's output to a meaningful variable name using "output_variable".
                5. Return a JSON object with the following structure:

                {{
                "original_request": "{request}",
                "steps": [
                    {{
                    "step_id": 1,
                    "description": "Description of what this step does",
                    "tool_name": "tool_name",
                    "parameters": {{
                        "param1": "value1",
                        "param2": "$context.previous_output"
                    }},
                    "output_variable": "variable_name"
                    }},
                    ...
                ]
                }}

                **Important:**
                - Make sure step_id starts from 1 and increments sequentially.
                - Only use tools that are listed in the Available Tools section.
                - Use $context.variable_name syntax to reference previous step outputs.
                - Return ONLY valid JSON, no additional text or explanation.

                Generate the workflow now:"""
        
        return prompt
    
    def _format_tools(self, tool_schemas: List[ToolSchema]) -> str:
        """
        将工具 schemas 格式化为可读的字符串
        
        Args:
            tool_schemas: 工具 schema 列表
            
        Returns:
            格式化的工具描述
        """
        tools_text = []
        for tool in tool_schemas:
            # 提取必需参数
            required_params = tool.parameters.required if tool.parameters.required else []
            
            # 格式化参数
            params_text = []
            for param_name, param_schema in tool.parameters.properties.items():
                required_marker = " (required)" if param_name in required_params else " (optional)"
                default_marker = f" [default: {param_schema.default}]" if param_schema.default is not None else ""
                params_text.append(
                    f"  - {param_name}: {param_schema.type}{required_marker}{default_marker}\n"
                    f"    {param_schema.description or ''}"
                )
            
            tool_text = f"""
                Tool: {tool.name}
                Description: {tool.description}
                Parameters:
                {chr(10).join(params_text)}
                """
            tools_text.append(tool_text)
        
        return "\n".join(tools_text)
    
    def _call_llm(self, prompt: str) -> str:
        """
        调用 LLM API (OpenAI 风格，兼容 OpenRouter)
        
        Args:
            prompt: 发送给 LLM 的 prompt
            
        Returns:
            LLM 的响应文本
        """
        try:
            # 使用 OpenAI 风格的 API (支持 OpenAI 和 OpenRouter)
            response = self.llm_client.chat.completions.create(
                model=self.model_name or "gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful workflow planning assistant that outputs only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise RuntimeError(f"Failed to generate workflow: {str(e)}")

