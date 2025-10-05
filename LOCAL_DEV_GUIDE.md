# VideoRAG 本地开发手册

## 🎯 目标

提供高效的本地开发环境，替代重复的Docker构建，避免glibc兼容性问题，提高开发迭代速度。

## 📋 环境要求

- **操作系统**: Linux/macOS/Windows WSL2
- **Python**: 3.10.x (推荐使用pyenv管理)
- **Node.js**: 18.x+ (前端开发)
- **内存**: 至少8GB可用内存
- **存储**: 至少10GB可用空间

## 🚀 快速开始

### 第一步：环境准备

```bash
# 1. 创建开发目录
cd /data/项目/videoagent

# 2. 设置执行权限
chmod +x scripts/*.sh

# 3. 运行自动安装脚本（包含所有Dockerfile.dev功能）
./scripts/setup_local_dev.sh

# 4. 启动开发环境
./scripts/start_dev.sh
```

## 🛠️ 核心功能实现

### 1. 系统依赖安装

模拟Dockerfile.dev中的系统依赖安装：

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libglib2.0-0 \
    nodejs \
    npm \
    patchelf \
    binutils \
    gcc \
    g++
```

### 2. Python虚拟环境配置

```bash
# 创建Python环境
python3 -m venv videorag_dev

# 激活环境
source videorag_dev/bin/activate

# 安装依赖
pip install --upgrade pip
pip install --upgrade setuptools wheel
```

### 3. 分层依赖安装策略

#### 3.1 基础系统依赖
```bash
pip install numpy scipy requests flask flask-cors
pip install opencv-python Pillow pandas matplotlib
```

#### 3.2 机器学习核心依赖
```bash
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
pip install transformers pytorchvideo sentence-transformers
pip install timm einops networkx nano-vectordb
```

#### 3.3 复杂多媒体处理库
```bash
# 这些库最复杂，单独安装并测试
pip install faster_whisper ctranslate2
pip install moviepy

# 安装Git仓库依赖
pip install git+https://github.com/facebookresearch/ImageBind.git
```

## 🔬 glibc兼容性测试实现

### 核心测试功能

```python
# test_glibc_compatibility.py 核心功能
class GlibcCompatibilityTest:
    def setup(self):
        """查找并分析ctranslate2库文件"""
        self.ctranslate_lib = self._find_ctranslate_lib()
        return self.ctranslate_lib is not None

    def test_method_1_patchelf(self):
        """使用patchelf修改RPATH"""
        return self._apply_patchelf_fix()

    def test_method_2_ld_library_path(self):
        """使用LD_LIBRARY_PATH环境变量"""
        return self._apply_ld_library_path_fix()

    def integrate_with_videorag(self):
        """测试VideoRAG完整集成"""
        return self._test_videorag_import()
```

### 测试流程

```bash
# 运行完整兼容性测试
cd /data/项目/videoagent
source videorag_dev/bin/activate

# 执行glibc兼容性测试
python scripts/test_glibc_compatibility.py

# 查看详细测试报告
cat glibc_test_report.log
```

### 测试覆盖范围

#### 1. 库文件发现
- 自动查找ctranslate2安装位置
- 支持多种查找策略
- 获取库文件详细信息

#### 2. patchelf修复方法
- 修改ELF文件的RPATH
- 应用glibc兼容性修复
- 验证库加载正常性

#### 3. 环境变量方法
- 设置LD_LIBRARY_PATH
- 构建兼容库目录
- 测试环境变量生效性

#### 4. VideoRAG集成测试
- 测试VideoRAG模块导入
- 验证语音处理功能
- 检查完整工作流程

## 📁 项目结构

```
/data/项目/videoagent/
├── scripts/                    # 本地开发脚本
│   ├── setup_local_dev.sh      # 自动环境搭建
│   ├── install_dependencies.sh  # 分层依赖安装
│   ├── test_glibc_compatibility.py  # glibc测试
│   └── start_dev.sh            # 开发环境启动
├── videorag_dev/               # Python虚拟环境
├── VideoRAG-algorithm/         # 核心算法
├── backend/                    # Python API
└── web/                        # React前端
```

## 🔧 脚本详细说明

### setup_local_dev.sh

```bash
#!/bin/bash
# VideoRAG 本地开发环境自动搭建脚本

echo "🚀 开始VideoRAG本地开发环境搭建..."

# 检查系统环境
check_system_requirements() {
    echo "📋 检查系统要求..."
    # 检查Python版本
    # 检查可用内存
    # 检查可用存储空间
}

# 安装系统依赖
setup_system_dependencies() {
    echo "🔧 安装系统依赖..."
    # 模拟Dockerfile.dev的前几步
    sudo apt-get update
    sudo apt-get install build-essential ffmpeg nodejs npm patchelf
}

# 创建Python虚拟环境
setup_python_environment() {
    echo "🐍 创建Python虚拟环境..."
    python3 -m venv videorag_dev
    source videorag_dev/bin/activate
}

# 分层安装Python依赖
setup_python_dependencies() {
    echo "📦 安装Python依赖..."
    # 基础依赖
    ./scripts/install_dependencies.sh --phase base
    # 机器学习依赖
    ./scripts/install_dependencies.sh --phase ml
    # 复杂依赖
    ./scripts/install_dependencies.sh --phase complex
}

# 配置开发环境
setup_development_config() {
    echo "⚙️ 配置开发环境..."
    # 设置PYTHONPATH
    # 创建环境变量文件
    # 配置热重载
}

# 运行glibc兼容性测试
run_compatibility_tests() {
    echo "🧪 运行glibc兼容性测试..."
    python scripts/test_glibc_compatibility.py
    # 保存测试结果
}

main() {
    check_system_requirements
    setup_system_dependencies
    setup_python_environment
    setup_python_dependencies
    setup_development_config
    run_compatibility_tests

    echo "✅ 本地开发环境搭建完成！"
    echo "📖 请运行 ./scripts/start_dev.sh 启动开发环境"
}

main "$@"
```

### install_dependencies.sh

```bash
#!/bin/bash
# 分层依赖安装脚本

PHASE=$1

install_base_dependencies() {
    echo "📦 安装基础依赖..."
    pip install --upgrade pip setuptools wheel

    pip install \
        numpy \
        scipy \
        requests \
        flask \
        flask-cors \
        opencv-python \
        Pillow
}

install_ml_dependencies() {
    echo "🤖 安装机器学习依赖..."
    pip install torch torchvision torchaudio \
        --extra-index-url https://download.pytorch.org/whl/cpu

    pip install \
        transformers \
        pytorchvideo \
        sentence-transformers \
        timm \
        einops
}

install_complex_dependencies() {
    echo "🔬 安装复杂依赖..."
    # 分步安装以便错误追踪
    echo "安装faster_whisper..."
    pip install faster_whisper

    echo "安装ctranslate2..."
    pip install ctranslate2

    echo "安装ImageBind..."
    pip install git+https://github.com/facebookresearch/ImageBind.git
}

case $PHASE in
    base) install_base_dependencies ;;
    ml) install_ml_dependencies ;;
    complex) install_complex_dependencies ;;
    *) echo "用法: $0 {base|ml|complex}" ;;
esac
```

### start_dev.sh

```bash
#!/bin/bash
# VideoRAG开发环境启动脚本

echo "🚀 启动VideoRAG本地开发环境..."

# 设置环境变量
export PYTHONPATH=/data/项目/videoagent/VideoRAG-algorithm:/data/项目/videoagent/backend:$PYTHONPATH
export FLASK_ENV=development
export FLASK_DEBUG=1

# 激活虚拟环境
source videorag_dev/bin/activate

# 创建必要的目录
mkdir -p logs storage uploads

# 启动后端服务
echo "📡 启动Python后端API (端口: 64451)..."
python backend/videorag_web_api.py &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 检查后端是否启动成功
if ! curl -f -s http://localhost:64451/api/health > /dev/null; then
    echo "❌ 后端启动失败，正在重试..."
    kill $BACKEND_PID 2>/dev/null
    python backend/videorag_web_api.py &
    BACKEND_PID=$!
    sleep 10
fi

# 启动前端开发服务器
echo "🌐 启动React前端开发服务器 (端口: 3000)..."
cd web
npm run dev &
FRONTEND_PID=$!

# 等待前端启动
sleep 10

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
echo ""
echo "按 Ctrl+C 退出..."
wait
```

## 🧪 测试策略

### 1. 单元测试

```bash
# 运行VideoRAG核心功能测试
source videorag_dev/bin/activate
cd /data/项目/videoagent

# 测试VideoRAG导入
python -c "import videorag; print('✅ VideoRAG导入成功')"

# 测试Whisper功能
python -c "from faster_whisper import WhisperModel; print('✅ FasterWhisper可用')"

# 测试ImageBind功能
python -c "import imagebind; print('✅ ImageBind可用')"
```

### 2. 集成测试

```bash
# 测试完整API链
# 1. 健康检查
curl http://localhost:64451/api/health

# 2. 会话创建
SESSION_ID=$(curl -s -X POST http://localhost:64451/api/sessions \
    -H "Content-Type: application/json" \
    -d '{"session_name": "test_session"}' | jq -r '.session_id')

# 3. 模拟视频上传和查询
curl -X POST http://localhost:64451/api/sessions/$SESSION_ID/query \
    -H "Content-Type: application/json" \
    -d '{"message": "测试查询"}'
```

### 3. 性能基准测试

```bash
# 测试语音处理性能
python scripts/benchmark.py --test audio_processing

# 测试视频处理性能
python scripts/benchmark.py --test video_processing

# 生成性能报告
open performance_report.html
```

## 🐛 故障排除

### 常见问题

#### 1. pip安装失败
```bash
# 使用镜像加速
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package-name

# 清理缓存
pip cache purge
rm -rf ~/.cache/pip
```

#### 2. 依赖冲突
```bash
# 查看已安装包
pip list | grep torch

# 重新安装有冲突的包
pip install --force-reinstall torch=="2.3.0+cpu"
```

#### 3. glibc兼容性问题（本地）
```bash
# 如果出现glibc错误，运行详细测试
python scripts/test_glibc_compatibility.py --verbose

# 查看系统glibc版本
ldd --version

# 检查库文件
objdump -T /path/to/libctranslate2.so | grep GLIBC
```

#### 4. 端口冲突
```bash
# 检查端口占用
lsof -i :64451
lsof -i :3000

# 修改端口配置
export SERVER_PORT=64452
export WEB_DEV_PORT=3001
```

#### 5. 虚拟环境问题
```bash
# 重新创建虚拟环境
rm -rf videorag_dev
python3 -m venv videorag_dev
source videorag_dev/bin/activate
pip install --upgrade pip
./scripts/install_dependencies.sh --phase base
```

### 进阶调试

#### 查看详细日志
```bash
# Python后端日志
tail -f logs/videorag.log

# npm前端日志
cd web && npm run dev -- --debug

# 系统资源监控
htop
df -h
```

#### 环境变量调试
```bash
# 打印所有相关环境变量
env | grep -E "(PYTHON|FLASK|PATH)"

# 检查Python路径
python -c "import sys; print('\n'.join(sys.path))"
```

## 📊 效率对比

| 方面 | Docker开发 | 本地开发 | 提升倍数 |
|-----|----------|---------|---------|
| 初始搭建 | 15-20分钟 | 5-10分钟 | 2-3x |
| 代码修改重启 | 10-15分钟 | 3-10秒 | 60-300x |
| 调试体验 | 容器内限制 | 本地产开调试 | 10x+ |
| 资源消耗 | 高(每次重建) | 低(虚拟环境) | 5-10x |
| 兼容性测试 | 困难 | 直接本地运行 | 10x |

## 🎯 最佳实践

### 1. 开发习惯
- **频繁提交**: 本地开发后及时提交到git
- **环境隔离**: 每个功能分支使用独立虚拟环境
- **配置版本控制**: 将关键配置写入环境变量文件

### 2. 性能优化
- **虚拟环境缓存**: 保持videorag_dev目录避免重复安装
- **分层安装**: 先安装基础库，再安装复杂库
- **增量测试**: 只测试修改的功能模块

### 3. 团队协作
- **环境文档**: 更新本地开发环境要求
- **依赖锁定**: 使用requirements.txt确保一致性
- **CI/CD集成**: 提交前运行本地测试验证

### 4. 运维考虑
- **Docker比对**: 定期验证local和docker环境一致性
- **部署验证**: 使用相同的依赖版本进行部署测试
- **监控指标**: 建立本地环境的关键性能指标

## 📚 参考资料

- [VideoRAG项目简介](README.md)
- [Docker开发环境](docker-compose.dev.yml)
- [Python依赖管理](requirements.txt)
- [Flask API文档](backend/README.md)
- [React前端文档](web/README.md)

---

*本文档持续更新，建议在使用过程中记录和分享优化经验。*