import os
import logging
import time
from tqdm import tqdm
from faster_whisper import WhisperModel

def speech_to_text(video_name, working_dir, segment_index2name, audio_output_format, use_epyc_optimization=False):
    """
    语音识别函数，支持传统模式和EPYC优化模式

    Args:
        video_name: 视频名称
        working_dir: 工作目录
        segment_index2name: 片段索引映射
        audio_output_format: 音频格式
        use_epyc_optimization: 是否使用EPYC优化模式
    """
    if use_epyc_optimization:
        try:
            # 尝试导入EPYC优化模块
            from .asr_epyc_optimized import speech_to_text_epyc_optimized
            print("🚀 使用EPYC 64核心优化模式")
            return speech_to_text_epyc_optimized(video_name, working_dir, segment_index2name, audio_output_format)
        except ImportError as e:
            print(f"⚠️ EPYC优化模块导入失败，降级到传统模式: {e}")
            use_epyc_optimization = False

    # 传统模式处理
    print("📝 使用传统语音识别模式")
    start_time = time.time()

    # 使用faster-whisper内置模型，faster-distil-whisper-large-v3等效于large-v3
    model = WhisperModel("large-v3", device="cpu")
    model.logger.setLevel(logging.WARNING)

    cache_path = os.path.join(working_dir, '_cache', video_name)

    transcripts = {}
    for index in tqdm(segment_index2name, desc=f"Speech Recognition {video_name}"):
        segment_name = segment_index2name[index]
        audio_file = os.path.join(cache_path, f"{segment_name}.{audio_output_format}")

        # if the audio file does not exist, skip it
        if not os.path.exists(audio_file):
            transcripts[index] = ""
            continue

        segments, info = model.transcribe(audio_file)

        # 处理transcribe可能返回None的情况
        if segments is None:
            transcripts[index] = ""
            continue

        result = ""
        for segment in segments:
            result += "[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text)
        transcripts[index] = result

    # 性能统计
    elapsed_time = time.time() - start_time
    avg_time_per_file = elapsed_time / len(segment_index2name) if segment_index2name else 0

    print(f"✅ 传统模式语音识别完成:")
    print(f"   - 处理文件数: {len(segment_index2name)}")
    print(f"   - 总耗时: {elapsed_time:.2f}秒")
    print(f"   - 平均每文件: {avg_time_per_file:.2f}秒")
    print(f"   - 处理速度: {len(segment_index2name)/elapsed_time:.2f}文件/秒")

    return transcripts