"""
Master Control Plane (MCP) - The workflow execution engine
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import List, Dict, Any, Tuple
import logging
import time
from .models import Workflow, StepExecutionLog
from .tool_registry import ToolRegistry
from .utils import resolve_parameters

logger = logging.getLogger(__name__)


class MasterControlPlane:
    """
    主控程序 (MCP) - 负责执行工作流
    
    MCP 是系统的核心执行引擎，负责：
    1. 按顺序执行工作流中的每个步骤
    2. 管理执行上下文（状态）
    3. 处理步骤之间的依赖关系
    4. 捕获每一步的执行结果或错误
    5. 处理执行中的错误（重试、中止）
    """
    
    def __init__(self, tool_registry: ToolRegistry, enable_retry: bool = False, max_retries: int = 3):
        """
        初始化 MCP
        
        Args:
            tool_registry: 工具注册中心
            enable_retry: 是否启用失败重试
            max_retries: 最大重试次数
        """
        self.tool_registry = tool_registry
        self.enable_retry = enable_retry
        self.max_retries = max_retries
        logger.info(f"Initialized MCP (retry: {enable_retry}, max_retries: {max_retries})")
    
    def execute(self, workflow: Workflow) -> Tuple[List[StepExecutionLog], Dict[str, Any]]:
        """
        执行工作流
        
        Args:
            workflow: 要执行的工作流
            
        Returns:
            (步骤执行日志列表, 最终的上下文状态)
        """
        logger.info(f"Starting workflow execution: {workflow.workflow_id}")
        logger.info(f"Original request: {workflow.original_request}")
        
        # 初始化上下文
        context: Dict[str, Any] = {}
        execution_logs: List[StepExecutionLog] = []
        
        # 按顺序执行每个步骤
        for step in workflow.steps:
            logger.info(f"Executing step {step.step_id}: {step.description}")
            
            # 执行步骤
            log = self._execute_step(step, context)
            execution_logs.append(log)
            
            # 检查执行状态
            if log.status == "success":
                # 将输出存入上下文
                context[step.output_variable] = log.output
                logger.info(f"Step {step.step_id} succeeded. Output stored in context['{step.output_variable}']")
            
            elif log.status == "failure":
                # 步骤失败，跳过后续步骤
                logger.error(f"Step {step.step_id} failed: {log.error}")
                logger.info(f"Aborting workflow execution. Skipping remaining steps.")
                
                # 将剩余步骤标记为 skipped
                remaining_steps = workflow.steps[workflow.steps.index(step) + 1:]
                for remaining_step in remaining_steps:
                    skipped_log = StepExecutionLog(
                        step_id=remaining_step.step_id,
                        tool_name=remaining_step.tool_name,
                        status="skipped",
                        error=f"Dependency failed: step {step.step_id}",
                        duration_ms=0
                    )
                    execution_logs.append(skipped_log)
                
                break
        
        logger.info(f"Workflow execution completed: {workflow.workflow_id}")
        return execution_logs, context
    
    def _execute_step(self, step, context: Dict[str, Any]) -> StepExecutionLog:
        """
        执行单个步骤
        
        Args:
            step: WorkflowStep 对象
            context: 当前的上下文状态
            
        Returns:
            StepExecutionLog 对象
        """
        start_time = time.time()
        
        # 检查工具是否存在
        if not self.tool_registry.has_tool(step.tool_name):
            duration_ms = (time.time() - start_time) * 1000
            return StepExecutionLog(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="failure",
                error=f"Tool '{step.tool_name}' not found in registry",
                duration_ms=duration_ms
            )
        
        # 解析参数（处理 $context 引用）
        try:
            resolved_params = resolve_parameters(step.parameters, context)
            logger.debug(f"Resolved parameters for step {step.step_id}: {resolved_params}")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return StepExecutionLog(
                step_id=step.step_id,
                tool_name=step.tool_name,
                status="failure",
                error=f"Parameter resolution failed: {str(e)}",
                duration_ms=duration_ms
            )
        
        # 执行工具（带重试）
        retries = 0
        last_error = None
        
        while retries <= (self.max_retries if self.enable_retry else 0):
            try:
                # 调用工具
                output = self.tool_registry.invoke(step.tool_name, resolved_params)
                duration_ms = (time.time() - start_time) * 1000
                
                return StepExecutionLog(
                    step_id=step.step_id,
                    tool_name=step.tool_name,
                    status="success",
                    output=output,
                    duration_ms=duration_ms
                )
            
            except Exception as e:
                last_error = str(e)
                retries += 1
                
                if self.enable_retry and retries <= self.max_retries:
                    logger.warning(f"Step {step.step_id} failed (attempt {retries}/{self.max_retries}): {last_error}")
                    logger.info(f"Retrying step {step.step_id}...")
                    time.sleep(1)  # 简单的退避策略
                else:
                    # 所有重试都失败
                    duration_ms = (time.time() - start_time) * 1000
                    return StepExecutionLog(
                        step_id=step.step_id,
                        tool_name=step.tool_name,
                        status="failure",
                        error=last_error,
                        duration_ms=duration_ms
                    )
        
        # 不应该到达这里
        duration_ms = (time.time() - start_time) * 1000
        return StepExecutionLog(
            step_id=step.step_id,
            tool_name=step.tool_name,
            status="failure",
            error=last_error or "Unknown error",
            duration_ms=duration_ms
        )

