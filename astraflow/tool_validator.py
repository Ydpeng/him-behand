"""
Tool validation and dependency checking
"""

from typing import Dict, List, Optional, Any
import subprocess
import importlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolDependency:
    """工具依赖定义"""
    
    def __init__(
        self,
        name: str,
        dependency_type: str,
        check_method: str,
        install_instructions: str,
        required: bool = True,
        version_requirement: Optional[str] = None
    ):
        """
        初始化工具依赖
        
        Args:
            name: 依赖名称
            dependency_type: 类型 (python_package, executable, file, url, model)
            check_method: 检查方法（如包名、命令名、文件路径等）
            install_instructions: 安装说明
            required: 是否必需
            version_requirement: 版本要求
        """
        self.name = name
        self.dependency_type = dependency_type
        self.check_method = check_method
        self.install_instructions = install_instructions
        self.required = required
        self.version_requirement = version_requirement


class ToolValidator:
    """
    工具验证器：检查工具的依赖是否满足
    """
    
    def __init__(self):
        self.dependency_cache: Dict[str, bool] = {}
    
    def check_python_package(self, package_name: str, version_requirement: Optional[str] = None) -> tuple[bool, str]:
        """
        检查 Python 包是否已安装
        
        Args:
            package_name: 包名
            version_requirement: 版本要求（可选）
            
        Returns:
            (是否安装, 消息)
        """
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'unknown')
            
            if version_requirement:
                # 这里可以添加版本比较逻辑
                return True, f"Package '{package_name}' version {version} is installed"
            else:
                return True, f"Package '{package_name}' is installed"
        
        except ImportError:
            return False, f"Package '{package_name}' is not installed"
    
    def check_executable(self, executable_name: str) -> tuple[bool, str]:
        """
        检查可执行文件是否在 PATH 中
        
        Args:
            executable_name: 可执行文件名
            
        Returns:
            (是否存在, 消息)
        """
        try:
            result = subprocess.run(
                ['which', executable_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                path = result.stdout.strip()
                return True, f"Executable '{executable_name}' found at {path}"
            else:
                return False, f"Executable '{executable_name}' not found in PATH"
        
        except Exception as e:
            return False, f"Error checking executable '{executable_name}': {e}"
    
    def check_file_exists(self, file_path: str) -> tuple[bool, str]:
        """
        检查文件或目录是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否存在, 消息)
        """
        path = Path(file_path).expanduser()
        
        if path.exists():
            return True, f"Path '{file_path}' exists"
        else:
            return False, f"Path '{file_path}' does not exist"
    
    def check_url_accessible(self, url: str) -> tuple[bool, str]:
        """
        检查 URL 是否可访问
        
        Args:
            url: URL 地址
            
        Returns:
            (是否可访问, 消息)
        """
        try:
            import requests
            response = requests.head(url, timeout=5)
            
            if response.status_code < 400:
                return True, f"URL '{url}' is accessible"
            else:
                return False, f"URL '{url}' returned status {response.status_code}"
        
        except ImportError:
            logger.warning("requests package not installed, skipping URL check")
            return True, "URL check skipped (requests not installed)"
        except Exception as e:
            return False, f"Error accessing URL '{url}': {e}"
    
    def check_model_available(self, model_info: Dict[str, Any]) -> tuple[bool, str]:
        """
        检查模型文件或 API 是否可用
        
        Args:
            model_info: 模型信息字典，包含 type, path/api_key 等
            
        Returns:
            (是否可用, 消息)
        """
        model_type = model_info.get('type', 'file')
        
        if model_type == 'file':
            model_path = model_info.get('path')
            return self.check_file_exists(model_path)
        
        elif model_type == 'api':
            api_key = model_info.get('api_key')
            if api_key:
                return True, "API key is configured"
            else:
                return False, "API key is not configured"
        
        else:
            return False, f"Unknown model type: {model_type}"
    
    def validate_tool_dependencies(
        self,
        tool_name: str,
        dependencies: List[ToolDependency]
    ) -> tuple[bool, List[str]]:
        """
        验证工具的所有依赖
        
        Args:
            tool_name: 工具名称
            dependencies: 依赖列表
            
        Returns:
            (所有必需依赖是否满足, 消息列表)
        """
        messages = []
        all_required_met = True
        
        logger.info(f"Validating dependencies for tool: {tool_name}")
        
        for dep in dependencies:
            cache_key = f"{dep.dependency_type}:{dep.check_method}"
            
            # 检查缓存
            if cache_key in self.dependency_cache:
                satisfied = self.dependency_cache[cache_key]
                msg = f"[Cached] {dep.name}: {'✓' if satisfied else '✗'}"
            else:
                # 执行检查
                if dep.dependency_type == "python_package":
                    satisfied, msg = self.check_python_package(dep.check_method, dep.version_requirement)
                
                elif dep.dependency_type == "executable":
                    satisfied, msg = self.check_executable(dep.check_method)
                
                elif dep.dependency_type == "file":
                    satisfied, msg = self.check_file_exists(dep.check_method)
                
                elif dep.dependency_type == "url":
                    satisfied, msg = self.check_url_accessible(dep.check_method)
                
                elif dep.dependency_type == "model":
                    model_info = {"type": "file", "path": dep.check_method}
                    satisfied, msg = self.check_model_available(model_info)
                
                else:
                    satisfied = False
                    msg = f"Unknown dependency type: {dep.dependency_type}"
                
                # 缓存结果
                self.dependency_cache[cache_key] = satisfied
            
            # 记录结果
            status = "✓" if satisfied else "✗"
            full_msg = f"{status} {dep.name}: {msg}"
            
            if not satisfied:
                full_msg += f"\n  → Install instructions: {dep.install_instructions}"
                
                if dep.required:
                    all_required_met = False
                    logger.warning(f"Required dependency not met: {dep.name}")
            
            messages.append(full_msg)
        
        return all_required_met, messages
    
    def clear_cache(self):
        """清除依赖检查缓存"""
        self.dependency_cache.clear()


def print_dependency_report(tool_name: str, messages: List[str]) -> None:
    """
    打印依赖检查报告
    
    Args:
        tool_name: 工具名称
        messages: 检查消息列表
    """
    print(f"\n{'='*80}")
    print(f"Dependency Check Report for: {tool_name}")
    print(f"{'='*80}")
    
    for msg in messages:
        print(msg)
    
    print(f"{'='*80}\n")

