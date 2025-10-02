# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

VideoRAG是一个革命性的桌面应用程序，允许用户通过AI技术与视频进行对话。该项目基于VideoRAG框架构建，能够理解并分析任意长度的视频内容。

### 项目结构

```
videoagent/
├── VideoRAG-algorithm/     # VideoRAG核心算法实现 (Python)
│   ├── videorag/          # 核心VideoRAG模块
│   ├── examples/          # 示例脚本
│   ├── longervideos/      # 长视频基准测试
│   └── reproduce/         # 实验复现脚本
├── Vimo-desktop/          # 桌面应用程序 (Electron + React)
│   ├── src/
│   │   ├── main/          # Electron主进程
│   │   ├── renderer/      # React前端渲染进程
│   │   └── preload/       # 预加载脚本
│   ├── python_backend/    # Python后端API服务
│   └── figures/           # 图片资源
└── README.md
```

## 开发环境设置

### Python后端环境

1. **VideoRAG算法环境**：
   ```bash
   cd VideoRAG-algorithm
   pip install -r requirements.txt  # 如有requirements.txt文件
   ```

2. **Python版本**：推荐使用Python 3.8+
3. **关键依赖**：
   - transformers (Hugging Face)
   - torch (PyTorch)
   - networkx (图处理)
   - neo4j (图数据库，可选)

### 前端桌面应用环境

1. **Node.js版本**：>= 20.x (根据package.json engines配置)
2. **包管理器**：pnpm (版本 9.10.0)

## 常用命令

### 桌面应用开发命令 (Vimo-desktop)

```bash
cd Vimo-desktop

# 安装依赖
pnpm install

# 开发模式启动
pnpm dev

# 代码格式化
pnpm format

# 代码检查和修复
pnpm lint

# 构建应用
pnpm build
```

### VideoRAG算法相关命令

```bash
cd VideoRAG-algorithm

# 处理视频示例
python examples/process_videos_deepseek.py

# 查询视频示例
python examples/query_videos_deepseek.py

# 运行VideoRAG
python videorag_longervideos.py
```

## 核心架构

### VideoRAG算法架构

1. **双通道架构**：
   - 图驱动文本知识索引：跨视频语义关系建模
   - 分层多模态上下文编码：保持时空视觉模式

2. **核心组件**：
   - `videorag/videorag.py`: 主要VideoRAG类实现
   - `videorag/_llm.py`: LLM配置和接口
   - `videorag/_op.py`: 核心操作实现
   - `videorag/_storage/`: 存储层实现

3. **存储支持**：
   - Neo4j图数据库
   - NetworkX图处理
   - JSON键值存储

### 桌面应用架构

1. **Electron主进程** (`src/main/`):
   - `main.ts`: 应用入口点
   - `handlers/`: IPC处理器，包括VideoRAG处理器、文件处理器等

2. **React渲染进程** (`src/renderer/`):
   - `App.tsx`: 主应用组件
   - `components/`: UI组件
   - `pages/`: 页面组件
   - `contexts/`: React上下文
   - `utils/`: 工具函数

3. **Python后端** (`python_backend/`):
   - `videorag_api.py`: VideoRAG API服务
   - `videorag/`: VideoRAG算法模块

## 开发注意事项

### API密钥配置

在使用VideoRAG功能前，需要配置相应的API密钥：
- DeepSeek API密钥
- SiliconFlow API密钥
- 其他LLM服务API密钥

### 文件处理

- 支持多种视频格式：MP4, MKV, AVI等
- 支持处理极长视频（数百小时）
- 支持多视频同时分析和比较

### 性能优化

- 可在单个NVIDIA RTX 3090 (24GB)上处理数百小时视频内容
- 使用图结构索引压缩视频知识表示
- 动态知识图构建保持语义连贯性

## 测试和调试

### 视频处理测试

使用examples目录中的示例脚本进行测试：
```bash
# 处理单个视频进行测试
python examples/process_videos_deepseek.py --video-path test_video.mp4

# 查询测试
python examples/query_videos_deepseek.py
```

### 前端调试

使用Electron开发者工具进行前端调试，启动开发模式后会自动打开DevTools。

## 部署和构建

### 桌面应用构建

```bash
cd Vimo-desktop
pnpm build  # 构建所有目标
```

构建产物位于 `dist/` 目录。

### Python环境打包

如需打包Python环境，可使用PyInstaller或类似工具：
```bash
pip install pyinstaller
pyinstaller --onefile videorag_api.py
```