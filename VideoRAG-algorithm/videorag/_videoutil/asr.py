import os
import logging
import time
from tqdm import tqdm
from faster_whisper import WhisperModel
from .._storage import IntermediateStorageManager

def speech_to_text(video_name, working_dir, segment_index2name, audio_output_format, use_epyc_optimization=False, session_id=None, progress_callback=None):
    """
    语音识别函数，支持传统模式和EPYC优化模式

    Args:
        video_name: 视频名称
        working_dir: 工作目录
        segment_index2name: 片段索引映射
        audio_output_format: 音频格式
        use_epyc_optimization: 是否使用EPYC优化模式
        session_id: 会话ID，用于中间文件存储
    """
    if use_epyc_optimization:
        try:
            # 尝试导入EPYC优化模块
            from .asr_epyc_optimized import speech_to_text_epyc_optimized
            print("🚀 使用EPYC 64核心优化模式")
            return speech_to_text_epyc_optimized(video_name, working_dir, segment_index2name, audio_output_format, session_id, progress_callback)
        except ImportError as e:
            print(f"⚠️ EPYC优化模块导入失败，降级到传统模式: {e}")
            use_epyc_optimization = False

    # 传统模式处理
    print("📝 使用传统语音识别模式")
    start_time = time.time()

    # 初始化中间文件存储管理器
    storage_manager = None
    if session_id:
        try:
            storage_manager = IntermediateStorageManager(session_id, working_dir)
            storage_manager.append_to_log("03_asr_transcription", f"开始传统模式语音识别: {video_name}")
        except Exception as e:
            logging.warning(f"无法初始化中间文件存储管理器: {e}")

    # 保存传统模式配置
    if storage_manager:
        config = {
            "video_name": video_name,
            "audio_output_format": audio_output_format,
            "model_name": "large-v3",
            "device": "cpu",
            "use_epyc_optimization": False,
            "total_segments": len(segment_index2name)
        }
        storage_manager.save_step_config("03_asr_transcription", config)

    # 使用faster-whisper内置模型，faster-distil-whisper-large-v3等效于large-v3
    model = WhisperModel("large-v3", device="cpu")
    model.logger.setLevel(logging.WARNING)

    cache_path = os.path.join(working_dir, '_cache', video_name)

    transcripts = {}
    successful_transcriptions = 0
    failed_transcriptions = 0
    processed_segments = 0

    for index in tqdm(segment_index2name, desc=f"Speech Recognition {video_name}"):
        segment_name = segment_index2name[index]
        audio_file = os.path.join(cache_path, f"{segment_name}.{audio_output_format}")

        # if the audio file does not exist, skip it
        if not os.path.exists(audio_file):
            transcripts[index] = ""
            failed_transcriptions += 1
            if storage_manager:
                storage_manager.append_to_log("03_asr_transcription",
                    f"跳过缺失的音频文件: {audio_file}", "WARNING")
            continue

        try:
            segments, info = model.transcribe(audio_file)

            # 处理transcribe可能返回None的情况
            if segments is None:
                transcripts[index] = ""
                failed_transcriptions += 1
                if storage_manager:
                    storage_manager.append_to_log("03_asr_transcription",
                        f"转录返回空结果: {audio_file}", "WARNING")
                continue

            result = ""
            for segment in segments:
                result += "[%.2fs -> %.2fs] %s\n" % (segment.start, segment.end, segment.text)
            transcripts[index] = result
            successful_transcriptions += 1

            # 实时保存每个片段的转录结果
            if storage_manager:
                segment_data = {
                    "segment_id": index,
                    "audio_file": os.path.basename(audio_file),
                    "transcript": result,
                    "timestamp": time.time(),
                    "info": {
                        "language": info.language if info else "unknown",
                        "language_probability": info.language_probability if info else 0.0
                    },
                    "success": bool(result and result.strip())
                }

                step_path = storage_manager._get_step_path("03_asr_transcription")
                segment_file = step_path / "transcripts_by_segment" / f"segment_{index.zfill(3)}.json"
                storage_manager._atomic_write(segment_file, segment_data)

                # 每10个片段记录一次进度
                if (processed_segments + 1) % 10 == 0:
                    storage_manager.append_to_log("03_asr_transcription",
                        f"已处理 {processed_segments + 1}/{len(segment_index2name)} 个片段")

        except Exception as e:
            transcripts[index] = ""
            failed_transcriptions += 1
            logging.error(f"转录失败 {audio_file}: {e}")
            if storage_manager:
                storage_manager.append_to_log("03_asr_transcription",
                    f"转录失败 {audio_file}: {str(e)}", "ERROR")

        processed_segments += 1

    # 性能统计
    elapsed_time = time.time() - start_time
    avg_time_per_file = elapsed_time / len(segment_index2name) if segment_index2name else 0

    print(f"✅ 传统模式语音识别完成:")
    print(f"   - 处理文件数: {len(segment_index2name)}")
    print(f"   - 成功转录: {successful_transcriptions}")
    print(f"   - 失败转录: {failed_transcriptions}")
    print(f"   - 总耗时: {elapsed_time:.2f}秒")
    print(f"   - 平均每文件: {avg_time_per_file:.2f}秒")
    print(f"   - 处理速度: {len(segment_index2name)/elapsed_time:.2f}文件/秒")

    # 保存完整结果和统计信息
    if storage_manager:
        # 保存转录结果
        data = {
            "video_name": video_name,
            "transcripts": transcripts,
            "total_segments": len(segment_index2name),
            "processed_segments": processed_segments,
            "successful_transcriptions": successful_transcriptions,
            "failed_transcriptions": failed_transcriptions,
            "success_rate": successful_transcriptions / processed_segments if processed_segments > 0 else 0
        }
        storage_manager.save_step_result("03_asr_transcription", data)

        # 保存性能统计
        stats = {
            "video_name": video_name,
            "model_name": "large-v3",
            "device": "cpu",
            "total_segments": len(segment_index2name),
            "processed_segments": processed_segments,
            "successful_transcriptions": successful_transcriptions,
            "failed_transcriptions": failed_transcriptions,
            "processing_time": elapsed_time,
            "avg_time_per_file": avg_time_per_file,
            "files_per_second": len(segment_index2name) / elapsed_time if elapsed_time > 0 else 0
        }
        storage_manager.save_step_stats("03_asr_transcription", stats)

        storage_manager.append_to_log("03_asr_transcription",
            f"传统模式ASR完成: {successful_transcriptions}/{processed_segments} 成功, 耗时 {elapsed_time:.2f}s")

    return transcripts