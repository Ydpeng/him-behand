"""
Feedback Collector for generating and storing training labels
"""

from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path
from datetime import datetime
from .models import Workflow, StepExecutionLog, WorkflowEvaluation, FeedbackLabel

logger = logging.getLogger(__name__)


class FeedbackCollector:
    """
    反馈收集器，负责收集和存储用于 LLM 微调的标签数据
    
    FeedbackCollector 聚合：
    1. WorkflowGenerator 生成的工作流
    2. MCP 的详细执行日志
    3. 用户满意度评分/工作流评估
    
    并将这些数据保存为结构化的 FeedbackLabel
    """
    
    def __init__(self, datastore_path: Optional[str] = None):
        """
        初始化 FeedbackCollector
        
        Args:
            datastore_path: 数据存储路径（默认为 ./data/feedback_labels）
        """
        self.datastore_path = Path(datastore_path) if datastore_path else Path("./data/feedback_labels")
        self.datastore_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FeedbackCollector with datastore: {self.datastore_path}")
    
    def create_label(
        self,
        workflow: Workflow,
        logs: List[StepExecutionLog],
        evaluation: WorkflowEvaluation
    ) -> FeedbackLabel:
        """
        创建一个反馈标签
        
        Args:
            workflow: 生成的工作流
            logs: 步骤执行日志列表
            evaluation: 工作流评估结果
            
        Returns:
            FeedbackLabel 对象
        """
        logger.info(f"Creating feedback label for workflow: {workflow.workflow_id}")
        
        label = FeedbackLabel(
            workflow_id=workflow.workflow_id,
            original_request=workflow.original_request,
            generated_workflow=workflow,
            step_execution_logs=logs,
            workflow_evaluation=evaluation
        )
        
        logger.info(f"Created feedback label: {label.label_id}")
        return label
    
    def save_to_datastore(self, label: FeedbackLabel) -> str:
        """
        将反馈标签保存到数据存储
        
        Args:
            label: 要保存的 FeedbackLabel
            
        Returns:
            保存的文件路径
        """
        # 生成文件名：label_id_timestamp.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{label.label_id}_{timestamp}.json"
        filepath = self.datastore_path / filename
        
        # 转换为 JSON
        label_dict = label.model_dump(mode='json')
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(label_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved feedback label to: {filepath}")
        return str(filepath)
    
    def load_label(self, label_id: str) -> Optional[FeedbackLabel]:
        """
        从数据存储加载标签
        
        Args:
            label_id: 标签 ID
            
        Returns:
            FeedbackLabel 对象，如果未找到则返回 None
        """
        # 查找匹配的文件
        matching_files = list(self.datastore_path.glob(f"{label_id}_*.json"))
        
        if not matching_files:
            logger.warning(f"Label {label_id} not found in datastore")
            return None
        
        # 加载最新的文件
        filepath = sorted(matching_files)[-1]
        
        with open(filepath, 'r', encoding='utf-8') as f:
            label_dict = json.load(f)
        
        label = FeedbackLabel(**label_dict)
        logger.info(f"Loaded label from: {filepath}")
        return label
    
    def list_labels(self, limit: Optional[int] = None) -> List[str]:
        """
        列出数据存储中的所有标签 ID
        
        Args:
            limit: 返回的最大数量（可选）
            
        Returns:
            标签 ID 列表
        """
        files = sorted(self.datastore_path.glob("label-*.json"), reverse=True)
        
        if limit:
            files = files[:limit]
        
        # 提取 label_id
        label_ids = []
        for file in files:
            # 文件名格式: label-uuid_timestamp.json
            label_id = file.stem.split('_')[0]
            label_ids.append(label_id)
        
        return label_ids
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据存储的统计信息
        
        Returns:
            包含统计数据的字典
        """
        all_files = list(self.datastore_path.glob("label-*.json"))
        
        stats = {
            "total_labels": len(all_files),
            "successful_workflows": 0,
            "failed_workflows": 0,
            "datastore_path": str(self.datastore_path)
        }
        
        # 统计成功/失败
        for file in all_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    label_dict = json.load(f)
                
                if label_dict.get("workflow_evaluation", {}).get("overall_success"):
                    stats["successful_workflows"] += 1
                else:
                    stats["failed_workflows"] += 1
            except Exception as e:
                logger.warning(f"Error reading file {file}: {e}")
        
        return stats
    
    def export_for_training(
        self,
        output_file: str,
        filter_successful_only: bool = False
    ) -> int:
        """
        导出标签数据用于 LLM 微调
        
        Args:
            output_file: 输出文件路径
            filter_successful_only: 是否只导出成功的工作流
            
        Returns:
            导出的标签数量
        """
        all_files = list(self.datastore_path.glob("label-*.json"))
        
        training_data = []
        
        for file in all_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    label_dict = json.load(f)
                
                # 过滤
                if filter_successful_only:
                    if not label_dict.get("workflow_evaluation", {}).get("overall_success"):
                        continue
                
                # 提取训练数据
                training_sample = {
                    "original_request": label_dict["original_request"],
                    "generated_workflow": label_dict["generated_workflow"],
                    "execution_logs": label_dict["step_execution_logs"],
                    "overall_success": label_dict["workflow_evaluation"]["overall_success"]
                }
                
                training_data.append(training_sample)
            
            except Exception as e:
                logger.warning(f"Error processing file {file}: {e}")
        
        # 保存训练数据
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(training_data)} training samples to {output_file}")
        return len(training_data)

