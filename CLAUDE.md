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
# 语法检查
python -m py_compile backend/videorag_web_api.py

# 模块导入测试
python -c "import videorag; print('模块导入成功')"

# torchvision兼容性修复
python torchvision_fix.py

# 服务重启
python reload_services.py
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

### 1. VideoRAG算法核心
- 双通道架构：图驱动文本知识索引 + 分层多模态上下文编码
- 支持任意长度视频分析，多模态理解：视频、音频、文本
- AI模型集成：GPT、Qwen-VL、ImageBind等

### 2. Python后端API
- Flask Web框架，提供RESTful API
- 视频处理：上传、分析、索引构建，会话管理
- 异步处理：长时间任务的多进程处理

### 3. React Web前端
- React 18 + TypeScript + Vite + TailwindCSS
- 响应式设计，组件化架构：视频上传、对话界面、设置管理

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
- **直接调试**: 本地产开调试，无容器限制
- **资源效率**: 低资源消耗，无重复构建
- **兼容性测试**: 直接本地运行，避免glibc问题

### 兼容性修复
项目包含特殊的兼容性修复：
- **torchvision兼容性**: `torchvision_fix.py` 修复PyTorchVideo和ImageBind导入问题
- **glibc兼容性**: Dockerfile.dev包含完整的兼容性测试流程
- **服务管理**: `reload_services.py` 提供便捷的服务重启功能

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

**6. 本地开发环境问题:**
```bash
# 重新激活虚拟环境
source venv/bin/activate  # 或实际环境路径

# 重新安装依赖
pip install -r requirements.txt

# 应用torchvision修复
python torchvision_fix.py
```