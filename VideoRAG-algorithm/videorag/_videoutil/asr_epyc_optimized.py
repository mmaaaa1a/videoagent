import os
import sys
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from faster_whisper import WhisperModel
from typing import List, Tuple, Dict, Any
from .epyc_config import setup_epyc_environment
import psutil
from .._storage import IntermediateStorageManager

# 设置EPYC处理器优化环境变量
def setup_epyc_optimization():
    """配置EPYC 64核心处理器的性能优化"""
    config = setup_epyc_environment()

    # PyTorch优化
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'

    # 设置日志级别减少输出开销
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)
    logging.getLogger("ctranslate2").setLevel(logging.WARNING)

    return config

class PerformanceMonitor:
    """性能监控器"""
    def __init__(self):
        self.start_time = time.time()
        self.processed_files = 0
        self.total_files = 0
        self.cpu_usage_history = []
        self.memory_usage_history = []
        self.lock = threading.Lock()

    def update_progress(self, processed_count: int = 1):
        """更新处理进度"""
        with self.lock:
            self.processed_files += processed_count
            # 记录系统性能
            self.cpu_usage_history.append(psutil.cpu_percent())
            self.memory_usage_history.append(psutil.virtual_memory().percent)

    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前性能统计"""
        with self.lock:
            elapsed_time = time.time() - self.start_time
            files_per_second = self.processed_files / elapsed_time if elapsed_time > 0 else 0
            avg_cpu = sum(self.cpu_usage_history) / len(self.cpu_usage_history) if self.cpu_usage_history else 0
            avg_memory = sum(self.memory_usage_history) / len(self.memory_usage_history) if self.memory_usage_history else 0

            return {
                "elapsed_time": elapsed_time,
                "processed_files": self.processed_files,
                "total_files": self.total_files,
                "files_per_second": files_per_second,
                "progress_percent": (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0,
                "current_cpu_usage": psutil.cpu_percent(),
                "current_memory_usage": psutil.virtual_memory().percent,
                "avg_cpu_usage": avg_cpu,
                "avg_memory_usage": avg_memory,
                "eta_seconds": (self.total_files - self.processed_files) / files_per_second if files_per_second > 0 else 0,
                "cpu_usage_history": self.cpu_usage_history.copy(),
                "memory_usage_history": self.memory_usage_history.copy()
            }

class ModelCache:
    """优化的模型缓存管理器"""
    def __init__(self, max_cache_size: int = 3):  # 减少缓存大小，避免内存过度占用
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.cache_hits = 0
        self.cache_misses = 0
        self.lock = threading.Lock()

    def get_model(self, model_name: str = "large-v3", device: str = "cpu", compute_type: str = "float32"):
        cache_key = f"{model_name}_{device}_{compute_type}"

        with self.lock:
            if cache_key in self.cache:
                self.cache_hits += 1
                return self.cache[cache_key]

            if len(self.cache) >= self.max_cache_size:
                # 移除最旧的缓存
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            self.cache_misses += 1
            model = WhisperModel(model_name, device=device, compute_type=compute_type)
            model.logger.setLevel(logging.WARNING)
            self.cache[cache_key] = model
            return model

    def get_cache_stats(self) -> Dict[str, Any]:
        with self.lock:
            total = self.cache_hits + self.cache_misses
            hit_rate = self.cache_hits / total if total > 0 else 0
            return {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "hit_rate": f"{hit_rate:.2%}",
                "cached_models": len(self.cache)
            }

class EPYCWhisperManager:
    """重构的EPYC 64核心优化Whisper管理器"""

    def __init__(self, config_override: Dict[str, Any] = None):
        # 获取EPYC配置
        self.config = setup_epyc_optimization()

        # 允许配置覆盖
        if config_override:
            self.config.update(config_override)

        self.num_models = self.config.get('num_models', 8)
        self.batch_size = self.config.get('batch_size', 16)  # 减少批量大小
        self.workers = self.config.get('workers', 32)       # 减少工作进程数，避免过度竞争
        self.compute_type = self.config.get('compute_type', 'float32')

        self.model_cache = ModelCache(max_cache_size=self.config.get('model_cache_size', 3))
        self.performance_monitor = PerformanceMonitor()

        # 预加载模型到内存
        print(f"🚀 初始化重构版EPYC优化Whisper管理器:")
        print(f"   - 模型实例数: {self.num_models}")
        print(f"   - 批量大小: {self.batch_size}")
        print(f"   - 工作进程数: {self.workers}")
        print(f"   - 计算类型: {self.compute_type}")
        print(f"   - 系统核心数: {psutil.cpu_count()}")
        print(f"   - 系统内存: {psutil.virtual_memory().total // (1024**3)}GB")

        self.models = []
        for i in range(self.num_models):
            model = self.model_cache.get_model("large-v3", "cpu", self.compute_type)
            self.models.append(model)

        print(f"✅ EPYC Whisper管理器初始化完成，内存缓存: {self.model_cache.get_cache_stats()}")

    def _process_single_file(self, args: Tuple[str, str, int]) -> Tuple[str, str, str]:
        """优化的单文件处理函数"""
        audio_file, seg_index, model_idx = args

        if not os.path.exists(audio_file):
            return (audio_file, seg_index, "")

        try:
            # 获取模型实例（轮换使用）
            model = self.models[model_idx % len(self.models)]

            # 优化参数设置 - 提升速度
            segments, info = model.transcribe(
                audio_file,
                beam_size=1,                              # 最小beam size最大化速度
                language=None,                            # 自动检测语言
                condition_on_previous_text=False,         # 减少依赖
                vad_filter=False,                         # 不使用VAD以提升速度
                word_timestamps=False,                    # 不需要词级时间戳
                temperature=0.0                           # 确定性输出
            )

            result = ""
            for segment in segments:
                result += "[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text)

            return (audio_file, seg_index, result)

        except Exception as e:
            logging.error(f"文件处理失败 {audio_file}: {e}")
            return (audio_file, seg_index, "")

    def parallel_transcribe(self, audio_files: List[Tuple[str, str]], progress_callback=None) -> List[Tuple[str, str, str]]:
        """重构的并行转录函数 - 简化架构，提升性能"""
        if not audio_files:
            return []

        start_time = time.time()

        # 初始化性能监控
        self.performance_monitor.total_files = len(audio_files)
        self.performance_monitor.processed_files = 0

        print(f"📁 开始处理 {len(audio_files)} 个音频文件")
        print(f"🎯 配置: 模型数={self.num_models}, 批量大小={self.batch_size}, 工作进程数={self.workers}")

        # 准备任务参数 - 避免嵌套线程池
        task_args = []
        for i, (audio_file, seg_index) in enumerate(audio_files):
            model_idx = i % self.num_models  # 简单的轮换策略
            task_args.append((audio_file, seg_index, model_idx))

        all_results = []

        # 使用单一线程池直接处理所有文件
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # 提交所有任务
            future_to_index = {}
            for i, args in enumerate(task_args):
                future = executor.submit(self._process_single_file, args)
                future_to_index[future] = i

            # 创建增强的进度条
            with tqdm(total=len(audio_files), desc="🎤 EPYC优化语音识别",
                     unit="文件", unit_scale=False, dynamic_ncols=True) as pbar:

                # 定期更新性能信息
                last_stats_time = time.time()

                for future in as_completed(future_to_index):
                    try:
                        result = future.result()
                        all_results.append(result)

                        # 更新进度和性能监控
                        self.performance_monitor.update_progress(1)
                        pbar.update(1)

                        # 每2秒更新一次详细性能信息
                        current_time = time.time()
                        if current_time - last_stats_time >= 2.0:
                            stats = self.performance_monitor.get_current_stats()
                            pbar.set_postfix({
                                '速度': f"{stats['files_per_second']:.2f}/s",
                                'CPU': f"{stats['current_cpu_usage']:.0f}%",
                                '内存': f"{stats['current_memory_usage']:.0f}%",
                                '进度': f"{stats['progress_percent']:.1f}%"
                            })
                            last_stats_time = current_time

                            # 调用进度回调函数
                            if progress_callback:
                                progress_info = {
                                    'current': stats['processed_files'],
                                    'total': stats['total_files'],
                                    'percentage': stats['progress_percent'],
                                    'speed': f"{stats['files_per_second']:.2f} 文件/秒",
                                    'eta': f"{stats['eta_seconds']:.0f}秒" if stats['eta_seconds'] > 0 else "",
                                    'resource_usage': {
                                        'cpu': f"{stats['current_cpu_usage']:.0f}%",
                                        'memory': f"{stats['current_memory_usage']:.0f}%"
                                    }
                                }
                                progress_callback("Transcribing Audio",
                                                 f"ASR处理中: {stats['processed_files']}/{stats['total_files']} (速度: {stats['files_per_second']:.2f}/秒)",
                                                 None, progress_info)

                    except Exception as e:
                        logging.error(f"任务执行失败: {e}")
                        # 添加空结果保持一致性
                        task_index = future_to_index[future]
                        audio_file, seg_index, _ = task_args[task_index]
                        all_results.append((audio_file, seg_index, ""))
                        pbar.update(1)

        # 最终性能统计
        total_time = time.time() - start_time
        final_stats = self.performance_monitor.get_current_stats()

        print(f"\n🎉 EPYC并行转录完成!")
        print(f"   📁 处理文件数: {len(audio_files)}")
        print(f"   ⏱️ 总耗时: {total_time:.2f}秒")
        print(f"   🚀 平均速度: {final_stats['files_per_second']:.2f}文件/秒")
        print(f"   🔥 峰值CPU使用率: {max(final_stats.get('cpu_usage_history', [0])):.0f}%")
        print(f"   💾 平均内存使用率: {final_stats['avg_memory_usage']:.0f}%")
        print(f"   📊 模型缓存统计: {self.model_cache.get_cache_stats()}")

        return all_results

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "num_models": self.num_models,
            "batch_size": self.batch_size,
            "cache_stats": self.model_cache.get_cache_stats(),
            "environment": {
                "OMP_NUM_THREADS": os.environ.get('OMP_NUM_THREADS'),
                "MKL_NUM_THREADS": os.environ.get('MKL_NUM_THREADS'),
                "OPENBLAS_NUM_THREADS": os.environ.get('OPENBLAS_NUM_THREADS')
            }
        }

# 全局EPYC管理器实例
_epyc_manager = None

def get_epyc_manager(config_override: Dict[str, Any] = None) -> EPYCWhisperManager:
    """获取全局EPYC Whisper管理器实例"""
    global _epyc_manager
    if _epyc_manager is None:
        _epyc_manager = EPYCWhisperManager(config_override=config_override)
    return _epyc_manager

def speech_to_text_epyc_optimized(video_name: str, working_dir: str, segment_index2name: Dict[str, str], audio_output_format: str, session_id: str = None, progress_callback=None) -> Dict[str, str]:
    """
    EPYC 64核心优化的语音识别函数

    Args:
        video_name: 视频名称
        working_dir: 工作目录
        segment_index2name: 片段索引到名称的映射
        audio_output_format: 音频输出格式
        session_id: 会话ID，用于中间文件存储

    Returns:
        转录结果字典 {segment_index: transcript}
    """
    print(f"🚀 开始EPYC优化语音识别: {video_name}")
    start_time = time.time()

    # 初始化中间文件存储管理器
    storage_manager = None
    if session_id:
        try:
            storage_manager = IntermediateStorageManager(session_id, working_dir)
            storage_manager.append_to_log("03_asr_transcription", f"开始EPYC优化语音识别: {video_name}")
        except Exception as e:
            logging.warning(f"无法初始化中间文件存储管理器: {e}")

    cache_path = os.path.join(working_dir, '_cache', video_name)

    # 收集所有有效的音频文件
    audio_files = []
    segment_indices = []
    valid_files = 0
    missing_files = 0

    for index in segment_index2name:
        segment_name = segment_index2name[index]
        audio_file = os.path.join(cache_path, f"{segment_name}.{audio_output_format}")

        if os.path.exists(audio_file):
            audio_files.append((audio_file, index))
            segment_indices.append(index)
            valid_files += 1
        else:
            missing_files += 1
            logging.warning(f"音频文件不存在: {audio_file}")

    if storage_manager:
        storage_manager.append_to_log("03_asr_transcription",
            f"文件检查完成: {valid_files} 个有效文件, {missing_files} 个缺失文件")

    if not audio_files:
        if storage_manager:
            storage_manager.append_to_log("03_asr_transcription", "没有找到有效的音频文件", "ERROR")
            storage_manager.save_error_log({
                "step": "03_asr_transcription",
                "error": "没有找到有效的音频文件",
                "video_name": video_name,
                "expected_files": len(segment_index2name),
                "missing_files": missing_files
            })
        print("⚠️ 没有找到有效的音频文件")
        return {}

    print(f"📁 找到 {len(audio_files)} 个音频文件待处理")

    # 保存ASR配置
    if storage_manager:
        config = {
            "video_name": video_name,
            "audio_output_format": audio_output_format,
            "total_files": len(audio_files),
            "cache_path": cache_path,
            "use_epyc_optimization": True
        }
        storage_manager.save_step_config("03_asr_transcription", config)

    # 获取EPYC管理器并并行处理
    try:
        manager = get_epyc_manager()
        results = manager.parallel_transcribe(audio_files, progress_callback)

        if storage_manager:
            storage_manager.append_to_log("03_asr_transcription",
                f"EPYC并行处理完成，获得 {len(results)} 个结果")

    except Exception as e:
        if storage_manager:
            storage_manager.append_to_log("03_asr_transcription",
                f"EPYC处理失败: {str(e)}", "ERROR")
            storage_manager.save_error_log({
                "step": "03_asr_transcription",
                "error": str(e),
                "video_name": video_name,
                "files_processed": 0
            })
        raise e

    # 构建返回结果并实时保存
    transcripts = {}
    successful_transcriptions = 0
    failed_transcriptions = 0

    for i, (audio_file, seg_index, result) in enumerate(results):
        transcripts[seg_index] = result

        if result and result.strip():
            successful_transcriptions += 1
        else:
            failed_transcriptions += 1

        # 实时保存每个片段的转录结果
        if storage_manager:
            segment_data = {
                "segment_id": seg_index,
                "audio_file": os.path.basename(audio_file),
                "transcript": result,
                "timestamp": time.time(),
                "success": bool(result and result.strip())
            }

            step_path = storage_manager._get_step_path("03_asr_transcription")
            segment_file = step_path / "transcripts_by_segment" / f"segment_{seg_index.zfill(3)}.json"
            storage_manager._atomic_write(segment_file, segment_data)

            # 每10个片段记录一次进度
            if (i + 1) % 10 == 0 and storage_manager:
                storage_manager.append_to_log("03_asr_transcription",
                    f"已处理 {i + 1}/{len(results)} 个片段")

    # 性能统计和结果保存
    total_time = time.time() - start_time
    avg_time_per_file = total_time / len(audio_files) if audio_files else 0

    # 获取EPYC性能统计
    performance_stats = manager.get_performance_stats() if 'manager' in locals() else {}

    print(f"✅ EPYC优化语音识别完成:")
    print(f"   - 处理文件数: {len(audio_files)}")
    print(f"   - 成功转录: {successful_transcriptions}")
    print(f"   - 失败转录: {failed_transcriptions}")
    print(f"   - 总耗时: {total_time:.2f}秒")
    print(f"   - 平均每文件: {avg_time_per_file:.2f}秒")
    print(f"   - 处理速度: {len(audio_files)/total_time:.2f}文件/秒")

    # 保存完整结果和统计信息
    if storage_manager:
        # 保存转录结果
        data = {
            "video_name": video_name,
            "transcripts": transcripts,
            "total_segments": len(segment_index2name),
            "processed_segments": len(audio_files),
            "successful_transcriptions": successful_transcriptions,
            "failed_transcriptions": failed_transcriptions,
            "success_rate": successful_transcriptions / len(audio_files) if audio_files else 0
        }
        storage_manager.save_step_result("03_asr_transcription", data)

        # 保存性能统计
        stats = {
            "video_name": video_name,
            "total_files": len(audio_files),
            "successful_transcriptions": successful_transcriptions,
            "failed_transcriptions": failed_transcriptions,
            "processing_time": total_time,
            "avg_time_per_file": avg_time_per_file,
            "files_per_second": len(audio_files) / total_time if total_time > 0 else 0,
            "performance_stats": performance_stats
        }
        storage_manager.save_step_stats("03_asr_transcription", stats)

        storage_manager.append_to_log("03_asr_transcription",
            f"ASR转录完成: {successful_transcriptions}/{len(audio_files)} 成功, 耗时 {total_time:.2f}s")

    return transcripts