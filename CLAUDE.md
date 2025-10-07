# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

VideoRAG是一个基于Web的视频对话应用，允许用户通过AI技术与视频进行对话。该项目采用三层架构：VideoRAG算法核心 + React前端 + Python后端，能够理解并分析任意长度的视频内容。

## 快速命令参考

### 开发环境启动
```bash
# Docker开发模式（推荐，支持热重载）
docker compose -f docker-compose.dev.yml up -d --build

# 本地开发模式（更快的开发迭代）
./start_dev.sh           # 自动启动前后端
# 或手动启动：
# 终端1: cd web && npm run dev          # 前端开发服务器
# 终端2: python backend/videorag_web_api.py  # 后端API

# 生产模式
docker compose -f docker-compose.prod.yml up -d --build
```

### 前端开发命令
```bash
cd web
npm run dev        # 启动开发服务器 (http://localhost:3000)
npm run build      # 构建生产版本
npm run preview    # 预览生产构建
npm run lint       # 代码检查
npm run format     # 代码格式化
```

### 后端调试
```bash
# 必须使用项目虚拟环境
source /data/项目/videoagent/venv/bin/activate

# 语法检查
python -m py_compile backend/videorag_web_api.py

# 模块导入测试
python -c "import videorag; print('模块导入成功')"

# torchvision兼容性修复
python torchvision_fix.py

# 服务重启
python reload_services.py

# 测试VideoRAG核心功能
python -c "
from videorag import VideoRAG
print('VideoRAG导入成功')
"
```

### 容器管理
```bash
docker compose ps                                # 查看容器状态
docker compose logs -f videorag-web-dev          # 查看开发日志
docker compose logs -f videorag-web-prod         # 查看生产日志
docker compose down                              # 停止所有服务
docker compose down -v                          # 停止并删除数据卷
```

## 核心架构

VideoRAG采用三层架构设计：

### 1. VideoRAG算法核心 (`VideoRAG-algorithm/`)
- **双通道架构**: 图驱动文本知识索引 + 分层多模态上下文编码
- **支持任意长度视频分析**，多模态理解：视频、音频、文本
- **AI模型集成**: GPT、Qwen-VL、ImageBind、Whisper等
- **核心模块**:
  - `videorag.py`: 主要VideoRAG类，实现索引构建和查询
  - `_llm.py`: LLM配置和调用（OpenAI、DashScope、本地模型）
  - `_videoutil/`: 视频处理工具（ASR、特征提取、视频分割）
  - `_storage/`: 多种存储后端（Neo4j、NanoVectorDB、JSON）
  - `_op.py`: 核心操作（分块、实体提取、查询处理）

### 2. Python后端API (`backend/`)
- **Flask Web框架**，提供RESTful API
- **视频处理流程**: 上传 → ASR转录 → 视觉特征提取 → 索引构建
- **异步处理**: 长时间任务的多进程处理
- **会话管理**: 多视频会话支持和状态追踪
- **核心文件**:
  - `videorag_web_api.py`: 主API服务器
  - `videorag_api.py`: VideoRAG包装器和进程管理

### 3. React Web前端 (`web/`)
- **React 18 + TypeScript + Vite + TailwindCSS**
- **响应式设计**，组件化架构
- **核心组件**:
  - `VideoUpload`: 视频上传和处理进度
  - `ChatInterface`: 对话界面和会话管理
  - `InitializationWizard`: 系统初始化配置
  - 设置页面：API密钥配置、模型选择、存储管理

## 项目结构

```
videoagent/
├── VideoRAG-algorithm/         # 核心算法实现
│   └── videorag/               # Python包
│       ├── videorag.py         # 主要VideoRAG类
│       ├── _llm.py             # LLM配置和调用
│       └── _videoutil/         # 视频处理工具 (asr.py, feature.py, split.py)
├── backend/                    # Flask API服务器
│   ├── videorag_web_api.py     # Web API服务
│   └── videorag_api.py         # VideoRAG包装器
├── web/                        # React前端
│   ├── src/
│   │   ├── components/         # React组件 (VideoUpload, ChatInterface, etc.)
│   │   ├── services/           # API客户端服务
│   │   ├── pages/              # 页面组件
│   │   └── utils/              # 工具函数
│   ├── package.json
│   └── vite.config.ts          # Vite构建配置
├── storage/                    # 数据持久化
├── uploads/                    # 视频上传缓存
├── models/                     # AI模型文件 (ImageBind等)
├── logs/                       # 应用日志
├── docker/                     # Docker相关文件
├── scripts/                    # 开发脚本
├── .env.template               # 环境变量模板
├── start_dev.sh               # 本地开发启动脚本
├── torchvision_fix.py         # torchvision兼容性修复
└── reload_services.py         # 服务重启脚本
```

## API接口参考

### 核心端点
- `/api/health` - 健康检查
- `/api/system/status` - 系统状态检查
- `/api/initialize` - 全局系统配置初始化
- `/api/sessions/{chatId}/videos/upload` - 上传视频
- `/api/sessions/{chatId}/status` - 检查视频处理状态
- `/api/sessions/{chatId}/videos/indexed` - 列出已处理视频
- `/api/sessions/{chatId}/query` - 视频内容查询
- `/api/videorag/defaults` - 获取默认配置值
- `/api/imagebind/check-status` - 检查ImageBind模型状态
- `/api/imagebind/download` - 下载ImageBind模型

## 环境配置

### 必需环境变量
```bash
cp .env.template .env

# 核心API密钥
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
ALI_DASHSCOPE_API_KEY=your_dashscope_api_key
ALI_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型配置
ANALYSIS_MODEL=gpt-4                    # 详细分析任务
PROCESSING_MODEL=gpt-3.5-turbo          # 批量处理任务
CAPTION_MODEL=qwen-vl-plus              # 视频理解模型
ASR_MODEL=whisper-1                     # 语音识别模型

# ASR处理模式
ASR_MODE=local                          # local: 本地处理, api: 云端处理

# 字幕生成模型配置（重要）
USE_GGUF_CAPTION=true                   # true: 使用GGUF模型, false: 使用原有MiniCPM-V模型
CAPTION_MODEL_PATH=/data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/Model-7.6B-Q4_K_M.gguf

# 存储配置
IMAGEBIND_MODEL_PATH=/app/models/imagebind.pth
BASE_STORAGE_PATH=/app/storage

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=64451
INTERNAL_PORT=64451

# 嵌入模型配置 (新增)
EMBEDDING_API_KEY=                      # 嵌入模型API密钥
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL_NAME=text-embedding-v4
EMBEDDING_MODEL_DIM=1024
```

## 开发调试

### 本地开发优势
- **快速迭代**: 代码修改后3-10秒重启，相比Docker的10-15分钟
- **直接调试**: 本地开发调试，无容器限制
- **资源效率**: 低资源消耗，无重复构建
- **兼容性测试**: 直接本地运行，避免glibc问题

### 关键开发原则
- **虚拟环境**: 必须使用 `/data/项目/videoagent/venv` 进行所有Python测试
- **测试效率**: 通过抽样和减少参数范围提高测试效率
- **时间管理**: 避免长时间完整测试，优先关键功能验证
- **错误日志**: 关注错误发生时间和修复状态，避免重复处理已修复问题

### 兼容性修复
项目包含特殊的兼容性修复：
- **torchvision兼容性**: `torchvision_fix.py` 修复PyTorchVideo和ImageBind导入问题
- **glibc兼容性**: Dockerfile.dev包含完整的兼容性测试流程
- **服务管理**: `reload_services.py` 提供便捷的服务重启功能

### 调试工作流
```bash
# 1. 激活虚拟环境
source /data/项目/videoagent/venv/bin/activate

# 2. 检查依赖
pip install -r requirements.txt

# 3. 应用兼容性修复
python torchvision_fix.py

# 4. 测试核心模块
python -c "import videorag; print('核心模块正常')"

# 5. 启动开发环境
./start_dev.sh
```

## 故障排除

### 常见问题

**1. 服务启动失败:**
```bash
# 检查端口占用
lsof -i :3000 -i :64451 -i :8125

# 查看Docker日志
docker compose logs videorag-web-dev
docker compose logs videorag-web-prod

# 本地模式查看后端日志
tail -f logs/videorag.log
```

**2. API连接失败:**
```bash
# 测试连接
curl http://localhost:64451/api/health

# 检查环境变量
env | grep -E "(API_KEY|PORT)"
```

**3. torchvision兼容性问题:**
```bash
# 运行修复脚本
python torchvision_fix.py

# 手动测试导入
python -c "import pytorchvideo; import imagebind; print('导入成功')"
```

**4. 视频处理问题:**
- 支持格式：MP4, WebM, OGG, MOV, AVI, MKV
- 文件大小限制：最大2GB
- 检查存储空间：推荐50GB+可用空间
- 查看详细错误日志

**5. 模型相关问题:**
```bash
# 检查ImageBind模型状态
curl -X POST http://localhost:64451/api/imagebind/check-status

# 重新下载模型
curl -X POST http://localhost:64451/api/imagebind/download
```

**6. 字幕生成模型问题:**
```bash
# 检查GGUF模型文件
ls -la /data/项目/videoagent/models/MiniCPM-o-2_6-gguf/.cache/huggingface/download/

# 验证模型文件完整性
python3 -c "
from llama_cpp import Llama
try:
    model = Llama.from_pretrained(
        repo_id='openbmb/MiniCPM-o-2_6-gguf',
        filename='Model-7.6B-Q4_K_M.gguf',
        n_ctx=100,
        n_gpu_layers=0,
        verbose=False
    )
    print('GGUF模型加载成功')
except Exception as e:
    print(f'GGUF模型加载失败: {e}')
"

# 切换字幕生成模式
# 编辑 .env 文件，修改 USE_GGUF_CAPTION=true/false
# 然后重启服务

# 检查MiniCPM-V模型（如果使用传统模式）
ls -la /data/项目/videoagent/models/MiniCPM-V-2_6-int4/
```

**7. 本地开发环境问题:**
```bash
# 重新激活虚拟环境（必须使用项目指定路径）
source /data/项目/videoagent/venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt

# 应用torchvision修复
python torchvision_fix.py

# 验证核心功能
python -c "import videorag; print('VideoRAG正常')"
"

# 测试字幕生成模型
python3 -c "
import os
os.environ['USE_GGUF_CAPTION'] = 'true'
from videorag._videoutil.caption import segment_caption
print('字幕生成模块导入成功')
"
```

### 重要开发约束
- **虚拟环境**: 必须使用 `/data/项目/videoagent/venv` 虚拟环境进行所有测试
- **测试原则**: 测试时考虑时间效率，通过抽样减少参数范围
- **禁止操作**: 不要手工启动 `npm run dev`，必须由用户控制
- **Docker构建**: 需要给10分钟timeout，并单独输出日志文件
- **错误处理**: 遇到 `Error editing file` 要先检查原因，不要反复重试

## 核心算法特性

### VideoRAG双通道架构
1. **图驱动文本知识索引**: 构建视频内容的语义图结构
2. **分层多模态上下文编码**: 视觉、听觉、文本信息的融合表示

### 视频处理流水线
```
视频上传 → 格式验证 → ASR转录 → 视频分割 → 特征提取 → 索引构建 → 就绪状态
```

### 模型集成策略
- **OpenAI GPT**: 文本生成和对话管理
- **阿里云Qwen-VL**: 视觉理解和视频描述
- **ImageBind**: 多模态特征提取（视频、音频、文本）
- **Whisper**: 语音识别和转录（本地/云端可选）

### 字幕生成模型架构
项目支持两种字幕生成模式，通过 `USE_GGUF_CAPTION` 环境变量控制：

#### 1. GGUF模式（推荐，`USE_GGUF_CAPTION=true`）
- **模型**: MiniCPM-o-2_6 (GGUF格式，量化版本)
- **特点**: 纯文本处理，基于ASR转录生成字幕描述
- **优势**:
  - 资源占用少（4-bit量化，约7.6B参数）
  - 处理速度快，适合大规模视频处理
  - 完全离线运行，无需GPU
- **文件**: `Model-7.6B-Q4_K_M.gguf`

#### 2. MiniCPM-V模式（`USE_GGUF_CAPTION=false`）
- **模型**: MiniCPM-V-2_6-int4 (原始版本)
- **特点**: 多模态模型，同时处理视频帧和音频转录
- **优势**:
  - 直接理解视频内容，生成更准确的字幕
  - 支持视觉信息综合分析
- **要求**: 需要GPU支持，资源占用较大

#### 选择建议
- **生产环境**: 推荐使用GGUF模式，性能和资源效率更佳
- **研究开发**: 使用MiniCPM-V模式，获得更好的视频理解能力
- **资源受限设备**: 必须使用GGUF模式

### 存储层架构
- **Neo4j**: 图数据库，存储实体关系和语义结构
- **NanoVectorDB**: 向量数据库，存储多模态嵌入
- **JSON**: 轻量级配置和元数据存储

## 性能优化指南

### 处理大型视频
- **分块策略**: 自动将长视频分割为可管理的片段
- **并行处理**: 多进程处理视频转录和特征提取
- **缓存机制**: 嵌入和中间结果的智能缓存

### API调用优化
- **批量处理**: 合并多个小请求以减少API调用
- **模型选择**: 根据任务复杂度选择合适的模型
- **超时控制**: 为长时间操作设置合理的超时时间