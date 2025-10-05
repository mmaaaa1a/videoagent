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

# 创建必要的目录
mkdir -p logs storage uploads models

# 应用torchvision兼容性修复
echo "🔧 应用兼容性修复..."
python3 "$(cd "$(dirname "$0")" && pwd)/torchvision_fix.py"

# 启动后端服务
echo "📡 启动Python后端API (端口: 64451)..."
python "$(cd "$(dirname "$0")" && pwd)/backend/videorag_web_api.py" &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 检查后端是否启动成功
if ! curl -f -s http://localhost:64451/api/health > /dev/null; then
    echo "❌ 后端启动失败，正在重试..."
    kill $BACKEND_PID 2>/dev/null
    sleep 5
    python "$(cd "$(dirname "$0")" && pwd)/backend/videorag_web_api.py" &
    BACKEND_PID=$!
    sleep 5
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
echo "   - 查看后端日志: tail -f logs/videorag.log"
echo "   - 停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "   - 重启服务: python3 reload_services.py"
echo ""
echo "按 Ctrl+C 退出..."
wait
