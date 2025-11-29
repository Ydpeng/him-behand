"""
Example tools for demonstrating AstraFlow
"""

import time
import random
from typing import List, Dict, Any


def search_web(query: str, num_results: int = 3) -> Dict[str, List[Dict[str, str]]]:
    """
    模拟网络搜索工具
    
    Args:
        query: 搜索关键词
        num_results: 返回结果数量
        
    Returns:
        搜索结果字典
    """
    time.sleep(0.5)  # 模拟网络延迟
    
    # 模拟搜索结果
    results = []
    for i in range(num_results):
        results.append({
            "url": f"https://example.com/result_{i+1}",
            "title": f"Result {i+1} for '{query}'",
            "snippet": f"This is a sample snippet for search result {i+1} about {query}..."
        })
    
    return {"results": results}


def fetch_url_content(url: str) -> str:
    """
    模拟从 URL 获取内容
    
    Args:
        url: 要抓取的 URL
        
    Returns:
        页面内容文本
    """
    time.sleep(0.3)  # 模拟网络延迟
    
    # 模拟可能的失败（10%概率）
    if random.random() < 0.1:
        raise Exception(f"HTTPError: 404 Not Found - {url}")
    
    # 模拟页面内容
    content = f"""
    Mock content from {url}
    
    财报摘要
    ========
    
    本季度营收: $10.5B (同比增长 15%)
    净利润: $2.3B (同比增长 20%)
    关键增长点:
    - 云服务业务增长 35%
    - AI 产品线营收翻倍
    - 国际市场拓展取得突破
    
    展望：预计下季度继续保持强劲增长态势。
    """
    
    return content


def summarize_text(text: str, points_to_cover: List[str] = None) -> Dict[str, Any]:
    """
    模拟文本摘要工具
    
    Args:
        text: 要摘要的文本
        points_to_cover: 需要关注的要点列表
        
    Returns:
        摘要结果字典
    """
    time.sleep(0.8)  # 模拟处理时间
    
    # 简单的摘要提取（实际应用中会使用 LLM）
    lines = text.strip().split('\n')
    key_lines = [line for line in lines if any(point in line for point in (points_to_cover or []))]
    
    summary = {
        "summary": "根据财报，公司本季度表现强劲，营收和利润均大幅增长。",
        "key_points": key_lines if key_lines else [
            "营收: $10.5B (同比增长 15%)",
            "净利润: $2.3B (同比增长 20%)",
            "云服务业务增长显著"
        ],
        "word_count": len(text.split()),
        "source_length": len(text)
    }
    
    return summary


def send_email(to: str, subject: str, body: str) -> Dict[str, Any]:
    """
    模拟发送邮件工具
    
    Args:
        to: 收件人地址
        subject: 邮件主题
        body: 邮件正文
        
    Returns:
        发送结果
    """
    time.sleep(0.5)  # 模拟发送延迟
    
    # 验证邮箱格式
    if "@" not in to:
        raise ValueError(f"Invalid email address: {to}")
    
    return {
        "success": True,
        "message_id": f"msg-{random.randint(1000, 9999)}",
        "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "to": to,
        "subject": subject
    }


def calculate(expression: str) -> Dict[str, Any]:
    """
    模拟计算工具
    
    Args:
        expression: 数学表达式
        
    Returns:
        计算结果
    """
    try:
        # 注意：实际应用中应使用更安全的表达式求值方法
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        raise ValueError(f"Invalid expression: {expression}. Error: {str(e)}")


def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """
    模拟天气查询工具
    
    Args:
        city: 城市名称
        unit: 温度单位 (celsius/fahrenheit)
        
    Returns:
        天气信息
    """
    time.sleep(0.4)
    
    # 模拟天气数据
    temp = random.randint(15, 30)
    if unit == "fahrenheit":
        temp = int(temp * 9/5 + 32)
    
    conditions = ["晴", "多云", "阴", "小雨"]
    
    return {
        "city": city,
        "temperature": temp,
        "unit": unit,
        "condition": random.choice(conditions),
        "humidity": random.randint(40, 80),
        "wind_speed": random.randint(5, 25)
    }


def translate_text(text: str, target_language: str) -> Dict[str, str]:
    """
    模拟翻译工具
    
    Args:
        text: 要翻译的文本
        target_language: 目标语言
        
    Returns:
        翻译结果
    """
    time.sleep(0.6)
    
    # 模拟翻译（实际应用中会调用真实的翻译 API）
    translations = {
        "english": f"[EN] {text}",
        "chinese": f"[中文] {text}",
        "spanish": f"[ES] {text}",
        "french": f"[FR] {text}"
    }
    
    return {
        "original_text": text,
        "translated_text": translations.get(target_language.lower(), f"[{target_language}] {text}"),
        "source_language": "auto-detected",
        "target_language": target_language
    }

