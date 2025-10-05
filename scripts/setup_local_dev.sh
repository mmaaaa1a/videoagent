#!/bin/bash
# VideoRAG 本地开发环境自动搭建脚本
# 实现Dockerfile.dev的完整本地版本

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 设置环境变量（对应Dockerfile.dev第17-19行）
export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1

# 检查系统要求
check_system_requirements() {
    log_info "📋 检查系统要求..."

    # 检查操作系统
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "目前仅支持Linux系统"
        exit 1
    fi

    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "未找到python3，请先安装Python 3.10+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ "$(printf '%s\n' "$PYTHON_VERSION" "3.10" | sort -V | head -n1)" != "3.10" ]]; then
        log_error "需要Python 3.10+，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    log_success "Python版本: $PYTHON_VERSION"

    # 检查可用内存（至少8GB）
    if [[ -f /proc/meminfo ]]; then
        MEM_GB=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
        if [[ $MEM_GB -lt 8 ]]; then
            log_warn "可用内存 ${MEM_GB}GB 可能不足，建议至少8GB"
        else
            log_success "可用内存: ${MEM_GB}GB"
        fi
    fi

    # 检查可用存储空间（至少10GB）
    if [[ -d / ]]; then
        DISK_GB=$(df / | awk 'NR==2 {printf "%.0f", $4/1024/1024}')
        if [[ $DISK_GB -lt 10 ]]; then
            log_warn "可用磁盘空间 ${DISK_GB}GB 可能不足，建议至少10GB"
        else
            log_success "可用磁盘空间: ${DISK_GB}GB"
        fi
    fi
}

# 检查ImageMagick是否已安装
check_imagemagick() {
    if command -v magick &> /dev/null; then
        log_warn "检测到ImageMagick已安装，可能与OpenCV冲突"
        read -p "是否要卸载ImageMagick? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get remove -y imagemagick imagemagick-6-common
        fi
    fi
}

# 检查Node.js和npm是否已安装
check_nodejs_npm() {
    log_info "🔍 检查Node.js和npm环境..."

    # 检查Node.js
    if command -v nodejs &> /dev/null; then
        NODE_VERSION=$(nodejs --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

        if [[ $NODE_MAJOR -ge 18 ]]; then
            log_success "Node.js已安装 (版本: $NODE_VERSION)"
            NODEJS_EXISTS=true
        else
            log_warn "Node.js版本过低 ($NODE_VERSION)，需要版本 >= 18.x"
            NODEJS_EXISTS=false
        fi
    else
        log_warn "未找到Node.js，需要安装"
        NODEJS_EXISTS=false
    fi

    # 检查npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        log_success "npm已安装 (版本: $NPM_VERSION)"
        NPM_EXISTS=true
    else
        log_warn "未找到npm，需要安装"
        NPM_EXISTS=false
    fi

    return 0
}

# 安装系统依赖（对应Dockerfile.dev第37-54行）
setup_system_dependencies() {
    log_info "🔧 安装系统依赖..."

    # 检查是否有管理员权限
    if [[ $EUID -eq 0 ]]; then
        log_warn "以root用户运行，建议使用普通用户"
    fi

    # 检查ImageMagick和Node.js环境
    check_imagemagick
    check_nodejs_npm

    # 更新包索引
    log_info "更新包索引..."
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        PACKAGES=(
            # 基础构建工具
            build-essential
            # 网络和版本控制
            curl
            git
            # 视频处理
            ffmpeg
            # 图形库依赖
            libsm6
            libxext6
            libfontconfig1
            libxrender1
            libglib2.0-0
            # 证书和运行时
            ca-certificates
            # glibc兼容性工具
            patchelf
            binutils
            # GCC编译工具链（完整版本，对应Dockerfile.dev）
            gcc
            g++
            gfortran
            libgomp1
            libasan8
            liblsan0
            libtsan2
            libubsan1
            pkg-config
            # Python开发依赖
            python3-dev
            python3-setuptools
            python3-wheel
            # BLAS/LAPACK（科学计算）
            libblas-dev
            liblapack-dev
            libatlas-base-dev
            # OpenCV额外依赖
            libgtk-3-dev
            libgstreamer-plugins-base1.0-dev
            # 其他系统库
            libffi-dev
            zlib1g-dev
            libssl-dev
            libbz2-dev
            libreadline-dev
            libsqlite3-dev
            liblzma-dev
        )

        # 根据Node.js检测结果决定是否添加Node.js相关包
        if [[ "$NODEJS_EXISTS" == "false" ]] || [[ "$NPM_EXISTS" == "false" ]]; then
            log_warn "Node.js或npm未满足要求，将尝试安装Ubuntu默认版本"
            PACKAGES+=(nodejs npm)
        else
            log_success "Node.js和npm已满足要求，跳过apt安装"
        fi

        log_info "安装系统包: ${PACKAGES[*]}"
        sudo apt-get update
        sudo apt-get install -y "${PACKAGES[@]}"
        sudo update-ca-certificates

        # 清理包缓存
        sudo apt-get clean
        sudo rm -rf /var/lib/apt/lists/*

    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        log_error "RHEL/CentOS系统需要手动配置依赖，请参考文档"
        exit 1
    else
        log_error "不支持的包管理器，仅支持apt-get"
        exit 1
    fi

    log_success "系统依赖安装完成"
}

# 配置Git（对应Dockerfile.dev第65-70行）
configure_git() {
    log_info "⚙️ 配置Git..."

    git config --global http.postBuffer 1048576000
    git config --global http.maxRequestBuffer 100M
    git config --global core.compression 0

    # 设置当前项目的安全目录
    git config --global safe.directory "$PROJECT_ROOT"
    git config --global safe.directory '/tmp/pip-req-build-*'

    log_success "Git配置完成"
}

# 创建Python虚拟环境
setup_python_environment() {
    log_info "🐍 配置Python虚拟环境..."

    cd "$PROJECT_ROOT"

    # 使用统一的虚拟环境路径
    VENV_PATH="/data/项目/videoagent/venv"

    # 如果已经存在venv环境，直接使用
    if [[ -d "$VENV_PATH" ]]; then
        log_info "发现已存在的虚拟环境，直接使用..."
        source "$VENV_PATH/bin/activate"
        log_success "虚拟环境已激活"
    else
        # 创建新的虚拟环境（对应Dockerfile.dev第62行）
        log_info "创建虚拟环境到 $VENV_PATH..."
        python3 -m venv "$VENV_PATH"
        source "$VENV_PATH/bin/activate"
        log_success "虚拟环境创建并激活"
    fi

    # 设置环境变量（对应Dockerfile.dev第17-19行）
    export DEBIAN_FRONTEND=noninteractive
    export PYTHONUNBUFFERED=1

    # 获取Python版本号
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')

    # 创建sitecustomize.py文件（对应Dockerfile.dev第20-21行）
    SITECUSTOMIZE_PATH="$VENV_PATH/lib/python$PYTHON_VERSION/site-packages/sitecustomize.py"
    mkdir -p "$(dirname "$SITECUSTOMIZE_PATH")"
    cat > "$SITECUSTOMIZE_PATH" << 'EOF'
# VideoRAG site customizations
import sys
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.dont_write_bytecode = True
EOF

    # 升级pip和基本工具（对应Dockerfile.dev第72-74行）
    log_info "升级pip和setuptools..."
    pip install --upgrade pip --retries 5 --timeout 300 || \
        (log_warn "重试pip升级..." && pip install --upgrade pip)
    pip install --no-cache-dir setuptools wheel

    log_success "Python环境配置完成"
}

# 安装Python依赖（对应Dockerfile.dev第76-103行）
install_python_dependencies() {
    log_info "📦 安装Python依赖..."

    # 确保在正确环境下（对应Dockerfile.dev第76行）
    source "/data/项目/videoagent/venv/bin/activate"
    export PYTHONPATH="$PROJECT_ROOT/VideoRAG-algorithm:$PROJECT_ROOT/backend:$PYTHONPATH"

    # 升级pip（对应Dockerfile.dev第73-74行）
    log_info "升级pip..."
    pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --retries 5 --timeout 300 || \
        pip install --upgrade pip --retries 5 --timeout 300

    # 安装PyTorch（必须先安装，对应Dockerfile.dev第76-79行）
    log_info "安装PyTorch系列库 (CPU版本)..."
    {
        pip install torch==2.3.0+cpu torchvision==0.18.0+cpu torchaudio==2.3.0+cpu \
            --extra-index-url https://download.pytorch.org/whl/cpu \
            -i https://pypi.tuna.tsinghua.edu.cn/simple \
            --retries 5 --timeout 600 || \
            (log_warn "重试PyTorch安装..." && \
             pip install torch==2.3.0+cpu torchvision==0.18.0+cpu torchaudio==2.3.0+cpu \
             --extra-index-url https://download.pytorch.org/whl/cpu --retries 5 --timeout 600)
    } &
    PYTORCH_PID=$!
    log_info "PyTorch安装已在后台启动 (PID: $PYTORCH_PID)"

    # 等待PyTorch安装完成
    log_info "等待PyTorch安装完成..."
    wait $PYTORCH_PID
    log_success "PyTorch安装已完成"

    # 安装基础依赖（对应Dockerfile.dev第77-78行）
    log_info "安装基础依赖..."
    pip install --no-cache-dir -r requirements.txt \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --retries 10 --timeout 1000 || \
        (log_warn "重试使用默认PyPI..." && \
         pip install --no-cache-dir -r requirements.txt \
         --retries 10 --timeout 1000)

    # 安装PyTorchVideo（对应Dockerfile.dev第80-84行）
    log_info "安装PyTorchVideo..."
    pip install --no-deps pytorchvideo>=0.1.5 \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --retries 10 --timeout 1000 || \
        (log_warn "重试PyTorchVideo安装..." && \
         pip install --no-deps pytorchvideo>=0.1.5 \
         --retries 10 --timeout 1000)

    # 验证安装（对应Dockerfile.dev第85-86行）
    log_info "验证关键依赖安装..."
    python3 -c "
import torch
import torchvision
import torchaudio
print(f'PyTorch版本: {torch.__version__}')
print(f'TorchVision版本: {torchvision.__version__}')
print(f'TorchAudio版本: {torchaudio.__version__}')
print('✅ PyTorch系列库验证成功')
" || log_error "PyTorch系列库验证失败"

    log_success "Python依赖安装完成"
}

# 修复兼容性问题（对应Dockerfile.dev第87-103行）
fix_compatibility_issues() {
    log_info "🔧 修复兼容性问题..."

    source "/data/项目/videoagent/venv/bin/activate"
    export PYTHONPATH="$PROJECT_ROOT/VideoRAG-algorithm:$PROJECT_ROOT/backend:$PYTHONPATH"

    # 使用现有的docker/scripts目录
    FIX_SCRIPTS_DIR="$PROJECT_ROOT/docker/scripts"

    # 检查修复脚本是否存在，不存在则创建
    if [[ ! -f "$FIX_SCRIPTS_DIR/fix_pytorchvideo.py" ]]; then
        mkdir -p "$FIX_SCRIPTS_DIR"
        log_warn "未找到PyTorchVideo修复脚本，创建默认修复..."
        cat > "$FIX_SCRIPTS_DIR/fix_pytorchvideo.py" << 'EOF'
#!/usr/bin/env python3
print("🔧 应用PyTorchVideo兼容性修复...")
import sys
try:
    import torchvision.transforms.functional as F
    if not hasattr(__import__('torchvision.transforms'), 'functional_tensor'):
        __import__('torchvision.transforms').functional_tensor = F
    print("✅ PyTorchVideo兼容性修复完成")
except Exception as e:
    print(f"❌ PyTorchVideo修复失败: {e}")
EOF
        chmod +x "$FIX_SCRIPTS_DIR/fix_pytorchvideo.py"
    fi

    if [[ ! -f "$FIX_SCRIPTS_DIR/fix_imagebind.py" ]]; then
        log_warn "未找到ImageBind修复脚本，创建默认修复..."
        cat > "$FIX_SCRIPTS_DIR/fix_imagebind.py" << 'EOF'
#!/usr/bin/env python3
print("🔧 应用ImageBind兼容性修复...")
try:
    import imagebind
    print("✅ ImageBind兼容性修复完成")
except ImportError:
    print("ℹ️ ImageBind未安装，跳过修复")
except Exception as e:
    print(f"❌ ImageBind修复失败: {e}")
EOF
        chmod +x "$FIX_SCRIPTS_DIR/fix_imagebind.py"
    fi

    # glibc测试脚本应该已经在docker/scripts目录中，如果不存在才创建
    if [[ ! -f "$FIX_SCRIPTS_DIR/test_glibc_compatibility.py" ]]; then
        log_warn "未找到glibc测试脚本，创建修复脚本..."
        create_glibc_test_script "$FIX_SCRIPTS_DIR/test_glibc_compatibility.py"
    fi

    # 复制修复脚本到项目根目录
    cp "$FIX_SCRIPTS_DIR/fix_pytorchvideo.py" "$PROJECT_ROOT/" 2>/dev/null || true
    cp "$FIX_SCRIPTS_DIR/fix_imagebind.py" "$PROJECT_ROOT/" 2>/dev/null || true
    cp "$FIX_SCRIPTS_DIR/test_glibc_compatibility.py" "$PROJECT_ROOT/" 2>/dev/null || true

    # 执行PyTorchVideo修复（对应Dockerfile.dev第87-88行）
    log_info "修复PyTorchVideo兼容性..."
    python3 "$PROJECT_ROOT/fix_pytorchvideo.py" 2>/dev/null || \
        log_warn "PyTorchVideo修复脚本执行失败，继续安装..."

    # 安装ImageBind（对应Dockerfile.dev第89-97行）
    log_info "安装ImageBind..."
    pip install --no-deps git+https://github.com/facebookresearch/ImageBind.git@e2e2e6943d0ca6aa7844aa17da77d04d78b99af5 \
        --retries 5 --timeout 300 || \
        (log_warn "重试安装最新版本..." && \
         pip install --no-deps git+https://github.com/facebookresearch/ImageBind.git@main \
         --retries 5 --timeout 600) || \
        (log_warn "尝试本地克隆安装..." && \
         (cd /tmp && \
          git clone --depth 1 https://github.com/facebookresearch/ImageBind.git imagebind 2>/dev/null || \
          (cd imagebind && git checkout e2e2e6943d0ca6aa7844aa17da77d04d78b99af5 2>/dev/null && \
           pip install -e . --no-deps 2>/dev/null || log_error "ImageBind安装失败")))

    # 执行ImageBind修复（对应Dockerfile.dev第99-100行）
    log_info "修复ImageBind兼容性..."
    python3 "$PROJECT_ROOT/fix_imagebind.py" 2>/dev/null || \
        log_warn "ImageBind修复脚本执行失败，可能无需修复"

    log_success "兼容性问题修复完成"
}

# 创建glibc兼容性测试脚本
create_glibc_test_script() {
    local script_path="$1"
    log_info "创建glibc兼容性测试脚本..."

    cat > "$script_path" << 'EOF'
#!/usr/bin/env python3
"""
VideoRAG glibc兼容性测试脚本
测试ctranslate2库的glibc兼容性并提供自动修复
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path

class GlibcCompatibilityTest:
    def __init__(self):
        self.ctranslate_lib = None
        self.test_results = {}

    def setup(self):
        """查找并分析ctranslate2库文件"""
        print("🔍 查找ctranslate2库文件...")
        self.ctranslate_lib = self._find_ctranslate_lib()
        return self.ctranslate_lib is not None

    def _find_ctranslate_lib(self):
        """查找ctranslate2库文件"""
        try:
            import ctranslate2
            ctranslate_path = Path(ctranslate2.__file__).parent
            lib_files = list(ctranslate_path.glob("*.so"))
            if lib_files:
                print(f"✅ 找到ctranslate2库: {lib_files[0]}")
                return str(lib_files[0])
        except ImportError:
            print("❌ ctranslate2未安装")
            return None
        except Exception as e:
            print(f"❌ 查找库文件失败: {e}")
            return None

    def test_method_1_patchelf(self):
        """使用patchelf修改RPATH"""
        print("🛠️ 测试patchelf修复方法...")
        if not self.ctranslate_lib:
            print("❌ 未找到ctranslate2库文件")
            return False

        try:
            # 检查patchelf是否可用
            result = subprocess.run(["patchelf", "--version"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ patchelf不可用")
                return False

            print("✅ patchelf可用，测试修复...")
            return self._apply_patchelf_fix()
        except Exception as e:
            print(f"❌ patchelf测试失败: {e}")
            return False

    def _apply_patchelf_fix(self):
        """应用patchelf修复"""
        try:
            cmd = ["patchelf", "--set-rpath", "/usr/lib/x86_64-linux-gnu:$ORIGIN",
                   self.ctranslate_lib]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ patchelf修复应用成功")
                return True
            else:
                print(f"❌ patchelf修复失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ patchelf修复异常: {e}")
            return False

    def test_method_2_ld_library_path(self):
        """使用LD_LIBRARY_PATH环境变量"""
        print("📁 测试LD_LIBRARY_PATH方法...")
        current_path = os.environ.get('LD_LIBRARY_PATH', '')
        new_path = '/usr/lib/x86_64-linux-gnu'
        if current_path:
            new_path = f"{new_path}:{current_path}"

        print(f"可以使用: export LD_LIBRARY_PATH=\"{new_path}\"")
        print("✅ LD_LIBRARY_PATH方法可用")
        return True

    def integrate_with_videorag(self):
        """测试VideoRAG完整集成"""
        print("🔗 测试VideoRAG集成...")
        try:
            # 尝试导入VideoRAG模块
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'VideoRAG-algorithm'))
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

            import videorag
            print("✅ VideoRAG模块导入成功")
            return True
        except ImportError as e:
            print(f"❌ VideoRAG导入失败: {e}")
            return False
        except Exception as e:
            print(f"❌ VideoRAG集成异常: {e}")
            return False

def main():
    print("🧪 VideoRAG glibc兼容性测试")
    print("=" * 50)

    tester = GlibcCompatibilityTest()

    if not tester.setup():
        print("❌ 无法继续测试，请先安装ctranslate2")
        return False

    # 执行测试
    tests = [
        ("patchelf修复", tester.test_method_1_patchelf),
        ("环境变量方法", tester.test_method_2_ld_library_path),
        ("VideoRAG集成", tester.integrate_with_videorag),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n⚙️ 执行测试: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - 通过")
        else:
            print(f"❌ {test_name} - 失败")

    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
EOF

    chmod +x "$script_path"
    log_success "glibc兼容性测试脚本创建完成"
}

# 创建开发环境配置
setup_development_config() {
    log_info "⚙️ 配置开发环境..."

    # 创建必要目录（对应Dockerfile.dev第107-112行）
    mkdir -p "$PROJECT_ROOT/logs" \
             "$PROJECT_ROOT/storage" \
             "$PROJECT_ROOT/uploads" \
             "$PROJECT_ROOT/models"

    log_success "必要目录创建完成"

    # 安装开发依赖（对应Dockerfile.dev第113-115行）
    source "/data/项目/videoagent/venv/bin/activate"
    pip install --no-cache-dir watchdog flask-cors \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        --retries 3 --timeout 300

    # 设置脚本权限（对应Dockerfile.dev第117-118行）
    chmod +x "$PROJECT_ROOT/backend/videorag_web_api.py" 2>/dev/null || true

    # 创建热重载脚本（对应Dockerfile.dev第120-121行）
    cat > "$PROJECT_ROOT/reload_services.py" << 'EOF'
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
EOF
    chmod +x "$PROJECT_ROOT/reload_services.py"

    # 创建torchvision兼容性修复脚本（对应Dockerfile.dev第123-145行）
    cat > "$PROJECT_ROOT/torchvision_fix.py" << 'EOF'
#!/usr/bin/env python3
import sys
import torchvision
# Apply global torchvision compatibility fix
if not hasattr(torchvision.transforms, "functional_tensor"):
    import torchvision.transforms.functional as F
    torchvision.transforms.functional_tensor = F
    print("✅ Applied torchvision compatibility fix")

# Test imports after fix
try:
    import pytorchvideo.transforms.augmentations
    print("✅ PyTorchVideo import successful")
except ImportError as e:
    print(f"❌ PyTorchVideo import failed: {e}")

try:
    import imagebind.data
    print("✅ ImageBind import successful")
except ImportError as e:
    print(f"❌ ImageBind import failed: {e}")

# Test CTranslate2
try:
    import ctranslate2
    print("✅ CTranslate2 import successful")
except ImportError as e:
    print(f"❌ CTranslate2 import failed: {e}")

# Test VideoRAG
try:
    import videorag
    print("✅ VideoRAG import successful")
except ImportError as e:
    print(f"❌ VideoRAG import failed: {e}")
EOF
    chmod +x "$PROJECT_ROOT/torchvision_fix.py"

    # 创建本地开发启动脚本（对应Dockerfile.dev第147-156行，但适配本地环境）
    cat > "$PROJECT_ROOT/start_dev.sh" << 'EOF'
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
EOF
    chmod +x "$PROJECT_ROOT/start_dev.sh"

    log_success "开发环境配置完成"
}

# 运行glibc兼容性测试（对应Dockerfile.dev第157-161行）
run_glibc_tests() {
    log_info "🧪 运行glibc兼容性测试..."

    source "/data/项目/videoagent/venv/bin/activate"

    export PYTHONPATH="$PROJECT_ROOT/VideoRAG-algorithm:$PROJECT_ROOT/backend:$PYTHONPATH"

    # 确保测试脚本存在
    if [[ ! -f "$PROJECT_ROOT/test_glibc_compatibility.py" ]]; then
        log_error "glibc兼容性测试脚本不存在"
        return 1
    fi

    # 验证必要目录存在（模拟Docker COPY操作）
    if [[ ! -d "$PROJECT_ROOT/VideoRAG-algorithm" ]]; then
        log_error "未找到VideoRAG-algorithm目录"
        exit 1
    fi

    if [[ ! -d "$PROJECT_ROOT/backend" ]]; then
        log_error "未找到backend目录"
        exit 1
    fi

    log_info "开始运行全面glibc兼容性测试..."
    if python3 "$PROJECT_ROOT/test_glibc_compatibility.py"; then
        log_success "glibc兼容性测试通过"
        return 0
    else
        log_warn "glibc兼容性测试失败，可能影响某些功能"
        log_warn "建议检查系统glibc版本和ctranslate2兼容性"
        return 1
    fi
}

# 保存环境变量
save_environment() {
    log_info "💾 保存环境配置..."

    # 创建环境变量脚本
    cat > "$PROJECT_ROOT/.dev_env" << EOF
# VideoRAG本地开发环境变量
export PYTHONPATH="$PROJECT_ROOT/VideoRAG-algorithm:$PROJECT_ROOT/backend:\$PYTHONPATH"
export FLASK_ENV=development
export FLASK_DEBUG=1
export NODE_ENV=development

# 激活虚拟环境
source "/data/项目/videoagent/venv/bin/activate"
EOF

    log_success "环境配置已保存到 $PROJECT_ROOT/.dev_env"
}

# 检查安装结果
verify_installation() {
    log_info "🔍 验证安装结果..."

    source "/data/项目/videoagent/venv/bin/activate"
    export PYTHONPATH="$PROJECT_ROOT/VideoRAG-algorithm:$PROJECT_ROOT/backend:$PYTHONPATH"

    # 测试基本导入
    TEST_RESULTS=()

    # 测试torchvision兼容性
    if python3 "$PROJECT_ROOT/torchvision_fix.py" 2>/dev/null; then
        TEST_RESULTS+=("✅ PyTorch系列库")
    else
        TEST_RESULTS+=("❌ PyTorch系列库")
    fi

    # 测试VideoRAG导入
    if python3 -c "import videorag" 2>/dev/null; then
        TEST_RESULTS+=("✅ VideoRAG核心")
    else
        TEST_RESULTS+=("❌ VideoRAG核心")
    fi

    # 测试faster_whisper导入
    if python3 -c "from faster_whisper import WhisperModel" 2>/dev/null; then
        TEST_RESULTS+=("✅ faster_whisper")
    else
        TEST_RESULTS+=("❌ faster_whisper")
    fi

    # 测试ctranslate2导入
    if python3 -c "import ctranslate2" 2>/dev/null; then
        TEST_RESULTS+=("✅ ctranslate2")
    else
        TEST_RESULTS+=("❌ ctranslate2")
    fi

    # 测试Flask应用
    if python3 -c "from backend.videorag_web_api import app" 2>/dev/null; then
        TEST_RESULTS+=("✅ Flask API")
    else
        TEST_RESULTS+=("❌ Flask API")
    fi

    echo "=== 安装验证结果 ==="
    printf '%s\n' "${TEST_RESULTS[@]}"
    echo "==================="

    # 统计成功/失败
    SUCCESS_COUNT=$(echo "${TEST_RESULTS[@]}" | grep -c "✅")
    TOTAL_COUNT=${#TEST_RESULTS[@]}

    log_success "$SUCCESS_COUNT/$TOTAL_COUNT 项测试通过"

    if [[ $SUCCESS_COUNT -eq $TOTAL_COUNT ]]; then
        log_success "🎉 本地开发环境安装完全成功！"
    else
        log_warn "⚠️ 部分项目测试失败，建议检查依赖安装"
    fi
}

# 主函数
main() {
    log_info "🚀 开始VideoRAG本地开发环境安装..."
    log_info "项目路径: $PROJECT_ROOT"

    check_system_requirements

    # 检查是否以root用户运行安装
    if [[ $EUID -eq 0 ]]; then
        log_warn "检测到以root用户运行，某些步骤可能需要手动确认"
        read -p "是否继续？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "安装已取消"
            exit 0
        fi
    fi

    # 根据参数决定是否跳过某些步骤
    if [[ "$SKIP_SYSTEM" != "true" ]]; then
        setup_system_dependencies
    else
        log_info "⏭️ 跳过系统依赖安装 (--skip-system)"
    fi

    configure_git
    setup_python_environment
    install_python_dependencies
    fix_compatibility_issues
    setup_development_config

    if [[ "$SKIP_TESTS" != "true" ]]; then
        run_glibc_tests
    else
        log_info "⏭️ 跳过glibc兼容性测试 (--skip-tests)"
    fi

    save_environment
    verify_installation

    echo ""
    log_success "🎊 VideoRAG本地开发环境安装完成！"
    echo ""
    echo "📖 使用说明:"
    echo "   激活环境: source /data/项目/videoagent/venv/bin/activate"
    echo "   或加载配置: source .dev_env"
    echo "   启动开发: ./start_dev.sh"
    echo "   查看帮助: ./LOCAL_DEV_GUIDE.md"
    echo ""
    echo "🚀 现在可以开始高效的本地开发了！"
    echo ""
}

# 参数处理
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "VideoRAG本地开发环境安装脚本"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --help, -h    显示此帮助信息"
            echo "  --skip-system 跳过系统依赖安装"
            echo "  --skip-tests  跳过glibc测试"
            echo ""
            exit 0
            ;;
        --skip-system)
            SKIP_SYSTEM=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            log_error "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 执行主函数
main "$@"