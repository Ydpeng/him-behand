"""
LLM-based tools that can be dynamically created and executed
"""

from typing import Any, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class LLMTool:
    """
    基于 LLM 的工具，可以动态执行各种任务
    """
    
    def __init__(self, llm_client: Any, model_name: Optional[str] = None):
        """
        初始化 LLM 工具
        
        Args:
            llm_client: LLM 客户端
            model_name: 模型名称
        """
        self.llm_client = llm_client
        self.model_name = model_name
    
    def analyze_text(self, text: str, task: str) -> str:
        """
        使用 LLM 分析文本
        
        Args:
            text: 要分析的文本
            task: 分析任务描述
            
        Returns:
            分析结果
        """
        prompt = f"""Task: {task}

Text to analyze:
{text}

Please provide your analysis:"""
        
        return self._call_llm(prompt)
    
    def extract_information(self, text: str, fields: list) -> Dict[str, Any]:
        """
        使用 LLM 从文本中提取结构化信息
        
        Args:
            text: 源文本
            fields: 要提取的字段列表
            
        Returns:
            提取的信息字典
        """
        fields_str = ", ".join(fields)
        prompt = f"""Extract the following information from the text: {fields_str}

Text:
{text}

Return the information in JSON format with keys: {fields_str}"""
        
        result = self._call_llm(prompt)
        
        # 尝试解析 JSON
        import json
        from .utils import parse_json_from_llm_response
        try:
            return parse_json_from_llm_response(result)
        except:
            # 如果解析失败，返回原始文本
            return {"raw_response": result}
    
    def transform_text(self, text: str, transformation: str) -> str:
        """
        使用 LLM 转换文本
        
        Args:
            text: 源文本
            transformation: 转换描述（如"翻译成英文"、"简化为要点"等）
            
        Returns:
            转换后的文本
        """
        prompt = f"""Transform the following text: {transformation}

Original text:
{text}

Transformed text:"""
        
        return self._call_llm(prompt)
    
    def answer_question(self, context: str, question: str) -> str:
        """
        基于上下文回答问题
        
        Args:
            context: 上下文信息
            question: 问题
            
        Returns:
            答案
        """
        prompt = f"""Context:
{context}

Question: {question}

Answer:"""
        
        return self._call_llm(prompt)
    
    def generate_content(self, task: str, context: Optional[str] = None) -> str:
        """
        生成内容
        
        Args:
            task: 生成任务描述
            context: 可选的上下文
            
        Returns:
            生成的内容
        """
        if context:
            prompt = f"""Task: {task}

                Context:
                {context}

                Generated content:"""
        else:
            prompt = f"""Task: {task}

                Generated content:"""
        
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM (OpenAI 风格，兼容 OpenRouter)"""
        try:
            # 使用 OpenAI 风格的 API (支持 OpenAI 和 OpenRouter)
            response = self.llm_client.chat.completions.create(
                model=self.model_name or "gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise


def create_llm_tool_function(llm_client: Any, tool_type: str, model_name: Optional[str] = None) -> Callable:
    """
    创建一个基于 LLM 的工具函数
    
    Args:
        llm_client: LLM 客户端
        tool_type: 工具类型 (analyze, extract, transform, answer, generate)
        model_name: 模型名称
        
    Returns:
        可调用的工具函数
    """
    llm_tool = LLMTool(llm_client, model_name)
    
    tool_methods = {
        "analyze": llm_tool.analyze_text,
        "extract": llm_tool.extract_information,
        "transform": llm_tool.transform_text,
        "answer": llm_tool.answer_question,
        "generate": llm_tool.generate_content,
    }
    
    if tool_type not in tool_methods:
        raise ValueError(f"Unknown tool type: {tool_type}. Available: {list(tool_methods.keys())}")
    
    return tool_methods[tool_type]

