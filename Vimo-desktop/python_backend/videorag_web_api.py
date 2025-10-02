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
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import logging
import warnings

warnings.filterwarnings("ignore")
logging.getLogger("httpx").setLevel(logging.WARNING)

from videorag._llm import LLMConfig, openai_embedding, gpt_complete, dashscope_caption_complete
from videorag import VideoRAG, QueryParam

# Import existing VideoRAG API functionality
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from videorag_api import (
    log_to_file, write_status_json, read_status_json, get_session_status_file,
    update_session_status, GlobalImageBindManager, HTTPImageBindClient,
    VideoRAGProcessManager, get_imagebind_manager, get_process_manager,
    index_video_worker_process, query_worker_process,
    check_port_available, find_available_port, get_system_free_port,
    cleanup_on_exit, signal_handler
)

# Configure file uploads
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Web-specific API routes
def register_web_routes(app):
    """Register web-specific routes to Flask application"""

    @app.route('/', methods=['GET'])
    def serve_index():
        """Serve the main web application"""
        try:
            return send_from_directory('/app/static', 'index.html')
        except Exception as e:
            log_to_file(f"Error serving index.html: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Web application not available"
            }), 404

    @app.route('/<path:path>', methods=['GET'])
    def serve_static(path):
        """Serve static files"""
        try:
            return send_from_directory('/app/static', path)
        except Exception as e:
            log_to_file(f"Error serving static file {path}: {str(e)}")
            return jsonify({
                "success": False,
                "error": "Static file not found"
            }), 404

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """Handle file upload for web interface"""
        try:
            if 'file' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No file provided"
                }), 400

            file = request.files['file']
            chat_id = request.form.get('chat_id')

            if not chat_id:
                return jsonify({
                    "success": False,
                    "error": "chat_id is required"
                }), 400

            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "No file selected"
                }), 400

            if not allowed_file(file.filename):
                return jsonify({
                    "success": False,
                    "error": f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
                }), 400

            # Create upload directory for this chat session
            upload_dir = os.path.join('/app/uploads', chat_id)
            os.makedirs(upload_dir, exist_ok=True)

            # Save file
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            saved_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(upload_dir, saved_filename)

            file.save(file_path)

            # Get video duration
            try:
                with VideoFileClip(file_path) as clip:
                    duration = clip.duration
                    fps = clip.fps
                    size = clip.size
            except Exception as e:
                log_to_file(f"Error getting video duration: {str(e)}")
                duration = 0
                fps = 0
                size = [0, 0]

            log_to_file(f"✅ File uploaded successfully: {saved_filename} ({duration}s)")

            return jsonify({
                "success": True,
                "message": "File uploaded successfully",
                "filename": saved_filename,
                "original_name": filename,
                "file_path": file_path,
                "duration": duration,
                "fps": fps,
                "width": size[0],
                "height": size[1],
                "chat_id": chat_id
            })

        except Exception as e:
            log_to_file(f"❌ File upload error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Upload error: {str(e)}"
            }), 500

    @app.route('/api/uploads/<chat_id>/<filename>', methods=['GET'])
    def serve_uploaded_file(chat_id, filename):
        """Serve uploaded files"""
        try:
            file_path = os.path.join('/app/uploads', chat_id, filename)
            if os.path.exists(file_path):
                return send_from_directory(os.path.join('/app/uploads', chat_id), filename)
            else:
                return jsonify({
                    "success": False,
                    "error": "File not found"
                }), 404
        except Exception as e:
            log_to_file(f"❌ Error serving uploaded file: {str(e)}")
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404

    @app.route('/api/sessions/<chat_id>/videos/upload-web', methods=['POST'])
    def upload_video_web(chat_id):
        """Upload video for web interface and start indexing"""
        try:
            data = request.json
            uploaded_files = data.get('uploaded_files', [])

            if not uploaded_files:
                return jsonify({
                    "success": False,
                    "error": "uploaded_files is required"
                }), 400

            # Verify files exist
            video_path_list = []
            for file_info in uploaded_files:
                file_path = file_info.get('file_path')
                if not file_path or not os.path.exists(file_path):
                    return jsonify({
                        "success": False,
                        "error": f"File not found: {file_path}"
                    }), 400
                video_path_list.append(file_path)

            log_to_file(f"📹 Starting video processing from web upload: {len(video_path_list)} files")

            # Get video names
            video_names = [os.path.basename(path) for path in video_path_list]

            # Start background indexing process
            get_process_manager().start_video_indexing(chat_id, video_path_list)

            return jsonify({
                "success": True,
                "message": "Video processing started from web upload",
                "video_names": video_names,
                "video_count": len(video_path_list),
                "chat_id": chat_id,
                "status": "started"
            })

        except Exception as e:
            error_msg = f"Failed to start video processing from web upload: {str(e)}"
            log_to_file(f"❌ {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg
            }), 500

    @app.route('/api/system/web-status', methods=['GET'])
    def get_web_system_status():
        """Get web-specific system status"""
        try:
            pm = get_process_manager()
            im = get_imagebind_manager()

            # Calculate active sessions
            active_sessions = set()
            for key in pm.running_processes.keys():
                if key.endswith('_query'):
                    chat_id = key.rsplit('_query', 1)[0]
                else:
                    chat_id = key
                active_sessions.add(chat_id)

            total_sessions = len(active_sessions)

            # Calculate storage info
            storage_info = {}
            try:
                upload_dir = '/app/uploads'
                if os.path.exists(upload_dir):
                    storage_info['upload_size'] = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(upload_dir)
                        for filename in filenames
                    )

                storage_dir = '/app/storage'
                if os.path.exists(storage_dir):
                    storage_info['storage_size'] = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(storage_dir)
                        for filename in filenames
                    )
            except Exception as e:
                log_to_file(f"Error calculating storage info: {str(e)}")

            return jsonify({
                "success": True,
                "global_config_set": pm.global_config is not None,
                "imagebind_initialized": im.is_initialized,
                "imagebind_loaded": im.is_loaded,
                "total_sessions": total_sessions,
                "total_indexed_videos": pm.global_config and len([
                    video for session_id in active_sessions
                    for video in pm.get_indexed_videos(session_id)
                ]) or 0,
                "running_processes": pm.get_process_status(),
                "sessions": list(active_sessions),
                "storage_info": storage_info,
                "web_interface": True
            })

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Web system status error: {str(e)}"
            }), 500

def create_web_app():
    """Create Flask web application instance"""
    app = Flask(__name__, static_folder='/app/static')

    # Configure Flask for file uploads
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    app.config['UPLOAD_FOLDER'] = '/app/uploads'

    CORS(app)

    # Register all existing routes from videorag_api.py
    from videorag_api import register_routes
    register_routes(app)

    # Register web-specific routes
    register_web_routes(app)

    return app

if __name__ == '__main__':
    # Must call freeze_support() at the beginning to support multiprocessing after packaging
    multiprocessing.freeze_support()

    # Register cleanup function and signal handler
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    # Set process name only in main process
    try:
        import setproctitle
        setproctitle.setproctitle('videorag-web-api-server')
    except ImportError:
        import sys
        if hasattr(sys, 'argv'):
            sys.argv[0] = 'videorag-web-api-server'

    # Port configuration
    DEFAULT_PORT = 64451
    PORT_RANGE_START = 64451
    PORT_RANGE_END = 64470

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

        # Set multiprocessing start method
        multiprocessing.set_start_method('spawn')

        log_to_file(f"🚀 Starting VideoRAG Web API on port {SERVER_PORT}")
        log_to_file(f"📝 Main process PID: {os.getpid()}")

        # Create web application
        app = create_web_app()

        # Start both API and web interface
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, threaded=True)

    except KeyboardInterrupt:
        log_to_file("🔔 Received keyboard interrupt")
        cleanup_on_exit()
    except Exception as e:
        log_to_file(f"❌ Failed to start web server: {e}")
        cleanup_on_exit()
        exit(1)
    finally:
        cleanup_on_exit()