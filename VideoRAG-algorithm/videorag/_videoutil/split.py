import os
import time
import shutil
import numpy as np
from tqdm import tqdm
from moviepy.video import fx as vfx
from moviepy import VideoFileClip
from .._utils import logger
from .._storage import IntermediateStorageManager

def split_video(
    video_path,
    working_dir,
    segment_length,
    num_frames_per_segment,
    audio_output_format='mp3',
    session_id=None,
):
    unique_timestamp = str(int(time.time() * 1000))
    video_name = os.path.basename(video_path).split('.')[0]
    video_segment_cache_path = os.path.join(working_dir, '_cache', video_name)
    if os.path.exists(video_segment_cache_path):
        shutil.rmtree(video_segment_cache_path)
    os.makedirs(video_segment_cache_path, exist_ok=False)

    # 初始化中间文件存储管理器
    storage_manager = None
    if session_id:
        try:
            storage_manager = IntermediateStorageManager(session_id, working_dir)
        except Exception as e:
            logger.warning(f"无法初始化中间文件存储管理器: {e}")

    # 保存分割配置
    if storage_manager:
        config = {
            "video_path": video_path,
            "video_name": video_name,
            "segment_length": segment_length,
            "num_frames_per_segment": num_frames_per_segment,
            "audio_output_format": audio_output_format,
            "unique_timestamp": unique_timestamp
        }
        storage_manager.save_step_config("02_video_splitting", config)
        storage_manager.append_to_log("02_video_splitting", f"开始分割视频: {video_name}")

    start_time = time.time()
    segment_index = 0
    segment_index2name, segment_times_info = {}, {}

    try:
        with VideoFileClip(video_path) as video:

            total_video_length = int(video.duration)
            start_times = list(range(0, total_video_length, segment_length))
            # if the last segment is shorter than 5 seconds, we merged it to the last segment
            if len(start_times) > 1 and (total_video_length - start_times[-1]) < 5:
                start_times = start_times[:-1]

            if storage_manager:
                storage_manager.append_to_log("02_video_splitting", f"视频总长度: {total_video_length}秒, 计划分割为 {len(start_times)} 个片段")

            for start in tqdm(start_times, desc=f"Spliting Video {video_name}"):
                if start != start_times[-1]:
                    end = min(start + segment_length, total_video_length)
                else:
                    end = total_video_length

                subvideo = video.subclipped(start, end)
                subvideo_length = subvideo.duration
                frame_times = np.linspace(0, subvideo_length, num_frames_per_segment, endpoint=False)
                frame_times += start

                segment_index2name[f"{segment_index}"] = f"{unique_timestamp}-{segment_index}-{start}-{end}"
                segment_times_info[f"{segment_index}"] = {"frame_times": frame_times, "timestamp": (start, end)}

                # save audio
                audio_file_base_name = segment_index2name[f"{segment_index}"]
                audio_file = f'{audio_file_base_name}.{audio_output_format}'
                try:
                    subaudio = subvideo.audio
                    subaudio.write_audiofile(os.path.join(video_segment_cache_path, audio_file), codec='mp3', logger=None)

                    if storage_manager:
                        storage_manager.append_to_log("02_video_splitting",
                            f"已处理片段 {segment_index}: [{start:.2f}s - {end:.2f}s], 音频文件: {audio_file}")

                except Exception as e:
                    logger.warning(f"Warning: Failed to extract audio for video {video_name} ({start}-{end}). Probably due to lack of audio track.")
                    if storage_manager:
                        storage_manager.append_to_log("02_video_splitting",
                            f"音频提取失败片段 {segment_index}: {str(e)}", "WARNING")

                segment_index += 1

    except Exception as e:
        if storage_manager:
            storage_manager.append_to_log("02_video_splitting", f"视频分割出错: {str(e)}", "ERROR")
            storage_manager.save_error_log({
                "step": "02_video_splitting",
                "error": str(e),
                "video_path": video_path,
                "processed_segments": segment_index
            })
        raise e

    # 保存分割结果和统计信息
    if storage_manager:
        processing_time = time.time() - start_time

        # 保存分割结果
        data = {
            "video_name": video_name,
            "total_segments": segment_index,
            "segment_index2name": segment_index2name,
            "segment_times_info": {k: {
                "frame_times": v["frame_times"].tolist() if isinstance(v["frame_times"], np.ndarray) else v["frame_times"],
                "timestamp": v["timestamp"]
            } for k, v in segment_times_info.items()},
            "cache_path": video_segment_cache_path
        }
        storage_manager.save_step_result("02_video_splitting", data)

        # 保存统计信息
        stats = {
            "total_video_length": total_video_length,
            "total_segments": segment_index,
            "segment_length": segment_length,
            "frames_per_segment": num_frames_per_segment,
            "processing_time": processing_time,
            "avg_segment_time": processing_time / segment_index if segment_index > 0 else 0,
            "cache_path": video_segment_cache_path
        }
        storage_manager.save_step_stats("02_video_splitting", stats)

        storage_manager.append_to_log("02_video_splitting",
            f"视频分割完成: {segment_index} 个片段, 耗时 {processing_time:.2f}s")

    return segment_index2name, segment_times_info

def saving_video_segments(
    video_name,
    video_path,
    working_dir,
    segment_index2name,
    segment_times_info,
    error_queue,
    video_output_format='mp4',
    session_id=None,
):
    # 初始化中间文件存储管理器
    storage_manager = None
    if session_id:
        try:
            storage_manager = IntermediateStorageManager(session_id, working_dir)
        except Exception as e:
            logger.warning(f"无法初始化中间文件存储管理器: {e}")

    if storage_manager:
        storage_manager.append_to_log("02_video_splitting", f"开始保存视频片段: {video_name}")

    start_time = time.time()
    processed_segments = 0

    try:
        with VideoFileClip(video_path) as video:
            video_segment_cache_path = os.path.join(working_dir, '_cache', video_name)
            for index in tqdm(segment_index2name, desc=f"Saving Video Segments {video_name}"):
                start, end = segment_times_info[index]["timestamp"][0], segment_times_info[index]["timestamp"][1]
                video_file = f'{segment_index2name[index]}.{video_output_format}'

                try:
                    subvideo = video.subclipped(start, end)
                    subvideo.write_videofile(os.path.join(video_segment_cache_path, video_file), codec='libx264', logger=None)
                    processed_segments += 1

                    if storage_manager:
                        storage_manager.append_to_log("02_video_splitting",
                            f"已保存视频片段 {index}: [{start:.2f}s - {end:.2f}s], 文件: {video_file}")

                except Exception as segment_error:
                    if storage_manager:
                        storage_manager.append_to_log("02_video_splitting",
                            f"保存视频片段失败 {index}: {str(segment_error)}", "ERROR")
                    logger.error(f"保存视频片段失败 {index}: {segment_error}")

    except Exception as e:
        if storage_manager:
            storage_manager.append_to_log("02_video_splitting", f"保存视频片段出错: {str(e)}", "ERROR")
            storage_manager.save_error_log({
                "step": "02_video_splitting",
                "sub_step": "saving_video_segments",
                "error": str(e),
                "video_name": video_name,
                "processed_segments": processed_segments
            })
        error_queue.put(f"Error in saving_video_segments:\n {str(e)}")
        raise RuntimeError

    # 保存视频片段保存统计
    if storage_manager:
        processing_time = time.time() - start_time
        stats = {
            "video_name": video_name,
            "total_segments": len(segment_index2name),
            "processed_segments": processed_segments,
            "failed_segments": len(segment_index2name) - processed_segments,
            "video_output_format": video_output_format,
            "processing_time": processing_time,
            "avg_segment_time": processing_time / processed_segments if processed_segments > 0 else 0
        }
        storage_manager.save_step_stats("02_video_splitting", stats)
        storage_manager.append_to_log("02_video_splitting",
            f"视频片段保存完成: {processed_segments}/{len(segment_index2name)} 个片段, 耗时 {processing_time:.2f}s")