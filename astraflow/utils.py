"""
Utility functions for AstraFlow
"""

import json
import re
from typing import Any, Dict


def parse_json_from_llm_response(response: str) -> Dict[str, Any]:
    """
    从 LLM 响应中解析 JSON
    
    LLM 可能会返回带有额外文本的响应，此函数尝试提取 JSON 部分
    
    Args:
        response: LLM 的原始响应
        
    Returns:
        解析后的 JSON 字典
        
    Raises:
        ValueError: 如果无法解析 JSON
    """
    # 尝试直接解析
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass
    
    # 尝试提取 JSON 代码块
    json_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    matches = re.findall(json_block_pattern, response, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass
    
    # 尝试查找任何 JSON 对象
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    
    raise ValueError(f"Could not parse valid JSON from LLM response: {response[:200]}...")


def resolve_context_reference(reference: str, context: Dict[str, Any]) -> Any:
    """
    解析上下文引用，例如 "$context.search_results[0].url" 或 "$context.search_results.results[0].url"
    
    Args:
        reference: 引用字符串
        context: 上下文字典
        
    Returns:
        解析后的值
        
    Raises:
        ValueError: 如果引用无效
    """
    if not isinstance(reference, str) or not reference.startswith("$context."):
        return reference
    
    # 移除 "$context." 前缀
    path = reference[9:]
    
    # 解析路径
    try:
        result = context
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]  # 移除空字符串
        
        for i, part in enumerate(parts):
            if part.isdigit():
                # 数组索引
                result = result[int(part)]
            else:
                # 对象属性
                if isinstance(result, dict):
                    result = result[part]
                else:
                    raise ValueError(
                        f"Cannot access property '{part}' on non-dict type {type(result).__name__}. "
                        f"Path so far: {'.'.join(parts[:i])}, Current value: {result}"
                    )
        
        return result
    except (KeyError, IndexError, TypeError) as e:
        # 提供更详细的错误信息
        raise ValueError(
            f"Failed to resolve context reference '{reference}': {str(e)}. "
            f"Available context keys: {list(context.keys())}, "
            f"Path attempted: {path}"
        )


def resolve_parameters(parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析参数字典中的所有上下文引用
    
    Args:
        parameters: 参数字典，可能包含 $context 引用
        context: 上下文字典
        
    Returns:
        解析后的参数字典
    """
    resolved = {}
    
    for key, value in parameters.items():
        if isinstance(value, str) and value.startswith("$context."):
            resolved[key] = resolve_context_reference(value, context)
        elif isinstance(value, dict):
            resolved[key] = resolve_parameters(value, context)
        elif isinstance(value, list):
            resolved[key] = [
                resolve_context_reference(item, context) if isinstance(item, str) else item
                for item in value
            ]
        else:
            resolved[key] = value
    
    return resolved

