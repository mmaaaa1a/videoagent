#!/bin/bash
# VideoRAG本地开发环境启动脚本

echo "🚀 启动VideoRAG本地开发环境..."

# 设置环境变量
export PYTHONPATH="$(cd "$(dirname "$0")" && pwd)/VideoRAG-algorithm:$(cd "$(dirname "$0")" && pwd)/backend:$PYTHONPATH"
export FLASK_ENV=development
export FLASK_DEBUG=1
export NODE_ENV=development

# 激活虚拟环境
source "/data/项目/videoagent/venv/bin/activate"

# 应用torchvision兼容性修复
echo "🔧 应用兼容性修复..."
python3 "$(cd "$(dirname "$0")" && pwd)/torchvision_fix.py"

# 日志监控函数
start_log_monitor() {
    local log_file="$(cd "$(dirname "$0")" && pwd)/backend/log.txt"
    echo "📝 开始监控后端日志: $log_file"

    # 等待日志文件存在
    while [ ! -f "$log_file" ]; do
        sleep 1
    done

    # 实时显示日志
    tail -f "$log_file" &
    LOG_PID=$!
    echo "📝 日志监控已启动 (PID: $LOG_PID)"
}

# 启动后端服务（避免重复启动）
echo "📡 启动Python后端API (端口: 64451)..."

# 检查端口是否已被占用
if ! curl -f -s http://localhost:64451/api/health > /dev/null 2>&1; then
    echo "🔍 端口64451空闲，启动后端服务..."
    python "$(cd "$(dirname "$0")" && pwd)/backend/videorag_web_api.py" &
    BACKEND_PID=$!

    # 启动日志监控
    start_log_monitor

    # 等待后端启动，增加等待时间并分阶段检查
    echo "⏳ 等待后端服务启动..."
    for i in {1..12}; do  # 最多等待60秒（12*5秒）
        sleep 5
        if curl -f -s http://localhost:64451/api/health > /dev/null 2>&1; then
            echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
            break
        else
            echo "⏳ 等待后端启动... ($i/12)"
            # 检查进程是否还在运行
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo "❌ 后端进程异常退出，重新启动..."
                python "$(cd "$(dirname "$0")" && pwd)/backend/videorag_web_api.py" &
                BACKEND_PID=$!
                start_log_monitor
            fi
        fi

        # 如果最后一次尝试失败，报错但不阻止前端启动
        if [ $i -eq 12 ]; then
            echo "⚠️ 后端服务启动超时，但继续启动前端（请手动检查后端状态）"
        fi
    done
else
    echo "✅ 后端服务已在运行，跳过启动"
    # 启动日志监控以查看现有服务的日志
    start_log_monitor
fi

# 启动前端开发服务器
echo "🌐 启动React前端开发服务器 (端口: 3000)..."
cd "$(cd "$(dirname "$0")" && pwd)/web" && npm run dev &
FRONTEND_PID=$!

# 检查服务状态
check_services() {
    echo "🔍 检查服务状态..."

    if curl -f -s http://localhost:64451/api/health > /dev/null; then
        echo "✅ 后端API服务: http://localhost:64451"
    else
        echo "❌ 后端API服务未就绪"
    fi

    if curl -f -s http://localhost:3000 > /dev/null; then
        echo "✅ 前端开发服务: http://localhost:3000"
    else
        echo "❌ 前端开发服务未就绪"
    fi
}

# 等待前端启动
sleep 10
check_services

echo ""
echo "🎉 VideoRAG开发环境启动完成!"
echo "📖 前端地址: http://localhost:3000 (React + Vite)"
echo "🔗 后端地址: http://localhost:64451 (Flask API)"
echo ""
echo "💡 开发提示:"
echo "   - 修改Python代码后直接重启，无需重新构建"
echo "   - 前端支持热重载，修改立即生效"
echo "   - 查看后端日志: tail -f backend/log.txt"
echo "   - 停止服务: kill $BACKEND_PID $FRONTEND_PID $LOG_PID"
echo "   - 重启服务: python3 reload_services.py"
echo ""
echo "按 Ctrl+C 退出..."

# 退出时清理所有进程
cleanup() {
    echo ""
    echo "🛑 正在停止所有服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    kill $LOG_PID 2>/dev/null
    echo "✅ 所有服务已停止"
    exit 0
}

trap cleanup INT TERM
wait
