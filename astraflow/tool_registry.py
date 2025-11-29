"""
Tool Registry for managing and executing tools
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Dict, List, Callable, Any, Optional, Literal, Union
from .models import ToolSchema
import logging

logger = logging.getLogger(__name__)

# 尝试导入 requests，如果没有安装则 API 功能不可用
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not installed. API tools will not be available.")


class APIConfig:
    """API 工具配置"""
    
    def __init__(
        self,
        url: str,
        method: Literal["GET", "POST"] = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 300,
        auth_type: Optional[Literal["bearer", "api_key", "basic"]] = None,
        auth_token: Optional[str] = None,
    ):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.timeout = timeout
        
        # 设置认证
        if auth_type == "bearer" and auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
        elif auth_type == "api_key" and auth_token:
            self.headers["X-API-Key"] = auth_token


class ToolRegistry:
    """
    工具注册中心，负责存储、管理和调用所有可用工具
    支持本地函数和远程 API 两种类型
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._tool_executors: Dict[str, Union[Callable, APIConfig]] = {}
        self._tool_types: Dict[str, str] = {}  # "local" 或 "api"
    
    def register(
        self, 
        tool_schema: ToolSchema, 
        tool_function: Optional[Callable] = None,
        api_config: Optional[APIConfig] = None
    ) -> None:
        """
        注册一个新工具（本地函数或远程 API）
        
        Args:
            tool_schema: 工具的 schema 定义
            tool_function: 本地工具的执行函数（与 api_config 二选一）
            api_config: API 工具的配置（与 tool_function 二选一）
        
        Raises:
            ValueError: 如果同时提供或都不提供 tool_function 和 api_config
        """
        if (tool_function is None) == (api_config is None):
            raise ValueError("Must provide exactly one of tool_function or api_config")
        
        tool_name = tool_schema.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered. Overwriting.")
        
        self._tools[tool_name] = tool_schema
        
        if tool_function is not None:
            # 注册本地工具
            self._tool_executors[tool_name] = tool_function
            self._tool_types[tool_name] = "local"
            logger.info(f"Registered local tool: {tool_name}")
        else:
            # 注册 API 工具
            if not REQUESTS_AVAILABLE:
                raise RuntimeError("requests library not installed. Cannot register API tools.")
            self._tool_executors[tool_name] = api_config
            self._tool_types[tool_name] = "api"
            logger.info(f"Registered API tool: {tool_name} -> {api_config.url}")
    
    def get_tool_schema(self, tool_name: str) -> ToolSchema:
        """
        获取指定工具的 schema
        
        Args:
            tool_name: 工具名称
            
        Returns:
            ToolSchema对象
            
        Raises:
            KeyError: 如果工具不存在
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        return self._tools[tool_name]
    
    def get_all_schemas(self) -> List[ToolSchema]:
        """
        获取所有已注册工具的 schema 列表
        
        Returns:
            所有 ToolSchema 的列表
        """
        return list(self._tools.values())
    
    def invoke(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        调用指定的工具（自动判断本地或 API）
        
        Args:
            tool_name: 要调用的工具名称
            args: 传递给工具的参数字典
            
        Returns:
            工具的执行结果
            
        Raises:
            KeyError: 如果工具不存在
            Exception: 工具执行过程中的任何异常
        """
        if tool_name not in self._tool_executors:
            raise KeyError(f"Tool '{tool_name}' not found in registry")
        
        tool_type = self._tool_types[tool_name]
        executor = self._tool_executors[tool_name]
        
        logger.info(f"Invoking {tool_type} tool: {tool_name} with args: {args}")
        
        try:
            if tool_type == "local":
                # 本地函数调用
                result = executor(**args)
            else:
                # API 调用
                result = self._invoke_api(executor, args)
            
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {str(e)}")
            raise
    
    def _invoke_api(self, api_config: APIConfig, args: Dict[str, Any]) -> Any:
        """
        调用远程 API
        
        Args:
            api_config: API 配置
            args: 请求参数
            
        Returns:
            API 响应数据
        """
        try:
            if api_config.method == "POST":
                response = requests.post(
                    api_config.url,
                    json=args,
                    headers=api_config.headers,
                    timeout=api_config.timeout
                )
            else:  # GET
                response = requests.get(
                    api_config.url,
                    params=args,
                    headers=api_config.headers,
                    timeout=api_config.timeout
                )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析 JSON 响应
            return response.json()
        
        except requests.exceptions.Timeout:
            raise TimeoutError(f"API call timed out after {api_config.timeout}s")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"API call failed: {str(e)}")
    
    def list_tools(self) -> List[str]:
        """
        列出所有已注册的工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def has_tool(self, tool_name: str) -> bool:
        """
        检查工具是否已注册
        
        Args:
            tool_name: 工具名称
            
        Returns:
            如果工具存在返回 True，否则返回 False
        """
        return tool_name in self._tools
    
    def get_tool_type(self, tool_name: str) -> str:
        """
        获取工具类型
        
        Args:
            tool_name: 工具名称
            
        Returns:
            "local" 或 "api"
        """
        if tool_name not in self._tool_types:
            raise KeyError(f"Tool '{tool_name}' not found")
        return self._tool_types[tool_name]
    
    def get_api_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取 API 工具的信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            API 信息字典，如果不是 API 工具则返回 None
        """
        if self.get_tool_type(tool_name) != "api":
            return None
        
        api_config = self._tool_executors[tool_name]
        return {
            "url": api_config.url,
            "method": api_config.method,
            "timeout": api_config.timeout
        }

