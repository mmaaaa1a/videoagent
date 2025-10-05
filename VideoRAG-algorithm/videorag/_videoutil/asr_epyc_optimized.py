import os
import sys
import time
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from tqdm import tqdm
from faster_whisper import WhisperModel
from typing import List, Tuple, Dict, Any
from .epyc_config import setup_epyc_environment

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

class ModelCache:
    """模型缓存管理器，利用256GB大内存"""
    def __init__(self, max_cache_size: int = 5):
        self.cache = {}
        self.max_cache_size = max_cache_size
        self.cache_hits = 0
        self.cache_misses = 0

    def get_model(self, model_name: str = "large-v3", device: str = "cpu", compute_type: str = "float32"):
        cache_key = f"{model_name}_{device}_{compute_type}"

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
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2%}",
            "cached_models": len(self.cache)
        }

class EPYCWhisperManager:
    """EPYC 64核心优化的Whisper管理器"""

    def __init__(self, config_override: Dict[str, Any] = None):
        # 获取EPYC配置
        self.config = setup_epyc_optimization()

        # 允许配置覆盖
        if config_override:
            self.config.update(config_override)

        self.num_models = self.config.get('num_models', 8)
        self.batch_size = self.config.get('batch_size', 32)
        self.workers = self.config.get('workers', 64)
        self.compute_type = self.config.get('compute_type', 'float32')

        self.model_cache = ModelCache(max_cache_size=self.config.get('model_cache_size', 5))

        # 预加载模型到内存
        print(f"🚀 初始化EPYC优化Whisper管理器:")
        print(f"   - 模型实例数: {self.num_models}")
        print(f"   - 批量大小: {self.batch_size}")
        print(f"   - 工作进程数: {self.workers}")
        print(f"   - 计算类型: {self.compute_type}")

        self.models = []
        for i in range(self.num_models):
            model = self.model_cache.get_model("large-v3", "cpu", self.compute_type)
            self.models.append(model)

        print(f"✅ EPYC Whisper管理器初始化完成，内存缓存: {self.model_cache.get_cache_stats()}")

    def _process_single_file(self, model_idx: int, audio_file: str, seg_index: str) -> Tuple[str, str, str]:
        """处理单个音频文件"""
        if not os.path.exists(audio_file):
            return (audio_file, seg_index, "")

        try:
            # 获取模型实例（轮换使用）
            model = self.models[model_idx % len(self.models)]

            # 优化参数设置
            segments, info = model.transcribe(
                audio_file,
                beam_size=2,  # 减少beam size提升速度
                language=None,  # 自动检测语言
                condition_on_previous_text=False,  # 减少依赖
                vad_filter=False  # 不使用VAD以提升速度
            )

            result = ""
            for segment in segments:
                result += "[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text)

            return (audio_file, seg_index, result)

        except Exception as e:
            logging.error(f"文件处理失败 {audio_file}: {e}")
            return (audio_file, seg_index, "")

    def _process_batch_threaded(self, model_idx: int, batch_files: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        """使用线程池处理单个批次"""
        results = []

        # 使用线程池处理批次内的文件
        with ThreadPoolExecutor(max_workers=min(16, len(batch_files))) as executor:
            # 提交批次内的所有文件
            future_to_file = {}
            for audio_file, seg_index in batch_files:
                future = executor.submit(self._process_single_file, model_idx, audio_file, seg_index)
                future_to_file[future] = (audio_file, seg_index)

            # 收集结果
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    audio_file, seg_index = future_to_file[future]
                    logging.error(f"批次内文件处理失败 {audio_file}: {e}")
                    results.append((audio_file, seg_index, ""))

        return results

    def parallel_transcribe(self, audio_files: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        """并行转录音频文件，充分利用64核心"""
        if not audio_files:
            return []

        start_time = time.time()

        # 分批处理
        batches = []
        for i in range(0, len(audio_files), self.batch_size):
            batch = audio_files[i:i+self.batch_size]
            model_idx = (i // self.batch_size) % self.num_models
            batches.append((model_idx, batch))

        all_results = []

        # 使用进程池并行处理批次
        with ProcessPoolExecutor(max_workers=min(self.workers, len(batches))) as executor:
            # 提交所有批次任务
            future_to_batch = {}
            for model_idx, batch in batches:
                future = executor.submit(self._process_batch_threaded, model_idx, batch)
                future_to_batch[future] = batch

            # 收集结果
            with tqdm(total=len(audio_files), desc="🎤 EPYC批量语音识别") as pbar:
                for future in as_completed(future_to_batch):
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                        pbar.update(len(batch_results))
                    except Exception as e:
                        logging.error(f"批次执行失败: {e}")
                        batch = future_to_batch[future]
                        # 降级处理失败批次
                        for audio_file, seg_index in batch:
                            all_results.append((audio_file, seg_index, ""))
                        pbar.update(len(batch))

        elapsed_time = time.time() - start_time
        files_per_second = len(audio_files) / elapsed_time if elapsed_time > 0 else 0

        print(f"🎉 EPYC并行转录完成: {len(audio_files)}个文件, 耗时: {elapsed_time:.2f}秒, 速度: {files_per_second:.2f}文件/秒")
        print(f"📊 模型缓存统计: {self.model_cache.get_cache_stats()}")

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

def speech_to_text_epyc_optimized(video_name: str, working_dir: str, segment_index2name: Dict[str, str], audio_output_format: str) -> Dict[str, str]:
    """
    EPYC 64核心优化的语音识别函数

    Args:
        video_name: 视频名称
        working_dir: 工作目录
        segment_index2name: 片段索引到名称的映射
        audio_output_format: 音频输出格式

    Returns:
        转录结果字典 {segment_index: transcript}
    """
    print(f"🚀 开始EPYC优化语音识别: {video_name}")
    start_time = time.time()

    cache_path = os.path.join(working_dir, '_cache', video_name)

    # 收集所有有效的音频文件
    audio_files = []
    segment_indices = []

    for index in segment_index2name:
        segment_name = segment_index2name[index]
        audio_file = os.path.join(cache_path, f"{segment_name}.{audio_output_format}")

        if os.path.exists(audio_file):
            audio_files.append((audio_file, index))
            segment_indices.append(index)
        else:
            logging.warning(f"音频文件不存在: {audio_file}")

    if not audio_files:
        print("⚠️ 没有找到有效的音频文件")
        return {}

    print(f"📁 找到 {len(audio_files)} 个音频文件待处理")

    # 获取EPYC管理器并并行处理
    manager = get_epyc_manager()
    results = manager.parallel_transcribe(audio_files)

    # 构建返回结果
    transcripts = {}
    for audio_file, seg_index, result in results:
        transcripts[seg_index] = result

    # 性能统计
    total_time = time.time() - start_time
    avg_time_per_file = total_time / len(audio_files) if audio_files else 0

    print(f"✅ EPYC优化语音识别完成:")
    print(f"   - 处理文件数: {len(audio_files)}")
    print(f"   - 总耗时: {total_time:.2f}秒")
    print(f"   - 平均每文件: {avg_time_per_file:.2f}秒")
    print(f"   - 处理速度: {len(audio_files)/total_time:.2f}文件/秒")

    return transcripts