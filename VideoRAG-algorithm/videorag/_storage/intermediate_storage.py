"""
中间文件存储管理器
为VideoRAG视频处理流程提供完整的中间过程文件存储支持
"""

import os
import json
import time
import shutil
import tempfile
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging

class IntermediateStorageManager:
    """中间文件存储管理器，负责处理所有中间过程文件的存储和管理"""

    # 处理步骤定义
    STEPS = [
        "01_video_upload",
        "02_video_splitting",
        "03_asr_transcription",
        "04_caption_generation",
        "05_data_merging",
        "06_feature_extraction",
        "07_text_chunking",
        "08_entity_extraction",
        "09_vector_embedding",
        "10_index_construction"
    ]

    def __init__(self, session_id: str, base_storage_path: str = "./storage"):
        """
        初始化存储管理器

        Args:
            session_id: 会话ID
            base_storage_path: 基础存储路径
        """
        self.session_id = session_id
        self.base_storage_path = Path(base_storage_path)

        # 日志记录 - 在使用前先初始化
        self.logger = logging.getLogger(f"IntermediateStorage-{session_id}")
        self.logger.setLevel(logging.INFO)

        # 智能检测路径，避免重复创建会话目录
        self._setup_session_path()
        self.intermediates_path = self.session_path / "intermediates"

        # 创建必要的目录结构
        self._create_directory_structure()

    def _setup_session_path(self):
        """
        智能设置会话路径，避免重复创建会话目录

        检测base_storage_path是否已经包含会话目录，如果是则直接使用，
        否则在base_storage_path下创建会话目录
        """
        base_path_str = str(self.base_storage_path)
        expected_session_dir = f"chat-{self.session_id}"

        # 检查路径中是否已经包含会话目录
        if expected_session_dir in base_path_str:
            # 如果路径已经包含会话目录，检查是否有重复嵌套
            path_parts = self.base_storage_path.parts
            session_indices = [i for i, part in enumerate(path_parts) if part == expected_session_dir]

            if len(session_indices) > 1:
                # 发现重复嵌套，使用最后一个会话目录作为session_path
                last_session_index = session_indices[-1]
                self.session_path = Path(*path_parts[:last_session_index + 1])
                self.logger.warning(f"检测到会话目录重复嵌套，使用路径: {self.session_path}")
            elif len(session_indices) == 1:
                # 只有一个会话目录，直接使用
                session_index = session_indices[0]
                self.session_path = Path(*path_parts[:session_index + 1])
            else:
                # 虽然包含字符串但没有匹配的目录名，这种情况很少见
                self.session_path = self.base_storage_path / expected_session_dir
        else:
            # 路径中不包含会话目录，正常创建
            self.session_path = self.base_storage_path / expected_session_dir

        self.logger.info(f"会话路径设置为: {self.session_path}")

    def _create_directory_structure(self):
        """创建完整的目录结构"""
        directories = [
            self.session_path,
            self.intermediates_path,
            self.session_path / "_cache",
            self.session_path / "final_outputs" / "vector_db",
            self.session_path / "final_outputs" / "graph_db"
        ]

        # 为每个处理步骤创建目录
        for step in self.STEPS:
            step_path = self.intermediates_path / step
            directories.append(step_path)

        # ASR和字幕生成需要额外的子目录
        asr_segments_path = self.intermediates_path / "03_asr_transcription" / "transcripts_by_segment"
        caption_segments_path = self.intermediates_path / "04_caption_generation" / "captions_by_segment"
        directories.extend([asr_segments_path, caption_segments_path])

        # 创建所有目录
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_step_path(self, step_name: str) -> Path:
        """获取指定步骤的路径"""
        if step_name not in self.STEPS:
            raise ValueError(f"未知步骤: {step_name}")
        return self.intermediates_path / step_name

    def _atomic_write(self, file_path: Path, content: Union[str, bytes, Dict, Any]):
        """
        原子写入文件，确保写入的完整性

        Args:
            file_path: 目标文件路径
            content: 文件内容
        """
        # 创建临时文件
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")

        try:
            if isinstance(content, (dict, list)):
                # 处理不可序列化的对象（如DictProxy）
                serializable_content = self._make_json_serializable(content)
                # JSON数据
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_content, f, ensure_ascii=False, indent=2)
            elif isinstance(content, str):
                # 文本数据
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            elif isinstance(content, bytes):
                # 二进制数据
                with open(temp_file, 'wb') as f:
                    f.write(content)
            else:
                raise ValueError(f"不支持的数据类型: {type(content)}")

            # 原子重命名
            temp_file.rename(file_path)

        except Exception as e:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            raise e

    def _make_json_serializable(self, obj):
        """
        递归转换不可序列化的对象为可序列化形式

        Args:
            obj: 需要序列化的对象

        Returns:
            可序列化的对象
        """
        try:
            # 尝试直接序列化，如果成功则返回原对象
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # 如果失败，则进行转换

            # 特殊处理DictProxy对象
            if hasattr(obj, '__class__') and 'DictProxy' in str(type(obj)):
                # DictProxy对象需要特殊处理，将其转换为普通字典
                try:
                    # 尝试获取DictProxy的内容
                    if hasattr(obj, 'items') and callable(obj.items):
                        return {str(k): self._make_json_serializable(v) for k, v in obj.items()}
                    else:
                        # 如果无法获取items，尝试转换为字典
                        return dict(obj)
                except Exception:
                    # 如果转换失败，返回字符串表示
                    return str(obj)

            elif hasattr(obj, '__dict__'):
                # 对于有__dict__的对象，尝试转换为字典
                return {k: self._make_json_serializable(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                # 对于字典，递归处理所有键值对
                return {str(k): self._make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                # 对于列表或元组，递归处理所有元素
                return [self._make_json_serializable(item) for item in obj]
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                # 对于其他可迭代对象（除字符串和字节），转换为列表
                return [self._make_json_serializable(item) for item in obj]
            else:
                # 对于其他对象，尝试转换为字符串
                return str(obj)

    def save_step_result(self, step_name: str, data: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None):
        """
        保存处理步骤的结果

        Args:
            step_name: 步骤名称
            data: 处理结果数据
            metadata: 元数据信息
        """
        if step_name not in self.STEPS:
            raise ValueError(f"未知步骤: {step_name}")

        step_path = self._get_step_path(step_name)

        # 准备完整的结果数据
        result = {
            "step": step_name,
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        if metadata:
            result["metadata"] = metadata

        # 保存主结果文件
        self._atomic_write(step_path / f"{step_name}_result.json", result)

        # 保存步骤特定的文件
        self._save_step_specific_files(step_name, data, step_path)

        self.logger.info(f"已保存步骤 {step_name} 的结果")

    def _save_step_specific_files(self, step_name: str, data: Dict[str, Any], step_path: Path):
        """保存步骤特定的文件"""
        if step_name == "03_asr_transcription":
            # 保存每个片段的转录结果
            transcripts = data.get("transcripts", {})
            segments_path = step_path / "transcripts_by_segment"

            for segment_id, transcript in transcripts.items():
                segment_file = segments_path / f"segment_{segment_id.zfill(3)}.json"
                segment_data = {
                    "segment_id": segment_id,
                    "transcript": transcript,
                    "timestamp": datetime.now().isoformat()
                }
                self._atomic_write(segment_file, segment_data)

        elif step_name == "04_caption_generation":
            # 保存每个片段的字幕结果
            captions = data.get("captions", {})
            segments_path = step_path / "captions_by_segment"

            for segment_id, caption in captions.items():
                segment_file = segments_path / f"segment_{segment_id.zfill(3)}.json"
                segment_data = {
                    "segment_id": segment_id,
                    "caption": caption,
                    "timestamp": datetime.now().isoformat()
                }
                self._atomic_write(segment_file, segment_data)

        elif step_name == "06_feature_extraction":
            # 保存NumPy嵌入向量
            if "video_embeddings" in data:
                embeddings_file = step_path / "video_embeddings.npy"
                np.save(embeddings_file, data["video_embeddings"])

            if "audio_embeddings" in data:
                embeddings_file = step_path / "audio_embeddings.npy"
                np.save(embeddings_file, data["audio_embeddings"])

        elif step_name == "09_vector_embedding":
            # 保存文本嵌入向量
            if "text_embeddings" in data:
                embeddings_file = step_path / "text_embeddings.npy"
                np.save(embeddings_file, data["text_embeddings"])

    def save_step_config(self, step_name: str, config: Dict[str, Any]):
        """保存处理步骤的配置"""
        step_path = self._get_step_path(step_name)
        config_data = {
            "step": step_name,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
        self._atomic_write(step_path / f"{step_name}_config.json", config_data)

    def save_step_stats(self, step_name: str, stats: Dict[str, Any]):
        """保存处理步骤的统计信息"""
        step_path = self._get_step_path(step_name)
        stats_data = {
            "step": step_name,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        self._atomic_write(step_path / f"{step_name}_stats.json", stats_data)

    def append_to_log(self, step_name: str, log_message: str, level: str = "INFO"):
        """追加日志到步骤日志文件"""
        step_path = self._get_step_path(step_name)
        log_file = step_path / f"{step_name}_log.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": log_message
        }

        # 读取现有日志
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logs = []

        # 追加新日志
        logs.append(log_entry)

        # 保存日志
        self._atomic_write(log_file, logs)

    def load_step_result(self, step_name: str) -> Optional[Dict[str, Any]]:
        """加载处理步骤的结果"""
        step_path = self._get_step_path(step_name)
        result_file = step_path / f"{step_name}_result.json"

        if not result_file.exists():
            return None

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载步骤 {step_name} 结果失败: {e}")
            return None

    def load_step_config(self, step_name: str) -> Optional[Dict[str, Any]]:
        """加载处理步骤的配置"""
        step_path = self._get_step_path(step_name)
        config_file = step_path / f"{step_name}_config.json"

        if not config_file.exists():
            return None

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"加载步骤 {step_name} 配置失败: {e}")
            return None

    def get_step_status(self, step_name: str) -> str:
        """获取处理步骤的状态"""
        result = self.load_step_result(step_name)
        if result is None:
            return "not_started"
        return result.get("status", "unknown")

    def get_all_steps_status(self) -> Dict[str, str]:
        """获取所有处理步骤的状态"""
        status = {}
        for step in self.STEPS:
            status[step] = self.get_step_status(step)
        return status

    def get_processing_progress(self) -> Dict[str, Any]:
        """获取整体处理进度"""
        steps_status = self.get_all_steps_status()
        completed_steps = sum(1 for status in steps_status.values() if status == "completed")
        total_steps = len(self.STEPS)

        # 找到当前正在处理的步骤
        current_step = None
        for step, status in steps_status.items():
            if status in ["processing", "in_progress"]:
                current_step = step
                break

        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percentage": (completed_steps / total_steps) * 100,
            "current_step": current_step,
            "steps_status": steps_status,
            "session_id": self.session_id
        }

    def save_processing_summary(self, summary: Dict[str, Any]):
        """保存整体处理摘要"""
        summary_data = {
            "session_id": self.session_id,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }
        self._atomic_write(self.intermediates_path / "processing_summary.json", summary_data)

    def save_error_log(self, error_info: Dict[str, Any]):
        """保存错误日志"""
        error_data = {
            "session_id": self.session_id,
            "error": error_info,
            "timestamp": datetime.now().isoformat()
        }
        error_file = self.intermediates_path / "error_log.json"

        # 读取现有错误日志
        errors = []
        if error_file.exists():
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    errors = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                errors = []

        # 追加新错误
        errors.append(error_data)

        # 只保留最近100个错误
        if len(errors) > 100:
            errors = errors[-100:]

        self._atomic_write(error_file, errors)

    def list_intermediate_files(self, step_name: Optional[str] = None) -> Dict[str, List[str]]:
        """列出中间文件"""
        if step_name:
            if step_name not in self.STEPS:
                raise ValueError(f"未知步骤: {step_name}")
            step_path = self._get_step_path(step_name)
            files = [str(f.relative_to(self.session_path)) for f in step_path.rglob("*") if f.is_file()]
            return {step_name: files}
        else:
            result = {}
            for step in self.STEPS:
                step_path = self._get_step_path(step)
                files = [str(f.relative_to(self.session_path)) for f in step_path.rglob("*") if f.is_file()]
                if files:
                    result[step] = files
            return result

    def get_file_path(self, relative_path: str) -> Path:
        """获取文件的完整路径"""
        return self.session_path / relative_path

    def cleanup_temp_files(self):
        """清理临时文件"""
        temp_files = list(self.session_path.rglob("*.tmp"))
        for temp_file in temp_files:
            try:
                temp_file.unlink()
                self.logger.info(f"已清理临时文件: {temp_file}")
            except Exception as e:
                self.logger.warning(f"清理临时文件失败 {temp_file}: {e}")