# VideoRAG 网页版 - 快速安装指南

5分钟内部署VideoRAG网页版应用！

## 🚀 一键部署

### 前置要求
- ✅ 已安装Docker
- ✅ 已安装Docker Compose
- ✅ 获取了OpenAI和阿里云API密钥

### 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd videoagent

# 2. 配置API密钥
cp .env.example .env
# 编辑 .env 文件，填入您的API密钥

# 3. 一键启动
./start.sh

# 4. 访问应用
# 浏览器打开: http://localhost:64451
```

## 🔑 API密钥配置

编辑 `.env` 文件，必须配置以下两项：

```bash
# OpenAI API密钥
OPENAI_API_KEY=sk-your-openai-key-here

# 阿里云DashScope API密钥
ALI_DASHSCOPE_API_KEY=sk-your-dashscope-key-here
```

### 如何获取API密钥？

#### OpenAI API密钥
1. 访问 https://platform.openai.com/api-keys
2. 点击 "Create new secret key"
3. 复制生成的密钥

#### 阿里云DashScope API密钥
1. 访问 https://dashscope.aliyuncs.com/
2. 注册/登录并开通服务
3. 在控制台创建API密钥

## ✅ 验证部署

启动成功后，您应该看到：

```bash
✅ VideoRAG Web Application is running successfully!
🌐 Access the application at: http://localhost:64451
```

在浏览器中访问 http://localhost:64451 即可开始使用！

## 🎯 首次使用

1. **初始化配置**: 首次访问需要配置API密钥
2. **上传视频**: 拖拽或选择视频文件上传
3. **开始对话**: 视频处理完成后即可开始对话

## 🛠️ 常用命令

```bash
./start.sh          # 启动应用
./stop.sh           # 停止应用
docker-compose logs -f  # 查看日志
```

## 🆘 遇到问题？

1. **端口被占用**: 修改 `docker-compose.yml` 中的端口映射
2. **API密钥错误**: 检查 `.env` 文件中的密钥是否正确
3. **内存不足**: 确保系统有8GB以上可用内存

详细文档请参考 [README_WEB.md](README_WEB.md)