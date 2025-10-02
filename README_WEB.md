# VideoRAG 网页版部署指南

VideoRAG是一个革命性的视频对话应用，现在支持通过Docker部署为网页版，让您可以在浏览器中与视频进行AI对话。

## 🌟 功能特性

### 核心功能
- **🎬 智能视频对话**: 与任意视频进行自然语言对话
- **📁 多视频支持**: 同时上传和分析多个视频
- **⚡ 极长视频处理**: 支持数百小时视频内容分析
- **🔍 精准检索**: 快速定位视频中的特定场景和内容
- **💾 对话历史**: 保存和管理对话记录

### Web版特性
- **🌐 浏览器访问**: 无需安装客户端，直接通过浏览器使用
- **📱 响应式设计**: 支持桌面和移动设备
- **🎨 简洁界面**: 采用卡片式设计，留白优雅
- **🔒 安全部署**: Docker容器化部署，数据本地存储

## 🚀 快速开始

### 系统要求

- **操作系统**: Linux, macOS, Windows (支持Docker)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 建议8GB以上
- **存储**: 建议50GB以上可用空间
- **网络**: 需要访问OpenAI和阿里云API

### 一键部署

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd videoagent
   ```

2. **配置API密钥**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入您的API密钥
   ```

3. **启动应用**
   ```bash
   ./start.sh
   ```

4. **访问应用**

   打开浏览器访问: http://localhost:64451

## ⚙️ 配置说明

### 环境变量配置

编辑 `.env` 文件配置以下参数：

```bash
# OpenAI API配置（必需）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 阿里云DashScope API配置（必需）
ALI_DASHSCOPE_API_KEY=your_dashscope_api_key_here
ALI_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 模型配置
ANALYSIS_MODEL=gpt-4                    # 分析模型
PROCESSING_MODEL=gpt-3.5-turbo          # 处理模型
CAPTION_MODEL=qwen-vl-plus              # 视频理解模型
ASR_MODEL=whisper-1                     # 语音识别模型

# 存储配置
BASE_STORAGE_PATH=/app/storage          # 数据存储路径
IMAGEBIND_MODEL_PATH=/app/models/imagebind.pth  # 模型文件路径

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=64451
```

### API密钥获取

#### OpenAI API密钥
1. 访问 [OpenAI API](https://platform.openai.com/api-keys)
2. 注册/登录账户
3. 创建新的API密钥
4. 复制密钥到 `.env` 文件中的 `OPENAI_API_KEY`

#### 阿里云DashScope API密钥
1. 访问 [阿里云DashScope](https://dashscope.aliyuncs.com/)
2. 注册/登录账户
3. 开通DashScope服务
4. 创建API密钥
5. 复制密钥到 `.env` 文件中的 `ALI_DASHSCOPE_API_KEY`

## 📁 目录结构

```
videoagent/
├── web/                    # Web前端源码
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API服务
│   │   └── styles/         # 样式文件
│   └── package.json
├── VideoRAG-algorithm/     # VideoRAG算法核心
├── Vimo-desktop/
│   └── python_backend/     # Python后端API
├── docker-compose.yml      # Docker编排配置
├── Dockerfile             # Docker镜像配置
├── .env.example           # 环境变量模板
├── start.sh               # 启动脚本
├── stop.sh                # 停止脚本
├── start-dev.sh           # 开发模式启动脚本
└── README_WEB.md          # 本文档
```

## 🛠️ 运维管理

### 启动服务
```bash
./start.sh              # 生产模式启动
./start-dev.sh          # 开发模式启动
```

### 停止服务
```bash
./stop.sh               # 停止所有服务
```

### 查看日志
```bash
docker-compose logs -f  # 查看实时日志
docker-compose logs -f videorag-web  # 查看应用日志
```

### 重启服务
```bash
docker-compose restart  # 重启所有服务
docker-compose restart videorag-web  # 重启应用
```

### 进入容器
```bash
docker-compose exec videorag-web bash  # 进入应用容器
```

### 数据备份
```bash
# 备份重要数据
tar -czf backup-$(date +%Y%m%d).tar.gz storage uploads logs
```

## 🌐 访问地址

### 生产环境
- **Web应用**: http://localhost:64451
- **API文档**: http://localhost:64451/api/health

### 开发环境
- **前端开发服务器**: http://localhost:3000
- **后端API服务器**: http://localhost:64451

## 📊 监控和调试

### 健康检查
```bash
curl http://localhost:64451/api/health
```

### 系统状态
```bash
curl http://localhost:64451/api/system/web-status
```

### 常用命令
```bash
# 查看容器状态
docker-compose ps

# 查看资源使用情况
docker stats

# 查看磁盘使用情况
df -h

# 查看内存使用情况
free -h
```

## 🔧 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用情况
lsof -i :64451

# 停止占用端口的进程或修改 docker-compose.yml 中的端口映射
```

#### 2. API密钥错误
- 检查 `.env` 文件中的API密钥是否正确
- 确认API密钥有足够的权限和余额
- 检查网络连接是否正常

#### 3. 视频处理失败
- 检查视频文件格式是否支持
- 确认视频文件大小不超过2GB
- 查看应用日志了解具体错误信息

#### 4. 内存不足
```bash
# 增加Docker内存限制
# 在 docker-compose.yml 中添加:
services:
  videorag-web:
    deploy:
      resources:
        limits:
          memory: 8G
```

#### 5. 模型文件缺失
- 确认ImageBind模型文件存在
- 检查 `IMAGEBIND_MODEL_PATH` 配置是否正确
- 模型文件会自动下载到 `/app/models/` 目录

### 日志分析

#### 查看详细日志
```bash
# 查看应用日志
docker-compose logs videorag-web | grep ERROR

# 查看最近100行日志
docker-compose logs --tail=100 videorag-web

# 实时监控日志
docker-compose logs -f --tail=50 videorag-web
```

#### 日志文件位置
- **应用日志**: `./logs/`
- **上传文件**: `./uploads/`
- **处理结果**: `./storage/`

## 🔒 安全注意事项

1. **API密钥安全**
   - 不要将 `.env` 文件提交到版本控制
   - 定期更换API密钥
   - 使用最小权限原则配置API密钥

2. **网络安全**
   - 在生产环境中使用HTTPS
   - 配置防火墙规则
   - 限制访问IP地址

3. **数据安全**
   - 定期备份重要数据
   - 设置适当的文件权限
   - 监控异常访问行为

## 🆙 升级和更新

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose up --build -d
```

### 数据迁移
```bash
# 备份现有数据
./backup.sh

# 更新应用
./update.sh

# 恢复数据（如需要）
./restore.sh backup-YYYYMMDD.tar.gz
```

## 📞 技术支持

如遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查GitHub Issues页面
3. 提交新的Issue并提供详细信息：
   - 错误描述
   - 系统环境
   - 相关日志
   - 复现步骤

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。