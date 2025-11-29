"""
Data models for AstraFlow system using Pydantic
"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ToolParameter(BaseModel):
    """Schema for a tool parameter"""
    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None


class ToolParameters(BaseModel):
    """Schema for tool parameters"""
    type: Literal["object"] = "object"
    properties: Dict[str, ToolParameter]
    required: List[str] = Field(default_factory=list)


class ToolReturns(BaseModel):
    """Schema for tool return value"""
    type: str
    properties: Optional[Dict[str, Any]] = None
    items: Optional[Dict[str, Any]] = None


class ToolSchema(BaseModel):
    """
    定义一个可被注册到 ToolRegistry 的工具
    """
    name: str = Field(..., description="工具的唯一标识名称")
    description: str = Field(..., description="工具的功能描述")
    parameters: ToolParameters = Field(..., description="工具的输入参数定义")
    returns: ToolReturns = Field(..., description="工具的返回值定义")


class WorkflowStep(BaseModel):
    """
    工作流中的单个步骤
    """
    step_id: int = Field(..., description="步骤的唯一ID")
    description: str = Field(..., description="步骤的描述")
    tool_name: str = Field(..., description="要调用的工具名称")
    parameters: Dict[str, Any] = Field(..., description="传递给工具的参数")
    output_variable: str = Field(..., description="存储此步骤输出的上下文变量名")


class Workflow(BaseModel):
    """
    由 WorkflowGenerator (LLM) 生成的结构化工作流
    """
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4()}")
    original_request: str = Field(..., description="用户的原始请求")
    steps: List[WorkflowStep] = Field(..., description="工作流的步骤列表")
    created_at: datetime = Field(default_factory=datetime.now)


class StepExecutionLog(BaseModel):
    """
    单个步骤的执行日志
    """
    step_id: int
    tool_name: str
    status: Literal["success", "failure", "skipped"]
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.now)


class WorkflowEvaluation(BaseModel):
    """
    整个工作流的评估结果
    """
    overall_success: bool = Field(..., description="是否满足用户的原始需求")
    final_output: Optional[Any] = None
    failure_reason: Optional[str] = None
    human_notes: Optional[str] = None


class FeedbackLabel(BaseModel):
    """
    用于 LLM 微调的完整标签数据
    """
    label_id: str = Field(default_factory=lambda: f"label-{uuid.uuid4()}")
    workflow_id: str
    original_request: str
    generated_workflow: Workflow
    step_execution_logs: List[StepExecutionLog]
    workflow_evaluation: WorkflowEvaluation
    created_at: datetime = Field(default_factory=datetime.now)

