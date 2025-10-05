#!/usr/bin/env python3
import subprocess
import time
import os
import signal
import sys
from pathlib import Path

def restart_service(service_name, command, cwd=None):
    """重启服务"""
    try:
        # 查找并终止现有进程
        result = subprocess.run(['pgrep', '-f', service_name],
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"已终止进程 {pid} ({service_name})")
                    time.sleep(1)
                except:
                    pass

        # 启动新服务
        print(f"启动 {service_name}...")
        if cwd:
            os.chdir(cwd)
        process = subprocess.Popen(command, shell=True)
        print(f"{service_name} 已启动 (PID: {process.pid})")
        return process

    except Exception as e:
        print(f"重启 {service_name} 失败: {e}")
        return None

if __name__ == "__main__":
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    frontend_dir = project_root / "web"

    # 重启后端
    restart_service("videorag_web_api", "python videorag_web_api.py", backend_dir)

    # 重启前端（如果正在运行）
    restart_service("npm run dev", "npm run dev", frontend_dir)

    print("服务重启完成")
