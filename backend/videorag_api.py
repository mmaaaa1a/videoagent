# type: ignore
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
import time
import threading
import multiprocessing
import base64
import pickle
import requests
import numpy as np
from typing import List
import socket
import datetime
import json
import signal
import atexit
import psutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from moviepy import VideoFileClip
import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)

from videorag._llm import LLMConfig, openai_embedding, dashscope_embedding, gpt_complete, dashscope_caption_complete, set_dashscope_embedding_config
from videorag import VideoRAG, QueryParam

# Configure supported video formats
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'}

# Log recording function
def log_to_file(message, log_file="log.txt"):
    """Log messages to file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure the log file is created in the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, log_file)

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[LOG] {message}")  # Add prefix to distinguish
    except Exception as e:
        print(f"[ERROR] Failed to write to log: {e}")
        print(f"[LOG] {message}")  # At least output to console

def validate_asr_config():
    """验证ASR配置,确保配置正确且相关依赖可用"""
    try:
        asr_config = get_asr_config()
        log_to_file(f"🔍 验证ASR配置: 模式={asr_config['mode']}, 模型={asr_config['model']}")

        # 根据模式进行不同验证
        if asr_config['mode'] == 'local':
            # 验证faster-whisper依赖
            try:
                import faster_whisper
                log_to_file(f"✅ 本地ASR验证成功 - faster-whisper可用")
                return True
            except ImportError as e:
                raise ValueError(f"本地ASR模式需要faster-whisper库: {str(e)}") from e

        elif asr_config['mode'] == 'api':
            # 验证API相关配置
            if not asr_config.get('api_key'):
                raise ValueError("API ASR模式需要配置ALI_DASHSCOPE_API_KEY")
            if not asr_config.get('base_url'):
                raise ValueError("API ASR模式需要配置ALI_DASHSCOPE_BASE_URL")

            # 尝试导入dashscope库
            try:
                import dashscope
                log_to_file(f"✅ API ASR验证成功 - DashScope SDK可用, API Key已配置")
                return True
            except ImportError as e:
                raise ValueError(f"API ASR模式需要dashscope库: {str(e)}") from e
        else:
            raise ValueError(f"无效ASR模式: {asr_config['mode']} (支持: local, api)")

    except Exception as e:
        log_to_file(f"❌ ASR配置验证失败: {str(e)}")
        raise

def get_asr_config():
    """获取ASR配置优先从环境变量读取"""
    try:
        asr_mode = os.getenv('ASR_MODE', 'local').strip().lower()

        config = {'mode': asr_mode}

        if asr_mode == 'local':
            # 本地模式配置 - 使用faster-whisper
            config.update({
                'model': os.getenv('ASR_MODEL', 'large-v3'),  # faster-whisper模型名
                'device': os.getenv('ASR_DEVICE', 'cpu'),     # CPU或CUDA
            })
        elif asr_mode == 'api':
            # API模式配置 - 使用DashScope
            config.update({
                'model': os.getenv('ASR_MODEL', 'paraformer-realtime-v2'), # DashScope模型名
                'api_key': os.getenv('ALI_DASHSCOPE_API_KEY'),
                'base_url': os.getenv('ALI_DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
                'max_concurrent': int(os.getenv('ASR_MAX_CONCURRENT', '5')),
            })
        else:
            # 如果配置错误，降级到本地模式
            log_to_file(f"⚠️ 无效ASR_MODE: {asr_mode}，降级使用本地模式")
            config = {
                'mode': 'local',
                'model': os.getenv('ASR_MODEL', 'large-v3'),
                'device': 'cpu'
            }

        return config

    except Exception as e:
        log_to_file(f"❌ ASR配置读取错误: {str(e)}，使用默认本地配置")
        return {
            'mode': 'local',
            'model': 'large-v3',
            'device': 'cpu'
        }

def create_asr_engine():
    """创建ASR引擎根据环境配置"""
    try:
        asr_config = get_asr_config()

        if asr_config['mode'] == 'local':
            # 返回VideoRAG-algorithm中的本地faster-whisper实现
            log_to_file(f"🎤 使用本地ASR模式，模型: {asr_config['model']}")
            return None  # 返回None表示使用默认的本地实现

        elif asr_config['mode'] == 'api':
            # 使用backend中的DashScope API实现
            if not asr_config.get('api_key'):
                raise ValueError("API ASR模式需要配置ALI_DASHSCOPE_API_KEY")
            log_to_file(f"🎤 使用API ASR模式，模型: {asr_config['model']}")
            return asr_config  # 返回配置表示使用API实现

        else:
            raise ValueError(f"不支持的ASR模式: {asr_config['mode']}")

    except Exception as e:
        log_to_file(f"❌ 创建ASR引擎失败: {str(e)}，降级为本地模式")
        return None  # 返回None降级到本地模式

def get_embedding_config():
    """获取嵌入配置，自动判断提供商"""
    try:
        api_url = os.getenv('EMBEDDING_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        api_key = os.getenv('EMBEDDING_API_KEY')
        model_name = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-small')
        model_dim = int(os.getenv('EMBEDDING_MODEL_DIM', '1536'))  # 默认OpenAI维度

        # 根据URL自动判断服务商
        if 'openrouter.ai' in api_url or 'api.openai.com' in api_url:
            embedding_func = openai_embedding
            if not model_name or model_name == 'text-embedding-4':
                model_name = 'text-embedding-3-small'
            if model_dim != 1536:
                model_dim = 1536  # OpenAI固定维度
        elif 'dashscope.aliyuncs.com' in api_url:
            embedding_func = dashscope_embedding
            if not model_name or model_name == 'text-embedding-3-small':
                model_name = 'text-embedding-v4'
            if model_dim != 1024:
                model_dim = 1024  # DashScope固定维度
            # 设置DashScope嵌入配置
            if api_key or os.getenv('ALI_DASHSCOPE_API_KEY'):
                config = {
                    'embedding_api_key': api_key or os.getenv('ALI_DASHSCOPE_API_KEY'),
                    'embedding_base_url': api_url
                }
                set_dashscope_embedding_config(config)
        elif 'azure' in api_url.lower():
            embedding_func = azure_openai_embedding
            if not model_name or model_name.startswith('text-embedding'):
                model_name = 'text-embedding-ada-002'  # Azure默认模型
            if model_dim != 1536:
                model_dim = 1536  # Azure OpenAI固定维度
        else:
            # 默认回退到OpenAI兼容模式
            embedding_func = openai_embedding
            if not model_name or model_name == 'text-embedding-4':
                model_name = 'text-embedding-3-small'
            model_dim = 1536

        config = {
            'func': embedding_func,
            'model_name': model_name,
            'dim': model_dim,
            'api_key': api_key,
            'base_url': api_url
        }

        log_to_file(f"🔗 嵌入配置: URL={api_url}, 模型={model_name}, 维度={model_dim}")
        return config

    except Exception as e:
        log_to_file(f"❌ 获取嵌入配置失败: {str(e)}，使用默认OpenAI配置")
        return {
            'func': openai_embedding,
            'model_name': 'text-embedding-3-small',
            'dim': 1536,
            'api_key': os.getenv('OPENAI_API_KEY'),
            'base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        }

# New: JSON status management tool function
def write_status_json(file_path: str, status_data: dict):
    """Atomic write status JSON file"""
    temp_file = file_path + ".tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        # Atomic rename
        os.rename(temp_file, file_path)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

def read_status_json(file_path: str) -> dict:
    """Read status JSON file"""
    try:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_to_file(f"⚠️ Failed to read status file {file_path}: {str(e)}")
        return {}

def get_session_status_file(chat_id: str, base_storage_path: str) -> str:
    """Get session status file path"""
    session_dir = os.path.join(base_storage_path, f"chat-{chat_id}")
    os.makedirs(session_dir, exist_ok=True)
    return os.path.join(session_dir, "status.json")

def update_session_status(chat_id: str, base_storage_path: str, status_type: str, status_data: dict):
    """Update session status"""
    status_file = get_session_status_file(chat_id, base_storage_path)
    
    # Read existing status
    current_status = read_status_json(status_file)
    
    # Update status data
    if status_type not in current_status:
        current_status[status_type] = {}
    
    current_status[status_type].update(status_data)
    current_status["last_updated"] = time.time()
    
    # Write updated status
    write_status_json(status_file, current_status)
    log_to_file(f"📝 Updated {status_type} status for {chat_id}")

class GlobalImageBindManager:
    """Global ImageBind manager, providing HTTP API interface, supporting concurrent access control"""
    
    def __init__(self):
        self.embedder = None
        self.is_initialized = False
        self.is_loaded = False
        self.usage_count = 0
        self.model_config = None
        self.model_path = None
        
        # Simple thread lock to prevent concurrent access
        self._lock = threading.Lock()
        
    def initialize(self, model_path: str):
        """Initialize configuration but do not load model"""
        with self._lock:
            self.model_path = model_path
            self.model_config = {
                "model_path": model_path,
                "configured_at": time.time()
            }
            self.is_initialized = True
            log_to_file(f"✅ ImageBind manager configured with model path: {model_path}")
            return True
                
    def ensure_imagebind_loaded(self):
        """Ensure ImageBind model is loaded"""
        with self._lock:
            if self.is_loaded:
                log_to_file("⚠️ ImageBind already loaded")
                return True
                
            if not self.is_initialized or not self.model_path:
                raise RuntimeError("ImageBind not initialized with model path")
                
            try:
                log_to_file("🔄 Loading ImageBind model...")
                
                import torch
                from imagebind.models.imagebind_model import ImageBindModel
                from videorag._utils import get_imagebind_device
                
                device = get_imagebind_device()
                log_to_file(f"📍 Using device for ImageBind: {device}")
                
                self.embedder = ImageBindModel(
                    vision_embed_dim=1280,
                    vision_num_blocks=32,
                    vision_num_heads=16,
                    text_embed_dim=1024,
                    text_num_blocks=24,
                    text_num_heads=16,
                    out_embed_dim=1024,
                    audio_drop_path=0.1,
                    imu_drop_path=0.7,
                )
                
                if not self.model_path or not os.path.exists(self.model_path):
                    raise FileNotFoundError(f"ImageBind model not found at: {self.model_path}")
                
                self.embedder.load_state_dict(torch.load(self.model_path, map_location=device))
                self.embedder = self.embedder.to(device)
                self.embedder.eval()
                
                self.model_config.update({
                    "device": str(device),
                    "loaded_at": time.time()
                })
                
                self.is_loaded = True
                log_to_file("✅ ImageBind model loaded successfully")
                return True
                        
            except Exception as e:
                log_to_file(f"❌ Failed to load ImageBind: {str(e)}")
                raise
                
    def release_imagebind(self):
        """Release ImageBind model memory"""
        with self._lock:
            if not self.is_loaded:
                log_to_file("⚠️ ImageBind not loaded, nothing to release")
                return True
                
            try:
                if self.embedder:
                    # Clean up GPU memory
                    if hasattr(self.embedder, 'to'):
                        self.embedder.to('cpu')
                    del self.embedder
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        
                self.embedder = None
                self.is_loaded = False
                log_to_file("🧹 ImageBind model released successfully")
                return True
                
            except Exception as e:
                log_to_file(f"❌ Failed to release ImageBind: {str(e)}")
                raise
                
    def encode_video_segments(self, video_batch: List[str]) -> np.ndarray:
        """Encode video segments"""
        with self._lock:
            if not self.is_loaded:
                raise RuntimeError("ImageBind not loaded")
                
            self.usage_count += 1
            
            from videorag._videoutil import encode_video_segments
            result = encode_video_segments(video_batch, self.embedder)
            log_to_file(f"🎬 Encoded {len(video_batch)} video segments")
            return result
                
    def encode_string_query(self, query: str) -> np.ndarray:
        """Encode string query"""
        with self._lock:
            if not self.is_loaded:
                raise RuntimeError("ImageBind not loaded")
                
            self.usage_count += 1
            
            try:
                from videorag._videoutil import encode_string_query
                result = encode_string_query(query, self.embedder)
                log_to_file(f"🔍 Encoded query: {query[:50]}...")
                return result
            except Exception as e:
                log_to_file(f"❌ Query encoding failed: {str(e)}")
                raise
                
    def get_status(self) -> dict:
        """Get status information"""
        with self._lock:
            return {
                "initialized": self.is_initialized,
                "loaded": self.is_loaded,
                "total_usage_count": self.usage_count,
                "model_config": self.model_config,
                "device": str(next(self.embedder.parameters()).device) if self.embedder else None
            }
        
    def cleanup(self):
        """Clean up resources"""
        self.release_imagebind()
        with self._lock:
            self.is_initialized = False
            self.model_path = None
            self.model_config = None
            log_to_file("🧹 ImageBind manager cleaned up")

class HTTPImageBindClient:
    """HTTP client, used for subprocess access to ImageBind service"""
    
    def __init__(self, base_url: str = "http://localhost:64451"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
    def encode_video_segments(self, video_batch: List[str]) -> np.ndarray:
        """Encode video segments"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/imagebind/encode/video",
                json={"video_batch": video_batch},
                timeout=1800  # 30min timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                
            result = response.json()
            if not result.get("success"):
                raise RuntimeError(f"API error: {result.get('error')}")
            
            # Decode base64 string back to numpy array
            result_b64 = result["result"]
            result_bytes = base64.b64decode(result_b64)
            embeddings = pickle.loads(result_bytes)
            log_to_file(f"Received embeddings: {embeddings}")
            
            return embeddings
            
        except Exception as e:
            log_to_file(f"❌ HTTP client video encoding error: {str(e)}")
            raise
            
    def encode_string_query(self, query: str) -> np.ndarray:
        """Encode string query"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/imagebind/encode/query",
                json={"query": query},
                timeout=1800  # 30min timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                
            result = response.json()
            if not result.get("success"):
                raise RuntimeError(f"API error: {result.get('error')}")
            
            # Decode base64 string back to numpy array
            result_b64 = result["result"]
            result_bytes = base64.b64decode(result_b64)
            embeddings = pickle.loads(result_bytes)
            
            return embeddings
            
        except Exception as e:
            log_to_file(f"❌ HTTP client query encoding error: {str(e)}")
            raise
            
    def get_status(self) -> dict:
        """Get ImageBind service status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/imagebind/status",
                timeout=30
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                
            result = response.json()
            if not result.get("success"):
                raise RuntimeError(f"API error: {result.get('error')}")
                
            return result["status"]
            
        except Exception as e:
            log_to_file(f"❌ HTTP client status check error: {str(e)}")
            raise

class VideoRAGProcessManager:
    """VideoRAG process manager - using JSON file to store state, removing Manager and Queue"""
    
    def __init__(self):
        self.global_config = None
        self.running_processes = {}
        
    def set_global_config(self, config):
        """Set global configuration"""
        log_to_file(f"🔄 Global config set: {config}")
        self.global_config = config
        return True
        
    def start_video_indexing(self, chat_id, video_path_list):
        """Start video indexing process - using JSON status file"""
        try:
            # Initialize status file
            base_storage_path = self.global_config.get("base_storage_path")
            initial_status = {
                "indexing_status": {
                    "status": "processing", 
                    "message": "Initializing AI Assistant...",
                    "current_step": "Initializing",
                    "total_videos": len(video_path_list),
                    "processed_videos": 0
                },
                "indexed_videos": [],
                "created_at": time.time()
            }
            
            status_file = get_session_status_file(chat_id, base_storage_path)
            write_status_json(status_file, initial_status)
            
            # Get current server URL
            server_url = f"http://localhost:{globals().get('SERVER_PORT', 64451)}"
            
            # Create video indexing process
            process = multiprocessing.Process(
                target=index_video_worker_process,
                args=(chat_id, video_path_list, self.global_config, server_url)
            )
            process.start()
            
            # Record process
            self.running_processes[chat_id] = {
                "process": process,
                "type": "video_indexing",
                "chat_id": chat_id,
                "started_at": time.time()
            }
            
            return True
            
        except Exception as e:
            log_to_file(f"❌ Video indexing failed: {str(e)}")
            raise
            
    def start_query_processing(self, chat_id, query):
        """Start query processing process - using JSON status file"""
        try:
            # Initialize query status
            base_storage_path = self.global_config.get("base_storage_path")
            update_session_status(chat_id, base_storage_path, "query_status", {
                "status": "processing",
                "message": "Starting query processing...",
                "current_step": "Initializing",
                "query": query,
                "answer": None,
                "started_at": time.time()
            })
            
            server_url = f"http://localhost:{globals().get('SERVER_PORT', 64451)}"
            
            # Create query processing process
            process = multiprocessing.Process(
                target=query_worker_process,
                args=(chat_id, query, self.global_config, server_url)
            )
            process.start()
            
            # Record process
            process_key = f"{chat_id}_query"
            self.running_processes[process_key] = {
                "process": process,
                "type": "query_processing",
                "chat_id": chat_id,
                "started_at": time.time()
            }
            
            return True
            
        except Exception as e:
            log_to_file(f"❌ Query processing failed: {str(e)}")
            raise
            
    def terminate_process(self, chat_id):
        """Terminate process"""
        terminated = []
        
        if chat_id in self.running_processes:
            try:
                process_info = self.running_processes[chat_id]
                if process_info["process"].is_alive():
                    log_to_file(f"🔥 Terminating process: {chat_id}")
                    process_info["process"].terminate()
                    process_info["process"].join(timeout=5)
                    
                    if process_info["process"].is_alive():
                        log_to_file(f"💀 Force killing process: {chat_id}")
                        process_info["process"].kill()
                        process_info["process"].join()
                        
                terminated.append(chat_id)
                del self.running_processes[chat_id]
            except Exception as e:
                log_to_file(f"⚠️ Process termination failed {chat_id}: {str(e)}")
        
        # Update status file
        if self.global_config:
            base_storage_path = self.global_config.get("base_storage_path")
            update_session_status(chat_id, base_storage_path, "indexing_status", {
                "status": "terminated",
                "message": "Process terminated by user",
                "current_step": "Terminated"
            })
        
        return terminated
        
    def delete_session(self, chat_id):
        """Delete session and its processes"""
        try:
            log_to_file(f"🗑️ Deleting session {chat_id}")
            terminated = self.terminate_process(chat_id)   
            log_to_file(f"🗑️ Deleted session {chat_id}, terminated processes: {terminated}")
            return True
        except Exception as e:
            log_to_file(f"❌ Failed to delete session {chat_id}: {str(e)}")
            return False
        
    def get_session_status(self, chat_id, status_type="indexing"):
        """Get session status from JSON file"""
        if not self.global_config:
            return None
            
        try:
            base_storage_path = self.global_config.get("base_storage_path")
            status_file = get_session_status_file(chat_id, base_storage_path)
            status_data = read_status_json(status_file)
            
            if status_type == "query":
                return status_data.get("query_status")
            else:
                return status_data.get("indexing_status")
                
        except Exception as e:
            log_to_file(f"❌ Failed to get session status: {str(e)}")
            return None
            
    def get_indexed_videos(self, chat_id):
        """Get indexed video list"""
        if not self.global_config:
            return []
            
        try:
            base_storage_path = self.global_config.get("base_storage_path")
            status_file = get_session_status_file(chat_id, base_storage_path)
            status_data = read_status_json(status_file)
            return status_data.get("indexed_videos", [])
        except Exception as e:
            log_to_file(f"❌ Failed to get indexed videos: {str(e)}")
            return []
        
    def get_process_status(self):
        """Get all process status"""
        status = {}
        for key, process_info in self.running_processes.items():
            status[key] = {
                "type": process_info["type"],
                "is_alive": process_info["process"].is_alive(),
                "pid": process_info["process"].pid,
                "started_at": process_info.get("started_at")
            }
        return status
                
    def cleanup(self):
        """Clean up resources - force terminate all subprocesses"""
        log_to_file("🧹 Starting process cleanup...")
        
        # First try to gracefully terminate processes
        for key, process_info in list(self.running_processes.items()):
            try:
                process = process_info["process"]
                if process.is_alive():
                    log_to_file(f"🔥 Terminating process: {key} (PID: {process.pid})")
                    process.terminate()
            except Exception as e:
                log_to_file(f"⚠️ Error terminating process {key}: {str(e)}")
        
        # Wait for processes to end
        time.sleep(2)
        
        # Force kill still alive processes
        for key, process_info in list(self.running_processes.items()):
            try:
                process = process_info["process"]
                if process.is_alive():
                    log_to_file(f"💀 Force killing process: {key} (PID: {process.pid})")
                    process.kill()
                    process.join(timeout=3)
            except Exception as e:
                log_to_file(f"⚠️ Error killing process {key}: {str(e)}")
        
        # Extra insurance: find and kill all related processes through psutil
        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline', [])
                    if cmdline and len(cmdline) > 0:
                        proc_name = cmdline[0]
                        # Find videorag related processes (but exclude current main process)
                        if (proc_info['pid'] != current_pid and 
                            ('videorag-index-' in proc_name or 'videorag-query-' in proc_name)):
                            log_to_file(f"💀 Force killing orphan process: {proc_info['pid']} - {proc_name}")
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            log_to_file(f"⚠️ Error during psutil cleanup: {str(e)}")
                
        self.running_processes.clear()
        log_to_file("🧹 Process manager cleanup completed")

global_imagebind_manager = None
process_manager = None

def get_imagebind_manager():
    """Get ImageBind manager, delayed initialization"""
    global global_imagebind_manager
    if global_imagebind_manager is None:
        global_imagebind_manager = GlobalImageBindManager()
    return global_imagebind_manager

def get_process_manager():
    """Get process manager, delayed initialization"""
    global process_manager
    if process_manager is None:
        process_manager = VideoRAGProcessManager()
    return process_manager

# Process worker function
def index_video_worker_process(chat_id, video_path_list, global_config, server_url):
    """Process version of video indexing worker - using JSON status file, removing Queue"""
    # IMMEDIATELY set process name before any other operations
    process_name = f'videorag-index-{chat_id}'
    try:
        import setproctitle
        setproctitle.setproctitle(process_name)
        # Force set the argv[0] as backup
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = process_name
    except ImportError:
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = process_name
    
    # Log the process name setting for index worker
    import os
    log_to_file(f"🔧 Index worker process {os.getpid()} set name to: {process_name}")
    
    try:
        base_storage_path = global_config.get("base_storage_path")
        
        # Define status update function
        def update_status(status_data):
            update_session_status(chat_id, base_storage_path, "indexing_status", status_data)
        
        # Update video list function
        def add_indexed_video(video_path):
            status_file = get_session_status_file(chat_id, base_storage_path)
            current_status = read_status_json(status_file)
            if "indexed_videos" not in current_status:
                current_status["indexed_videos"] = []
            current_status["indexed_videos"].append(video_path)
            current_status["last_updated"] = time.time()
            write_status_json(status_file, current_status)
        
        update_status({
            "status": "processing",
            "message": "Initializing AI Assistant...",
            "current_step": "Initializing"
        })
        
        # Create HTTP ImageBind client
        imagebind_client = HTTPImageBindClient(server_url)
        
        # Verify ImageBind service availability
        try:
            status = imagebind_client.get_status()
            if not status["initialized"]:
                raise RuntimeError("ImageBind not initialized in main process")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to ImageBind service: {str(e)}")
        
        # Get ASR configuration
        asr_config = get_asr_config()
        log_to_file(f"🎤 ASR配置: 模式={asr_config['mode']}, 模型={asr_config['model']}")

        # Create VideoRAG instance
        session_working_dir = os.path.join(base_storage_path, f"chat-{chat_id}")
        os.makedirs(session_working_dir, exist_ok=True)

        # 获取动态嵌入配置
        embedding_config = get_embedding_config()

        videorag_llm_config = LLMConfig(
            embedding_func_raw=embedding_config['func'],
            embedding_model_name=embedding_config['model_name'],
            embedding_dim=embedding_config['dim'],
            embedding_max_token_size=8192,
            embedding_batch_num=32,
            embedding_func_max_async=16,
            query_better_than_threshold=0.2,
            best_model_func_raw=gpt_complete,
            best_model_name=global_config.get("analysisModel"),
            best_model_max_token_size=32768,
            best_model_max_async=16,
            cheap_model_func_raw=gpt_complete,
            cheap_model_name=global_config.get("processingModel"),
            cheap_model_max_token_size=32768,
            cheap_model_max_async=16,
            caption_model_func_raw=dashscope_caption_complete,
            caption_model_name=global_config.get("caption_model"),
            caption_model_max_async=3
        )

        # 将额外配置传递给addon_params，避免传递不支持的关键字参数
        addon_params = {
            "ali_dashscope_api_key": global_config.get("ali_dashscope_api_key"),
            "ali_dashscope_base_url": global_config.get("ali_dashscope_base_url"),
            "caption_model": global_config.get("caption_model"),
            "openai_api_key": global_config.get("openai_api_key"),
            "openai_base_url": global_config.get("openai_base_url"),
            "imagebind_client": imagebind_client,
        }

        videorag_instance = VideoRAG(
            llm=videorag_llm_config,
            working_dir=session_working_dir,
            asr_config=asr_config,  # 使用ASR配置对象
            addon_params=addon_params,  # 传递额外配置
        )

        # Define progress callback - directly write to JSON file
        def progress_callback(step_name, message, indexed_video_path=None):
            status_data = {
                "status": "processing" if step_name != "Completed" else "completed",
                "message": message,
                "current_step": step_name
            }
            update_status(status_data)
            
            # If a video is completed, add it to the indexed list
            if indexed_video_path and step_name == "One Video Completed":
                add_indexed_video(indexed_video_path)
        
        # Call insert_video
        videorag_instance.insert_video(
            video_path_list=video_path_list, 
            progress_callback=progress_callback
        )
        
        update_status({
            "status": "completed",
            "message": "All videos processed successfully",
            "current_step": "Completed"
        })
        
        log_to_file(f"✅ Process-based video indexing completed: {chat_id}")
        
    except Exception as e:
        base_storage_path = global_config.get("base_storage_path")
        update_session_status(chat_id, base_storage_path, "indexing_status", {
            "status": "error", 
            "message": f"Video indexing failed: {str(e)}",
            "current_step": "Error"
        })
        log_to_file(f"❌ Process-based video indexing failed: {str(e)}")

def query_worker_process(chat_id, query, global_config, server_url):
    """Query processing worker process - using JSON status file, removing Queue"""
    # IMMEDIATELY set process name before any other operations
    process_name = f'videorag-query-{chat_id}'
    try:
        import setproctitle
        setproctitle.setproctitle(process_name)
        # Force set the argv[0] as backup
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = process_name
    except ImportError:
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = process_name
    
    # Log the process name setting for query worker
    import os
    log_to_file(f"🔧 Query worker process {os.getpid()} set name to: {process_name}")
    
    try:
        base_storage_path = global_config.get("base_storage_path")
        
        # Define status update function
        def update_query_status(status_data):
            update_session_status(chat_id, base_storage_path, "query_status", status_data)
        
        log_to_file(f"🔄 Starting query processing for chat {chat_id}: {query}")
        
        # Step 1: Initializing
        update_query_status({
            "status": "processing",
            "message": "Initializing query processing...",
            "current_step": "Initializing",
            "query": query
        })
        
        # Create HTTP ImageBind client
        imagebind_client = HTTPImageBindClient(server_url)
        
        # Verify ImageBind service availability
        try:
            status = imagebind_client.get_status()
            if not status["initialized"]:
                raise RuntimeError("ImageBind not initialized in main process")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to ImageBind service: {str(e)}")

        # Create VideoRAG instance
        session_working_dir = os.path.join(base_storage_path, f"chat-{chat_id}")
        assert os.path.exists(session_working_dir), f"Session working directory does not exist: {session_working_dir}"

        videorag_llm_config = LLMConfig(
            embedding_func_raw=openai_embedding,
            embedding_model_name="text-embedding-3-small",
            embedding_dim=1536,
            embedding_max_token_size=8192,
            embedding_batch_num=32,
            embedding_func_max_async=16,
            query_better_than_threshold=0.2,
            best_model_func_raw=gpt_complete,
            best_model_name=global_config.get("analysisModel"),    
            best_model_max_token_size=32768,
            best_model_max_async=16,
            cheap_model_func_raw=gpt_complete,
            cheap_model_name=global_config.get("processingModel"),
            cheap_model_max_token_size=32768,
            cheap_model_max_async=16,
            caption_model_func_raw=dashscope_caption_complete,
            caption_model_name=global_config.get("caption_model"),
            caption_model_max_async=3
        )

        # Get ASR configuration for query processing
        asr_config = get_asr_config()
        log_to_file(f"🎤 Query ASR配置: 模式={asr_config['mode']}, 模型={asr_config['model']}")

        # 将额外配置传递给addon_params，避免传递不支持的关键字参数
        addon_params = {
            "ali_dashscope_api_key": global_config.get("ali_dashscope_api_key"),
            "ali_dashscope_base_url": global_config.get("ali_dashscope_base_url"),
            "caption_model": global_config.get("caption_model"),
            "openai_api_key": global_config.get("openai_api_key"),
            "openai_base_url": global_config.get("openai_base_url"),
            "imagebind_client": imagebind_client,
        }

        videorag_instance = VideoRAG(
            llm=videorag_llm_config,
            working_dir=session_working_dir,
            asr_config=asr_config,  # 使用ASR配置对象
            addon_params=addon_params,  # 传递额外配置
        )

        # Step 2: Processing
        update_query_status({
            "status": "processing", 
            "message": "Processing your query...",
            "current_step": "Processing",
            "query": query
        })
        
        param = QueryParam(mode="videorag")
        param.wo_reference = True
        response = videorag_instance.query(query=query, param=param)

        # Step 3: Completed
        update_query_status({
            "status": "completed",
            "message": "Query processing completed",
            "current_step": "Completed", 
            "query": query,
            "answer": response,
        })
        
        log_to_file(f"✅ Query processing completed for chat {chat_id}")
        
    except Exception as e:
        base_storage_path = global_config.get("base_storage_path")
        update_session_status(chat_id, base_storage_path, "query_status", {
            "status": "error",
            "message": f"Query processing failed: {str(e)}",
            "current_step": "Error",
            "query": query
        })
        log_to_file(f"❌ Query processing failed: {str(e)}")

# Flask application factory function
def create_app():
    """Create Flask application instance"""
    app = Flask(__name__)
    # 配置CORS，使用环境变量
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    if cors_origins == '*':
        CORS(app, origins="*", allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
    else:
        # 支持多个域名，用逗号分隔
        allowed_origins = [origin.strip() for origin in cors_origins.split(',')]
        CORS(app, origins=allowed_origins, allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
    
    # Register all routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Register all routes to Flask application"""
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check"""
        return jsonify({"status": "ok", "message": "VideoRAG API is running"})

    @app.route('/api/video/duration', methods=['POST'])
    def get_video_duration():
        """Get video duration information"""
        try:
            data = request.json
            video_path = data.get('video_path')
            with VideoFileClip(video_path) as clip:
                duration = clip.duration
                fps = clip.fps
                size = clip.size
                result = {
                    "success": True,
                    "duration": duration,
                    "fps": fps,
                    "width": size[0],
                    "height": size[1],
                    "video_path": video_path
                }
            log_to_file(f"🔍 Video duration: {result}")
            return jsonify(result)
        except Exception as e:
            log_to_file(f"❌ Video duration extraction error: {str(e)}")
            return jsonify({
                "success": False, 
                "error": f"Duration extraction error: {str(e)}"
            }), 500

    # ================= VideoRAG Default Configuration API =================

    @app.route('/api/videorag/defaults', methods=['GET'])
    def get_defaults():
        """获取VideoRAG系统默认配置 (从环境变量)"""
        try:
            # 从环境变量读取默认配置
            defaults = {
                # OpenAI配置
                "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "openai_api_key": "",  # API密钥不应通过此端点返回，出于安全考虑
                "processing_model": os.getenv("PROCESSING_MODEL", "gpt-4o-mini"),
                "analysis_model": os.getenv("ANALYSIS_MODEL", "gpt-4o-mini"),

                # DashScope配置
                "dashscope_api_key": "",  # API密钥不应通过此端点返回，出于安全考虑
                "dashscope_base_url": os.getenv("ALI_DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                "caption_model": os.getenv("CAPTION_MODEL", "qwen-vl-plus-latest"),
                "asr_model": os.getenv("ASR_MODEL", "paraformer-realtime-v2"),

                # 系统配置
                "store_directory": os.getenv("BASE_STORAGE_PATH", "/app/storage"),
                "imagebind_model_directory": os.getenv("IMAGEBIND_MODEL_PATH", "/app/models"),
                "selected_imagebind_model": "huge",  # 目前固定为huge模型
            }

            log_to_file(f"🔄 Returning default configuration from environment variables")

            return jsonify({
                "success": True,
                "defaults": defaults
            })

        except Exception as e:
            log_to_file(f"❌ Failed to get default configuration: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Failed to get default configuration: {str(e)}"
            }), 500

    @app.route('/api/initialize', methods=['POST'])
    def initialize_system():
        """初始化系统配置但不加载ImageBind模型"""
        try:
            config = request.json
            get_process_manager().set_global_config(config)
            
            # 只初始化ImageBind管理器配置，不加载模型
            model_path = config.get("image_bind_model_path")
            if model_path:
                get_imagebind_manager().initialize(model_path)
            
            return jsonify({
                "success": True, 
                "message": "VideoRAG system configuration set successfully",
                "imagebind_status": get_imagebind_manager().get_status()
            })
                
        except Exception as e:
            log_to_file(f"❌ Configuration error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Configuration error: {str(e)}"
            }), 500

    @app.route('/api/config/update', methods=['POST'])
    def update_system_config():
        """更新系统配置（用于已初始化系统的配置更新）"""
        try:
            config = request.json
            pm = get_process_manager()

            # 如果已有全局配置，进行合并更新
            if pm.global_config:
                pm.global_config.update(config)
                log_to_file(f"🔄 Updated global config: {config}")
            else:
                # 如果没有全局配置，直接设置
                pm.set_global_config(config)

            # 如果更新了ImageBind模型路径，重新初始化ImageBind管理器
            model_path = config.get("image_bind_model_path")
            if model_path:
                get_imagebind_manager().initialize(model_path)

            return jsonify({
                "success": True,
                "message": "System configuration updated successfully",
                "updated_config": pm.global_config
            })

        except Exception as e:
            log_to_file(f"❌ Configuration update error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Configuration update error: {str(e)}"
            }), 500


    @app.route('/api/imagebind/status', methods=['GET'])
    def get_imagebind_status():
        """获取ImageBind状态"""
        try:
            status = get_imagebind_manager().get_status()
            return jsonify({
                "success": True,
                "status": status
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Status check error: {str(e)}"
            }), 500

    @app.route('/api/imagebind/encode/video', methods=['POST'])
    def encode_video_segments_api():
        """编码视频段的API接口"""
        try:
            data = request.json
            video_batch = data.get('video_batch', [])
            
            if not video_batch:
                return jsonify({
                    "success": False,
                    "error": "video_batch is required"
                }), 400
                
            # Verify file existence
            for video_path in video_batch:
                if not os.path.exists(video_path):
                    return jsonify({
                        "success": False,
                        "error": f"Video file not found: {video_path}"
                    }), 400
            
            # Encode video
            log_to_file(f"🎬 Encoding {video_batch} video segments")
            result = get_imagebind_manager().encode_video_segments(video_batch).numpy()
            # Convert numpy array to base64 string for transmission
            result_bytes = pickle.dumps(result)
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            
            return jsonify({
                "success": True,
                "result": result_b64,
                "shape": result.shape,
                "dtype": str(result.dtype),
                "batch_size": len(video_batch)
            })
                
        except Exception as e:
            log_to_file(f"❌ Video encoding API error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Video encoding error: {str(e)}"
            }), 500

    @app.route('/api/imagebind/encode/query', methods=['POST'])
    def encode_string_query_api():
        """Encode string query API interface"""
        try:
            data = request.json
            query = data.get('query', '').strip()
            
            if not query:
                return jsonify({
                    "success": False,
                    "error": "query is required"
                }), 400
            
            # Encode query
            result = get_imagebind_manager().encode_string_query(query).numpy()
            
            # Convert numpy array to base64 string for transmission
            result_bytes = pickle.dumps(result)
            result_b64 = base64.b64encode(result_bytes).decode('utf-8')
            
            return jsonify({
                "success": True,
                "result": result_b64,
                "shape": result.shape,
                "dtype": str(result.dtype),
                "query": query
            })
            
        except Exception as e:
            log_to_file(f"❌ Query encoding API error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Query encoding error: {str(e)}"
            }), 500

    # ================= ImageBind Model Management APIs =================

    @app.route('/api/imagebind/models', methods=['GET'])
    def get_available_models():
        """获取可用的ImageBind模型列表"""
        try:
            # 当前只支持huge模型，预留接口用于未来扩展
            models = {
                "huge": {
                    "name": "ImageBind Huge",
                    "size": "4.5GB",
                    "description": "完整版ImageBind模型，支持所有模态",
                    "url": "https://dl.fbaipublicfiles.com/imagebind/imagebind_huge.pth",
                    "filename": "imagebind.pth"
                }
            }

            return jsonify({
                "success": True,
                "models": models,
                "default_model": "huge"
            })
        except Exception as e:
            log_to_file(f"❌ Get models error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Failed to get available models: {str(e)}"
            }), 500

    @app.route('/api/imagebind/check-status', methods=['POST'])
    def check_model_status():
        """检查指定目录中的ImageBind模型状态"""
        try:
            data = request.json
            model_directory = data.get('model_directory', '/app/models')

            if not model_directory:
                return jsonify({
                    "success": False,
                    "error": "model_directory is required"
                }), 400

            # 检查目录是否存在
            if not os.path.exists(model_directory):
                return jsonify({
                    "success": True,
                    "exists": False,
                    "message": "Model directory does not exist",
                    "directory": model_directory
                })

            # 检查模型文件是否存在
            model_path = os.path.join(model_directory, 'imagebind.pth')
            if os.path.exists(model_path):
                file_size = os.path.getsize(model_path)
                expected_size = 4.5 * 1024 * 1024 * 1024  # 4.5GB

                # 检查是否为临时下载文件
                temp_path = model_path + '.download'
                is_downloading = os.path.exists(temp_path)

                return jsonify({
                    "success": True,
                    "exists": True,
                    "model_path": model_path,
                    "file_size": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "is_complete": file_size >= expected_size * 0.95,  # 95% 阈值
                    "is_downloading": is_downloading,
                    "directory": model_directory
                })
            else:
                return jsonify({
                    "success": True,
                    "exists": False,
                    "message": "Model file not found",
                    "model_path": model_path,
                    "directory": model_directory
                })

        except Exception as e:
            log_to_file(f"❌ Model status check error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Model status check failed: {str(e)}"
            }), 500

    @app.route('/api/imagebind/download', methods=['POST'])
    def download_imagebind_model():
        """下载ImageBind模型到指定目录"""
        try:
            import requests
            import threading
            import time

            data = request.json
            model_type = data.get('model_type', 'huge')
            model_directory = data.get('model_directory', '/app/models')

            if not model_directory:
                return jsonify({
                    "success": False,
                    "error": "model_directory is required"
                }), 400

            # 创建下载进度跟踪
            download_progress = {
                'status': 'preparing',
                'progress': 0,
                'speed': 0,
                'eta': 0,
                'total_size': 0,
                'downloaded_size': 0,
                'error': None
            }

            # 确保目录存在
            os.makedirs(model_directory, exist_ok=True)

            # 获取模型信息
            models_response = get_available_models()
            if not models_response.json['success']:
                return models_response

            models = models_response.json['models']
            if model_type not in models:
                return jsonify({
                    "success": False,
                    "error": f"Model type '{model_type}' not supported"
                }), 400

            model_info = models[model_type]
            url = model_info['url']
            filename = model_info['filename']
            target_path = os.path.join(model_directory, filename)
            temp_path = target_path + '.download'

            # 检查是否已经存在完整文件
            if os.path.exists(target_path):
                file_size = os.path.getsize(target_path)
                expected_size = 4.5 * 1024 * 1024 * 1024  # 4.5GB
                if file_size >= expected_size * 0.95:  # 95% 阈值
                    return jsonify({
                        "success": True,
                        "message": "Model already exists",
                        "model_path": target_path,
                        "status": "completed"
                    })

            # 检查是否有正在进行的下载
            if os.path.exists(temp_path):
                download_progress['status'] = 'resuming'
                # 获取已下载的大小
                downloaded_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
                download_progress['downloaded_size'] = downloaded_size
            else:
                download_progress['status'] = 'starting'

            # 启动后台下载线程
            def download_worker():
                try:
                    download_progress['status'] = 'downloading'

                    # 使用Range header支持断点续传
                    headers = {}
                    downloaded_size = 0

                    if os.path.exists(temp_path):
                        downloaded_size = os.path.getsize(temp_path)
                        headers['Range'] = f'bytes={downloaded_size}-'

                    response = requests.get(url, headers=headers, stream=True, timeout=30)

                    if response.status_code not in [200, 206]:  # 206表示断点续传
                        download_progress['error'] = f'HTTP {response.status_code}: {response.reason}'
                        download_progress['status'] = 'error'
                        return

                    total_size = int(response.headers.get('content-length', 0))
                    if downloaded_size == 0 and 'content-range' in response.headers:
                        # 解析content-range
                        content_range = response.headers['content-range']
                        total_size = int(content_range.split('/')[-1])

                    download_progress['total_size'] = total_size

                    # 下载文件
                    start_time = time.time()
                    chunk_size = 8192
                    bytes_downloaded = downloaded_size

                    with open(temp_path, 'ab' if downloaded_size > 0 else 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
                                bytes_downloaded += len(chunk)

                                # 计算进度
                                if total_size > 0:
                                    progress = (bytes_downloaded / total_size) * 100
                                    download_progress['progress'] = progress
                                    download_progress['downloaded_size'] = bytes_downloaded

                                    # 计算速度
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = bytes_downloaded / elapsed_time  # bytes per second
                                        download_progress['speed'] = speed

                                        # 估算剩余时间
                                        remaining_bytes = total_size - bytes_downloaded
                                        if speed > 0:
                                            eta = remaining_bytes / speed
                                            download_progress['eta'] = eta

                    # 下载完成，重命名文件
                    os.rename(temp_path, target_path)
                    download_progress['status'] = 'completed'
                    download_progress['progress'] = 100.0

                    log_to_file(f"✅ ImageBind model downloaded successfully: {target_path}")

                except Exception as e:
                    download_progress['error'] = str(e)
                    download_progress['status'] = 'error'
                    log_to_file(f"❌ Model download failed: {str(e)}")

                    # 清理临时文件如果下载失败
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except:
                            pass

            # 启动下载线程
            download_thread = threading.Thread(target=download_worker, daemon=True)
            download_thread.start()

            return jsonify({
                "success": True,
                "message": "Model download started",
                "model_type": model_type,
                "target_path": target_path,
                "status": download_progress['status']
            })

        except Exception as e:
            log_to_file(f"❌ Download API error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Download failed: {str(e)}"
            }), 500

    @app.route('/api/imagebind/download-progress', methods=['GET'])
    def get_download_progress():
        """获取当前下载进度"""
        try:
            # 注意：这是一个简化的实现，实际项目中应该使用更持久的进度存储
            return jsonify({
                "success": True,
                "message": "Progress tracking not implemented in this demo. "
                          "Use check-model-status to verify download completion.",
                "status": "unknown"
            })
        except Exception as e:
            log_to_file(f"❌ Progress API error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Progress check failed: {str(e)}"
            }), 500

    # ================= End ImageBind Model Management APIs =================

    @app.route('/api/sessions/<chat_id>/videos/upload', methods=['POST'])
    def upload_video(chat_id):
        """Upload video for specific chat session and start indexing - asynchronous operation"""
        log_to_file(f"📝 API: Starting async video upload for chat_id: {chat_id}")
        
        try:
            data = request.json
            video_path_list = data.get('video_path_list', [])
            
            if not video_path_list:
                return jsonify({
                    "success": False, 
                    "error": "video_path_list is required"
                }), 400

            log_to_file(f"📹 Videos to process: {len(video_path_list)}")

            for path in video_path_list:
                if not path or not os.path.exists(path):
                    return jsonify({
                        "success": False, 
                        "error": f"Invalid video path: {path}"
                    }), 400

            # Get video name list
            video_names = [os.path.basename(path).split('.')[0] for path in video_path_list]
            
            log_to_file(f"🚀 Starting background video processing for {chat_id}")
            
            # Start background indexing process
            get_process_manager().start_video_indexing(chat_id, video_path_list)
            
            # Immediately return success response
            return jsonify({
                "success": True, 
                "message": "Video processing started",
                "video_names": video_names,
                "video_count": len(video_path_list),
                "chat_id": chat_id,
                "status": "started"
            })
            
        except Exception as e:
            error_msg = f"Failed to start video processing: {str(e)}"
            log_to_file(f"❌ {error_msg}")
            return jsonify({
                "success": False, 
                "error": error_msg
            }), 500

    @app.route('/api/sessions/<chat_id>/status', methods=['GET'])
    def get_indexing_status(chat_id):
        """Get indexing status for specific session"""
        try:
            # Check if this is a query status request
            query_type = request.args.get('type', 'indexing')
            
            if query_type == 'query':
                # Return query processing status
                status_info = get_process_manager().get_session_status(chat_id, "query")
                if not status_info:
                    return jsonify({
                        "success": False, 
                        "error": "Query status not found",
                        "status": "not_found"
                    }), 404
                
                log_to_file(f"🔍 Query status: {status_info}")
                
                return jsonify({
                    "success": True,
                    "chat_id": chat_id,
                    "status": status_info.get("status"),
                    "message": status_info.get("message"),
                    "current_step": status_info.get("current_step"),
                    "query": status_info.get("query"),
                    "answer": status_info.get("answer")
                })
            else:
                # Return indexing status (default)
                status_info = get_process_manager().get_session_status(chat_id, "indexing")
                if not status_info:
                    return jsonify({
                        "success": False, 
                        "error": "Session not found",
                        "status": "not_found"
                    }), 404
                
                log_to_file(f"🔍 Session status: {status_info}")

                return jsonify({
                    "success": True,
                    "chat_id": chat_id,
                    "status": status_info.get("status"),
                    "message": status_info.get("message"),
                    "current_step": status_info.get("current_step")
                })
            
        except Exception as e:
            log_to_file(f"❌ Session status error: {str(e)}")
            return jsonify({
                "success": False, 
                "error": f"Status check error: {str(e)}"
            }), 500

    @app.route('/api/sessions/<chat_id>/videos/indexed', methods=['GET'])
    def list_indexed_videos(chat_id):
        """Get list of indexed videos for specific session"""
        try:
            indexed_videos = get_process_manager().get_indexed_videos(chat_id)
            
            return jsonify({
                "success": True,
                "indexed_videos": indexed_videos,
                "total_count": len(indexed_videos),
                "chat_id": chat_id
            })
            
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"List error: {str(e)}"
            }), 500

    @app.route('/api/sessions/<chat_id>/terminate', methods=['POST'])
    def terminate_session_processes(chat_id):
        """终止特定session的进程"""
        try:
            terminated = get_process_manager().terminate_process(chat_id)
            
            return jsonify({
                "success": True,
                "message": f"Terminated processes for {chat_id}",
                "terminated_processes": terminated
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Termination failed: {str(e)}"
            }), 500

    @app.route('/api/sessions/<chat_id>/delete', methods=['DELETE'])
    def delete_session(chat_id):
        """删除session及其进程"""
        try:
            get_process_manager().delete_session(chat_id)
            return jsonify({
                "success": True,
                "message": f"Session {chat_id} deleted successfully",
                "chat_id": chat_id
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Delete failed: {str(e)}"
            }), 500

    @app.route('/api/sessions/<chat_id>/query', methods=['POST'])
    def query_video(chat_id):
        """Query video content for specific session - start async processing"""
        try:
            data = request.json
            log_to_file(f"🔍 Query data: {data}")
            if not data:
                return jsonify({
                    "success": False, 
                    "error": "No JSON data provided"
                }), 400
            
            query = data.get('query', '').strip()
            
            # Start async query processing
            log_to_file(f"🚀 Starting query processing for chat {chat_id}: {query}")
            success = get_process_manager().start_query_processing(chat_id, query)
            
            if not success:
                return jsonify({
                    "success": False,
                    "error": "Failed to start query processing"
                }), 500
            
            return jsonify({
                "success": True,
                "query": query,
                "message": "Query processing started",
                "chat_id": chat_id,
                "status": "started"
            })
            
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Query error: {str(e)}"
            }), 500

    @app.route('/api/system/status', methods=['GET'])
    def get_system_status():
        """Get overall system status"""
        try:
            pm = get_process_manager()
            im = get_imagebind_manager()
            
            # Calculate active sessions (extract unique chat_id from running processes)
            active_sessions = set()
            for key in pm.running_processes.keys():
                if key.endswith('_query'):
                    chat_id = key.rsplit('_query', 1)[0]
                else:
                    chat_id = key
                active_sessions.add(chat_id)
            
            total_sessions = len(active_sessions)
            
            # Calculate total indexed video count
            total_videos = 0
            if pm.global_config:
                for chat_id in active_sessions:
                    try:
                        videos = pm.get_indexed_videos(chat_id)
                        total_videos += len(videos)
                    except:
                        continue
            
            return jsonify({
                "success": True,
                "global_config_set": pm.global_config is not None,
                "imagebind_initialized": im.is_initialized,
                "imagebind_loaded": im.is_loaded,
                "total_sessions": total_sessions,
                "total_indexed_videos": total_videos,
                "running_processes": pm.get_process_status(),
                "sessions": list(active_sessions)
            })
            
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"System status error: {str(e)}"
            }), 500

    @app.route('/api/system/processes', methods=['GET'])
    def get_all_processes():
        """Get all running process status"""
        try:
            return jsonify({
                "success": True,
                "processes": get_process_manager().get_process_status()
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Process status error: {str(e)}"
            }), 500

    # New: ImageBind model management endpoint
    @app.route('/api/imagebind/load', methods=['POST'])
    def load_imagebind():
        """Load ImageBind model"""
        try:
            im = get_imagebind_manager()
            success = im.ensure_imagebind_loaded()
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "ImageBind model loaded successfully",
                    "status": im.get_status()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to load ImageBind model"
                }), 500
                
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Error loading ImageBind: {str(e)}"
            }), 500

    @app.route('/api/imagebind/release', methods=['POST'])
    def release_imagebind():
        """Release ImageBind model memory"""
        try:
            im = get_imagebind_manager()
            im.release_imagebind()
            
            return jsonify({
                "success": True,
                "message": "ImageBind model released successfully",
                "status": im.get_status()
            })
                
        except Exception as e:
            return jsonify({
                "success": False, 
                "error": f"Error releasing ImageBind: {str(e)}"
            }), 500

    @app.route('/api/imagebind/status', methods=['GET'])
    def imagebind_status():
        """Get ImageBind model status"""
        try:
            status = get_imagebind_manager().get_status()
            
            return jsonify({
                "success": True,
                "data": {
                    "loaded": status.get("loaded", False),
                    "model_type": status.get("model_type"),
                    "device": status.get("device"),
                    "memory_usage": status.get("memory_usage")
                }
            })
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error getting ImageBind status: {str(e)}"
            }), 500

    @app.route('/api/videos/available', methods=['GET'])
    def get_available_videos():
        """Get available videos from BASE_STORAGE_PATH directory tree"""
        try:
            # Get base storage path from global config
            pm = get_process_manager()
            base_storage_path = pm.global_config.get("base_storage_path", "/app/storage") if pm.global_config else "/app/storage"

            log_to_file(f"🔍 Scanning video files in: {base_storage_path}")

            if not os.path.exists(base_storage_path):
                return jsonify({
                    "success": False,
                    "error": f"Storage path not found: {base_storage_path}"
                }), 404

            def scan_directory_tree(dir_path, relative_path=""):
                """Recursively scan directory and build file tree"""
                items = []

                try:
                    entries = os.listdir(dir_path)

                    # Sort entries: directories first, then files (alphabetical)
                    entries.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))

                    for entry in entries:
                        if entry.startswith('.'):  # Skip hidden files
                            continue

                        entry_path = os.path.join(dir_path, entry)
                        full_relative_path = os.path.join(relative_path, entry) if relative_path else entry

                        try:
                            stat = os.stat(entry_path)
                            modified_time = stat.st_mtime

                            if os.path.isdir(entry_path):
                                # Directory - recurse to get children
                                children = scan_directory_tree(entry_path, full_relative_path)

                                # Only include directories that contain video files or other valid directories
                                if children:
                                    # Calculate totals for this directory
                                    total_files = sum(1 for child in children if child["type"] == "file")
                                    total_size = sum(child.get("size", 0) for child in children)

                                    items.append({
                                        "type": "directory",
                                        "name": entry,
                                        "path": entry_path,
                                        "relative_path": full_relative_path,
                                        "total_files": total_files,
                                        "total_size": total_size,
                                        "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size > 0 else 0,
                                        "modified": modified_time,
                                        "children": children,
                                        "expanded": False,  # Frontend will control expansion
                                        "selected": False   # Frontend will control selection
                                    })
                            else:
                                # File - check if it's a supported video format
                                if '.' in entry:
                                    ext = entry.rsplit('.', 1)[1].lower()
                                    if ext in ALLOWED_EXTENSIONS:
                                        items.append({
                                            "type": "file",
                                            "name": entry,
                                            "path": entry_path,
                                            "relative_path": full_relative_path,
                                            "size": stat.st_size,
                                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                                            "modified": modified_time,
                                            "format": ext,
                                            "selected": False
                                        })
                        except OSError as e:
                            log_to_file(f"⚠️ Skipping inaccessible item: {entry_path} - {str(e)}")
                            continue

                except PermissionError:
                    log_to_file(f"⚠️ Permission denied accessing directory: {dir_path}")
                    return []

                return items

            # Scan the directory tree
            structure = scan_directory_tree(base_storage_path)

            return jsonify({
                "success": True,
                "structure": {
                    "base_path": base_storage_path,
                    "items": structure,
                    "total_items": len(structure)
                }
            })

        except Exception as e:
            log_to_file(f"❌ Failed to get available videos: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Failed to scan video directory: {str(e)}"
            }), 500

def check_port_available(port):
    """Check if port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0
    except Exception:
        return False

def find_available_port(start_port, end_port):
    """Find an available port within specified range"""
    for port in range(start_port, end_port + 1):
        if check_port_available(port):
            return port
    return None

def get_system_free_port():
    """Get system-assigned free port (backup solution)"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# Global cleanup flag to avoid repeated cleanup
_cleanup_called = False

def cleanup_on_exit():
    """Cleanup function when program exits"""
    global _cleanup_called
    if _cleanup_called:
        return
    _cleanup_called = True
    
    try:
        log_to_file("🔔 VideoRAG API server is shutting down...")
        if process_manager:
            process_manager.cleanup()
        if global_imagebind_manager:
            global_imagebind_manager.cleanup()
        log_to_file("✅ Cleanup completed")
    except Exception as e:
        log_to_file(f"❌ Error during cleanup: {str(e)}")

def signal_handler(signum, frame):
    """Signal handler"""
    log_to_file(f"🔔 Received signal {signum}, initiating shutdown...")
    cleanup_on_exit()
    exit(0)

if __name__ == '__main__':
    # Must call freeze_support() at the beginning to support multiprocessing after packaging
    multiprocessing.freeze_support()
    
    # Register cleanup function and signal handler
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Windows special handling
    if os.name == 'nt':  # Windows
        try:
            import win32api
            def win32_handler(dwCtrlType):
                log_to_file(f"🔔 Windows signal received: {dwCtrlType}")
                cleanup_on_exit()
                return True
            win32api.SetConsoleCtrlHandler(win32_handler, True)
        except ImportError:
            log_to_file("⚠️ win32api not available, using basic signal handling")
            pass
    
    # Set process name only in main process
    try:
        import setproctitle
        setproctitle.setproctitle('videorag-api-server')
    except ImportError:
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = 'videorag-api-server'
    
    # Port configuration - centralized in main
    DEFAULT_PORT = 64451
    PORT_RANGE_START = 64451
    PORT_RANGE_END = 64470
    
    # Note: Do not initialize manager instance here directly, but use get_ function for delayed initialization
    
    try:
        SERVER_PORT = None

        if check_port_available(DEFAULT_PORT):
            SERVER_PORT = DEFAULT_PORT
        else:
            SERVER_PORT = find_available_port(PORT_RANGE_START, PORT_RANGE_END)
            if not SERVER_PORT:
                SERVER_PORT = get_system_free_port()

        # Set port as global variable for other functions
        globals()['SERVER_PORT'] = SERVER_PORT

        # Now it is safe to set multiprocessing start method
        multiprocessing.set_start_method('spawn')
        
        log_to_file(f"🚀 Starting VideoRAG API with global ImageBind on port {SERVER_PORT}")
        log_to_file(f"📝 Main process PID: {os.getpid()}")

        # Validate ASR configuration before starting
        log_to_file("🎤 验证ASR配置...")
        validate_asr_config()

        # Use factory function to create Flask app
        app = create_app()
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        log_to_file("🔔 Received keyboard interrupt")
        cleanup_on_exit()
    except Exception as e:
        log_to_file(f"❌ Failed to start server: {e}")
        cleanup_on_exit()
        exit(1)
    finally:
        cleanup_on_exit() 