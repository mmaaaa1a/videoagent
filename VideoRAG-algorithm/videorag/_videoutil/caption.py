import os
import time
import logging
import json
import torch
import numpy as np
from PIL import Image
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer
from moviepy.video.io.VideoFileClip import VideoFileClip
from llama_cpp import Llama
from .._storage import IntermediateStorageManager

def _make_serializable(obj):
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
                    return {str(k): _make_serializable(v) for k, v in obj.items()}
                else:
                    # 如果无法获取items，尝试转换为字典
                    return dict(obj)
            except Exception:
                # 如果转换失败，返回字符串表示
                return str(obj)

        elif hasattr(obj, '__dict__'):
            # 对于有__dict__的对象，尝试转换为字典
            return {k: _make_serializable(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            # 对于字典，递归处理所有键值对
            return {str(k): _make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            # 对于列表或元组，递归处理所有元素
            return [_make_serializable(item) for item in obj]
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
            # 对于其他可迭代对象（除字符串和字节），转换为列表
            return [_make_serializable(item) for item in obj]
        else:
            # 对于其他对象，尝试转换为字符串
            return str(obj)

def encode_video(video, frame_times):
    frames = []
    for t in frame_times:
        frames.append(video.get_frame(t))
    frames = np.stack(frames, axis=0)
    frames = [Image.fromarray(v.astype('uint8')).resize((1280, 720)) for v in frames]
    return frames
    
def segment_caption(video_name, video_path, segment_index2name, transcripts, segment_times_info, caption_result, error_queue, session_id=None, working_dir="./storage", progress_queue=None):
    try:
        # 初始化中间文件存储管理器
        storage_manager = None
        if session_id:
            try:
                storage_manager = IntermediateStorageManager(session_id, working_dir)
                storage_manager.append_to_log("04_caption_generation", f"开始字幕生成: {video_name}")
            except Exception as e:
                logging.warning(f"无法初始化中间文件存储管理器: {e}")

        # 尝试使用原有的MiniCPM-V模型，如果失败则回退到GGUF文本模型
        use_gguf = os.getenv('USE_GGUF_CAPTION', 'false').lower() == 'true'

        # 保存字幕生成配置
        if storage_manager:
            config = {
                "video_name": video_name,
                "video_path": video_path,
                "use_gguf": use_gguf,
                "total_segments": len(segment_index2name),
                "gguf_settings": {
                    "model_path": os.getenv('CAPTION_MODEL_PATH', '/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf'),
                    "context_size": int(os.getenv('GGUF_CONTEXT_SIZE', '4096')),
                    "n_threads": int(os.getenv('GGUF_N_THREADS', '32')),
                    "batch_size": int(os.getenv('GGUF_BATCH_SIZE', '64'))
                } if use_gguf else None
            }
            storage_manager.save_step_config("04_caption_generation", config)

        start_time = time.time()
        successful_captions = 0
        failed_captions = 0
        processed_segments = 0

        if use_gguf:
            # 使用GGUF模型（纯文本，基于转录生成字幕）
            model_path = os.getenv('CAPTION_MODEL_PATH', '/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf')
            if storage_manager:
                storage_manager.append_to_log("04_caption_generation", f"加载GGUF模型: {model_path}")

            model = Llama(
                model_path=model_path,
                n_ctx=int(os.getenv('GGUF_CONTEXT_SIZE', '4096')),
                n_gpu_layers=0,
                n_threads=int(os.getenv('GGUF_N_THREADS', '32')),
                verbose=False,
                n_batch=int(os.getenv('GGUF_BATCH_SIZE', '64'))
            )
        else:
            # 使用原有MiniCPM-V模型（支持图像）
            if storage_manager:
                storage_manager.append_to_log("04_caption_generation", "加载MiniCPM-V模型")

            model = AutoModel.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
            tokenizer = AutoTokenizer.from_pretrained('./MiniCPM-V-2_6-int4', trust_remote_code=True)
            model.eval()

        # 使用进度队列报告开始字幕生成
        if progress_queue:
            progress_queue.put(("Generating Captions",
                              f"开始生成字幕: {video_name} ({len(segment_index2name)} 个片段)"))

        with VideoFileClip(video_path) as video:
            for index in tqdm(segment_index2name, desc=f"Captioning Video {video_name}"):
                try:
                    frame_times = segment_times_info[index]["frame_times"]
                    video_frames = encode_video(video, frame_times)
                    segment_transcript = transcripts[index]

                    if use_gguf:
                        # GGUF模式：仅使用文本转录生成字幕
                        prompt = f"Video transcript: {segment_transcript}\n\nBased on this transcript, provide a description (caption) of the video content in English:"
                        response = model(
                            prompt,
                            max_tokens=256,
                            temperature=0.7,
                            stop=["\n\n"]
                        )
                        segment_caption = response['choices'][0]['text'].strip()
                        model_type = "GGUF"
                    else:
                        # 原有MiniCPM-V模式：支持图像理解
                        query = f"The transcript of the current video:\n{segment_transcript}.\nNow provide a description (caption) of the video in English."
                        msgs = [{'role': 'user', 'content': video_frames + [query]}]
                        params = {}
                        params["use_image_id"] = False
                        params["max_slice_nums"] = 2
                        segment_caption = model.chat(
                            image=None,
                            msgs=msgs,
                            tokenizer=tokenizer,
                            **params
                        )
                        model_type = "MiniCPM-V"

                    caption_result[index] = segment_caption.replace("\n", "")
                    successful_captions += 1

                    # 实时保存每个片段的字幕结果
                    if storage_manager:
                        segment_data = {
                            "segment_id": index,
                            "transcript": segment_transcript,
                            "caption": segment_caption.replace("\n", ""),
                            "model_type": model_type,
                            "timestamp": time.time(),
                            "frame_count": len(frame_times),
                            "success": True
                        }

                        step_path = storage_manager._get_step_path("04_caption_generation")
                        segment_file = step_path / "captions_by_segment" / f"segment_{index.zfill(3)}.json"
                        storage_manager._atomic_write(segment_file, segment_data)

                        # 每5个片段记录一次进度
                        if (processed_segments + 1) % 5 == 0:
                            storage_manager.append_to_log("04_caption_generation",
                                f"已处理 {processed_segments + 1}/{len(segment_index2name)} 个片段")

                    # 使用进度队列报告进度
                    if progress_queue and (processed_segments + 1) % 3 == 0:  # 每3个片段更新一次进度
                        current_time = time.time()
                        elapsed_time = current_time - start_time
                        avg_time_per_segment = elapsed_time / (processed_segments + 1) if processed_segments >= 0 else 0

                        speed_text = f"{1/avg_time_per_segment:.2f} 片段/秒" if avg_time_per_segment > 0 else "计算中..."
                        progress_message = f"字幕生成中: {processed_segments + 1}/{len(segment_index2name)} (速度: {speed_text})"
                        progress_queue.put(("Generating Captions", progress_message))

                    torch.cuda.empty_cache()

                except Exception as segment_error:
                    failed_captions += 1
                    caption_result[index] = f"字幕生成失败: {str(segment_error)}"
                    logging.error(f"字幕生成失败 {index}: {segment_error}")

                    if storage_manager:
                        segment_data = {
                            "segment_id": index,
                            "transcript": transcripts.get(index, ""),
                            "caption": "",
                            "model_type": model_type if 'model_type' in locals() else "unknown",
                            "timestamp": time.time(),
                            "error": str(segment_error),
                            "success": False
                        }

                        step_path = storage_manager._get_step_path("04_caption_generation")
                        segment_file = step_path / "captions_by_segment" / f"segment_{index.zfill(3)}.json"
                        storage_manager._atomic_write(segment_file, segment_data)

                        storage_manager.append_to_log("04_caption_generation",
                            f"字幕生成失败片段 {index}: {str(segment_error)}", "ERROR")

                processed_segments += 1

        # 使用进度队列报告完成
        if progress_queue:
            total_time = time.time() - start_time
            speed = f"{len(segment_index2name)/total_time:.2f} 片段/秒" if total_time > 0 else "计算完成"
            progress_message = f"字幕生成完成: {successful_captions}/{processed_segments} 成功, 耗时 {total_time:.2f}s (速度: {speed})"
            progress_queue.put(("Captions Generated", progress_message))

        # 保存完整的字幕生成结果和统计
        total_time = time.time() - start_time
        avg_time_per_segment = total_time / len(segment_index2name) if segment_index2name else 0

        if storage_manager:
            # 确保字幕结果数据是可序列化的（处理DictProxy等对象）
            serializable_captions = _make_serializable(caption_result)

            # 保存字幕结果
            data = {
                "video_name": video_name,
                "captions": serializable_captions,
                "total_segments": len(segment_index2name),
                "processed_segments": processed_segments,
                "successful_captions": successful_captions,
                "failed_captions": failed_captions,
                "success_rate": successful_captions / processed_segments if processed_segments > 0 else 0,
                "model_type": "GGUF" if use_gguf else "MiniCPM-V"
            }
            storage_manager.save_step_result("04_caption_generation", data)

            # 保存性能统计
            stats = {
                "video_name": video_name,
                "model_type": "GGUF" if use_gguf else "MiniCPM-V",
                "total_segments": len(segment_index2name),
                "processed_segments": processed_segments,
                "successful_captions": successful_captions,
                "failed_captions": failed_captions,
                "processing_time": total_time,
                "avg_time_per_segment": avg_time_per_segment,
                "segments_per_second": len(segment_index2name) / total_time if total_time > 0 else 0
            }
            storage_manager.save_step_stats("04_caption_generation", stats)

            storage_manager.append_to_log("04_caption_generation",
                f"字幕生成完成: {successful_captions}/{processed_segments} 成功, 耗时 {total_time:.2f}s")

        print(f"✅ 字幕生成完成:")
        print(f"   - 处理片段数: {processed_segments}")
        print(f"   - 成功生成: {successful_captions}")
        print(f"   - 失败生成: {failed_captions}")
        print(f"   - 模型类型: {'GGUF' if use_gguf else 'MiniCPM-V'}")
        print(f"   - 总耗时: {total_time:.2f}秒")
        print(f"   - 平均每片段: {avg_time_per_segment:.2f}秒")

    except Exception as e:
        if storage_manager:
            storage_manager.append_to_log("04_caption_generation",
                f"字幕生成过程出错: {str(e)}", "ERROR")
            storage_manager.save_error_log({
                "step": "04_caption_generation",
                "error": str(e),
                "video_name": video_name,
                "processed_segments": 'processed_segments' in locals()
            })
        error_queue.put(f"Error in segment_caption:\n {str(e)}")
        raise RuntimeError

def merge_segment_information(segment_index2name, segment_times_info, transcripts, captions, session_id=None, working_dir="./storage", video_name="unknown"):
    # 初始化中间文件存储管理器
    storage_manager = None
    if session_id:
        try:
            storage_manager = IntermediateStorageManager(session_id, working_dir)
            storage_manager.append_to_log("05_data_merging", f"开始数据合并: {video_name}")
        except Exception as e:
            logging.warning(f"无法初始化中间文件存储管理器: {e}")

    start_time = time.time()
    inserting_segments = {}
    successful_merges = 0
    failed_merges = 0

    for index in segment_index2name:
        try:
            inserting_segments[index] = {"content": None, "time": None}
            segment_name = segment_index2name[index]
            inserting_segments[index]["time"] = '-'.join(segment_name.split('-')[-2:])

            # 合并字幕和转录内容
            caption_content = captions.get(index, "")
            transcript_content = transcripts.get(index, "")

            inserting_segments[index]["content"] = f"Caption:\n{caption_content}\nTranscript:\n{transcript_content}\n\n"
            inserting_segments[index]["transcript"] = transcript_content
            inserting_segments[index]["caption"] = caption_content
            inserting_segments[index]["frame_times"] = segment_times_info[index]["frame_times"].tolist()

            # 检查合并是否成功
            if caption_content or transcript_content:
                successful_merges += 1
            else:
                failed_merges += 1

        except Exception as merge_error:
            failed_merges += 1
            inserting_segments[index] = {
                "content": f"合并失败: {str(merge_error)}",
                "time": None,
                "transcript": transcripts.get(index, ""),
                "caption": captions.get(index, ""),
                "frame_times": [],
                "error": str(merge_error)
            }
            logging.error(f"合并失败片段 {index}: {merge_error}")

            if storage_manager:
                storage_manager.append_to_log("05_data_merging",
                    f"合并失败片段 {index}: {str(merge_error)}", "ERROR")

    # 保存合并结果和统计
    total_time = time.time() - start_time

    if storage_manager:
        # 保存合并配置
        config = {
            "video_name": video_name,
            "total_segments": len(segment_index2name),
            "merge_fields": ["transcript", "caption", "frame_times", "time"]
        }
        storage_manager.save_step_config("05_data_merging", config)

        # 保存合并结果
        data = {
            "video_name": video_name,
            "inserting_segments": inserting_segments,
            "total_segments": len(segment_index2name),
            "successful_merges": successful_merges,
            "failed_merges": failed_merges,
            "merge_rate": successful_merges / len(segment_index2name) if segment_index2name else 0
        }
        storage_manager.save_step_result("05_data_merging", data)

        # 保存性能统计
        stats = {
            "video_name": video_name,
            "total_segments": len(segment_index2name),
            "successful_merges": successful_merges,
            "failed_merges": failed_merges,
            "processing_time": total_time,
            "avg_merge_time": total_time / len(segment_index2name) if segment_index2name else 0
        }
        storage_manager.save_step_stats("05_data_merging", stats)

        storage_manager.append_to_log("05_data_merging",
            f"数据合并完成: {successful_merges}/{len(segment_index2name)} 成功, 耗时 {total_time:.2f}s")

        # 生成内容摘要
        content_summary = {
            "video_name": video_name,
            "total_content_length": sum(len(seg.get("content", "")) for seg in inserting_segments.values()),
            "avg_segment_length": sum(len(seg.get("content", "")) for seg in inserting_segments.values()) / len(inserting_segments) if inserting_segments else 0,
            "segments_with_captions": sum(1 for seg in inserting_segments.values() if seg.get("caption", "").strip()),
            "segments_with_transcripts": sum(1 for seg in inserting_segments.values() if seg.get("transcript", "").strip()),
            "generation_timestamp": time.time()
        }

        summary_path = storage_manager._get_step_path("05_data_merging") / "content_summary.json"
        storage_manager._atomic_write(summary_path, content_summary)

    print(f"✅ 数据合并完成:")
    print(f"   - 总片段数: {len(segment_index2name)}")
    print(f"   - 成功合并: {successful_merges}")
    print(f"   - 失败合并: {failed_merges}")
    print(f"   - 耗时: {total_time:.2f}秒")

    return inserting_segments
        
def retrieved_segment_caption(caption_model, caption_tokenizer, refine_knowledge, retrieved_segments, video_path_db, video_segments, num_sampled_frames):
    caption_result = {}
    for this_segment in tqdm(retrieved_segments, desc='Captioning Segments for Given Query'):
        video_name = '_'.join(this_segment.split('_')[:-1])
        index = this_segment.split('_')[-1]
        video_path = video_path_db._data[video_name]
        timestamp = video_segments._data[video_name][index]["time"].split('-')
        start, end = eval(timestamp[0]), eval(timestamp[1])
        video = VideoFileClip(video_path)
        frame_times = np.linspace(start, end, num_sampled_frames, endpoint=False)
        video_frames = encode_video(video, frame_times)
        segment_transcript = video_segments._data[video_name][index]["transcript"]
        query = f"The transcript of the current video:\n{segment_transcript}.\nNow provide a very detailed description (caption) of the video in English and extract relevant information about: {refine_knowledge}'"
        msgs = [{'role': 'user', 'content': video_frames + [query]}]
        params = {}
        params["use_image_id"] = False
        params["max_slice_nums"] = 2
        segment_caption = caption_model.chat(
            image=None,
            msgs=msgs,
            tokenizer=caption_tokenizer,
            **params
        )
        this_caption = segment_caption.replace("\n", "")
        caption_result[this_segment] = f"Caption:\n{this_caption}\nTranscript:\n{segment_transcript}\n\n"
        torch.cuda.empty_cache()
    
    return caption_result
