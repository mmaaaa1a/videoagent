# VideoRAG: Web Video Conversational AI

<div align="center">
  <h1>
    <strong>VideoRAG: Chat with Your Videos</strong> • <strong>Web Application</strong>
  </h1>

  <a href='https://arxiv.org/abs/2502.01549'><img src='https://img.shields.io/badge/arXiv-2502.01549-b31b1b'></a>
  [![Platform](https://img.shields.io/badge/platform-Web%20%7C%20Docker-lightgrey.svg)]()

  **🎬 Intelligent Video Conversations | Powered by Advanced AI | Browser-Based Access**

</div>

<br/>

VideoRAG is a revolutionary web application that lets you **chat with your videos** using cutting-edge AI technology. Built on the powerful [VideoRAG framework](https://arxiv.org/abs/2502.01549), it can understand and analyze videos of any length - from short clips to hundreds of hours of content - and answer your questions with remarkable accuracy.

## ✨ Key Features

- **🌐 Browser Access**: No installation required, works in any modern browser
- **🎬 Smart Video Conversations**: Ask questions about video content in natural language
- **📁 Multi-Video Support**: Upload and analyze multiple videos simultaneously
- **⚡ Extreme Long Videos**: Process videos up to hundreds of hours
- **🔍 Precise Retrieval**: Find specific moments and scenes with high accuracy
- **💾 Conversation History**: Save and manage your video conversations
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🔒 Unified Configuration**: Single configuration entry point in settings page

## 🚀 Quick Start

VideoRAG supports multiple deployment modes suitable for different needs:

### 📋 System Requirements

- **CPU**: 2+ cores recommended, 4+ cores ideal
- **Memory**: 8GB+ RAM recommended
- **Storage**: 50GB+ available space
- **Docker**: 20.0+
- **Docker Compose**: 2.0+

### 🎯 Deployment Options

VideoRAG supports three main deployment approaches:

### 1. Development Mode (Hot Reload)

**Ideal for development and testing**
```bash
# Clone the repository
git clone <repository-url>
cd videoagent

# Configure API keys
cp .env.example .env
# Edit .env with your API keys

# Start development environment
docker-compose -f docker-compose.dev.yml up -d --build
```

**Access URLs:**
- **Web Application**: http://localhost:3000
- **API Endpoints**: http://localhost:64451

**Features:**
- Frontend hot reload for React code changes
- Backend hot reload for Python code changes
- Mounted volumes for live development
- Debug-friendly configuration

### 2. Production Mode (Optimized)

**Ready for production deployment**
```bash
# Clone and configure
git clone <repository-url>
cd videoagent

# Configure environment
cp .env.example .env
# Edit .env with production API keys

# Start production environment
docker-compose -f docker-compose.prod.yml up -d --build
```

**Access URLs:**
- **Web Application**: http://localhost:8125
- **API Documentation**: http://localhost:8125/api/health

**Features:**
- Optimized Docker layers for faster startup
- Health checks and auto-healing
- Production-ready resource limits
- Cached builds for optimal performance

### 3. Local Manual Setup (Without Docker)

**For advanced users who prefer local setup**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd web && npm install && cd ..

# Start backend API
python backend/videorag_web_api.py

# Start frontend (in another terminal)
cd web && npm run dev

# Alternatively, use provided scripts
./start-dev.sh    # Development mode
./start.sh        # Production mode
```

## ⚙️ Configuration

### Environment Variables Setup

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure required settings:**

```bash
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Alibaba DashScope API Configuration (Required)
ALI_DASHSCOPE_API_KEY=your_dashscope_api_key_here
ALI_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# AI Model Configuration
ANALYSIS_MODEL=gpt-4                    # GPT-4 recommended for analysis
PROCESSING_MODEL=gpt-3.5-turbo          # GPT-3.5-turbo for high-volume processing
CAPTION_MODEL=qwen-vl-plus              # Alibaba Qwen for video understanding
ASR_MODEL=whisper-1                     # OpenAI Whisper for speech recognition

# Storage Configuration
BASE_STORAGE_PATH=/app/storage          # Data storage directory
IMAGEBIND_MODEL_PATH=/app/models/imagebind.pth  # ImageBind model path

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8125                         # External port (host machine)
INTERNAL_PORT=64451                      # Internal port (Docker container)

# Development options
NODE_ENV=development
FLASK_ENV=development
```

### API Key Acquisition

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or log in
3. Generate a new API key
4. Set `OPENAI_API_KEY` in your `.env` file

#### Alibaba DashScope API Key
1. Visit [Alibaba DashScope](https://dashscope.aliyuncs.com/)
2. Register or log in to Alibaba Cloud account
3. Activate DashScope service
4. Generate API key in console
5. Set `ALI_DASHSCOPE_API_KEY` in your `.env` file

## 📁 Project Architecture

```
videoagent/
├── VideoRAG-algorithm/         # Core VideoRAG algorithm framework
│   └── src/                    # Algorithm implementation
├── backend/                    # Python Flask API server
│   ├── videorag_web_api.py     # Main API application
│   └── requirements.txt        # Python dependencies
├── web/                        # React web frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/           # API client services
│   │   └── pages/              # Page components (Chat, Settings)
│   ├── package.json
│   └── vite.config.ts         # Vite build configuration
├── storage/                    # Persistent data storage
├── uploads/                    # Temporary video uploads
├── logs/                       # Application logs
└── models/                     # AI model files
```

### Key Architectural Changes

**Simplified Configuration Flow:**
- **Removed**: Separate initialization wizard component
- **Added**: Unified configuration through settings page
- **Enhanced**: Settings page now handles first-time system initialization
- **Streamlined**: Single entry point for all configuration tasks

## 🛠️ Usage Guide

### First-Time Setup

1. **Start the application** using one of the deployment methods above
2. **Access the web interface** at http://localhost:3000
3. **Configure your API keys** in the settings page (automatically shown for new installations)
4. **Set storage preferences** if desired
5. **Wait for ImageBind model download** (happens automatically)
6. **Start uploading videos** and begin conversations!

### Using the Application

#### Uploading Videos
- Drag and drop video files or click to browse
- Supports: MP4, WebM, OGG, MOV, AVI, MKV (max 2GB per file)
- Videos are automatically processed and indexed for conversations

#### Starting Conversations
- Click on uploaded videos to start a chat session
- Ask questions in natural language
- Ask follow-up questions in the same conversation
- Switch between multiple video chat sessions

#### Managing Settings
- Access settings via the gear icon in header
- Configure individual API settings
- Adjust model preferences
- Modify storage directory paths
- Reset configuration if needed

## 📊 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/system/status` | GET | System status including initialization state |
| `/api/initialize` | POST | Initialize global system configuration |
| `/api/sessions/{chatId}/videos/upload` | POST | Upload video to chat session |
| `/api/sessions/{chatId}/status` | GET | Check video processing status |
| `/api/sessions/{chatId}/videos/indexed` | GET | List processed videos |
| `/api/sessions/{chatId}/query` | POST | Query video content |
| `/api/videorag/defaults` | GET | Get default configuration values |
| `/api/imagebind/check-status` | POST | Check ImageBind model status |
| `/api/imagebind/download` | POST | Download ImageBind model |

### Request Example

```bash
# Query video content
curl -X POST http://localhost:64451/api/sessions/123/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What happened in the middle of the video?"}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. ImageBind Model Not Found
**Symptoms:** Settings page shows "模型未找到" despite model being present
**Solution:**
- Check model path in settings matches actual file location
- Verify Docker volume mounts are correct
- Try clicking "检查状态" (Check Status) button
- Model will auto-download if missing

#### 2. Port Conflicts
**Symptoms:** Container fails to start due to port in use
**Solution:**
```bash
# Check what's using ports
lsof -i :3000 -i :64451 -i :8125

# Change ports in .env file
SERVER_PORT=8126
INTERNAL_PORT=64452
```

#### 3. API Key Authentication Failures
**Solutions:**
- Verify API keys are correct in `.env` file
- Check API key permissions and quota
- Confirm network connectivity to API providers
- Restart containers after key changes

#### 4. Video Processing Failures
**Check:**
- Video format supported (MP4, WebM, OGG, MOV, AVI, MKV)
- File size under 2GB limit
- Sufficient disk space (50GB+ recommended)
- View detailed logs for specific error messages

#### 5. Memory Issues
**Symptoms:** Processing fails or containers restart
**Solutions:**
```bash
# Check system memory
free -h

# Increase Docker memory in docker-compose.yml
services:
  videorag-web-dev:
    deploy:
      resources:
        limits:
          memory: 12G
```

#### 6. Configuration Issues After Updates
**Symptoms:** Application doesn't reflect new settings
**Solution:**
- Settings are cached in localStorage
- Click "重置系统配置" (Reset System Config) in settings
- Or clear browser localStorage and refresh

### Logs and Monitoring

#### Application Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f videorag-web-dev
docker-compose logs -f backend-dev

# Export logs for analysis
docker-compose logs > logs-$(date +%Y%m%d).txt
```

#### System Monitoring
```bash
# Check container resource usage
docker stats

# Check disk space
df -h

# Check network connectivity
ping api.openai.com
ping dashscope.aliyuncs.com
```

## 🔄 GitHub Actions Automation

### Automated Deployment Setup

1. **Configure GitHub Secrets:**
   ```
   # Server access
   SERVER_HOST=your-server-ip
   SERVER_USER=your-username
   SERVER_SSH_KEY=your-private-ssh-key
   SERVER_PATH=/opt/videoagent
   SERVER_DOMAIN=yourdomain.com

   # Optional: Development deployment
   DEV_SERVER_HOST=dev-server-ip
   DEV_SERVER_USER=dev-username
   DEV_SERVER_SSH_KEY=dev-ssh-key
   ```

2. **Automated Triggers:**
   - **main branch** → Production deployment
   - **develop branch** → Development deployment
   - **Pull requests** → Code quality checks and testing
   - **Manual dispatch** → On-demand deployment

## 🏗️ Building from Source

### Prerequisites for Local Development

```bash
# Node.js for frontend
node --version  # v20.0+
npm --version   # v8.0+

# Python for backend
python --version  # v3.10+
pip --version
```

### Development Setup

```bash
# Frontend development
cd web
npm install
npm run dev

# Backend development (separate terminal)
cd backend
python videorag_web_api.py
```

### Production Build

```bash
# Full stack build
docker-compose -f docker-compose.prod.yml build

# Optimized frontend build only
cd web && npm run build
```

## 🔒 Security Best Practices

1. **API Key Management**
   - Never commit `.env` to version control
   - Rotate API keys regularly
   - Use minimal required permissions
   - Monitor API usage for anomalies

2. **Network Security**
   - Configure HTTPS in production
   - Use firewall rules
   - Consider IP restrictions
   - Monitor for suspicious access

3. **Data Protection**
   - Regular backups of data directories
   - Enforce proper file permissions
   - Encrypt sensitive data at rest
   - Log access and audit activities

## 📈 Performance Optimization

### System Tuning

- **CPU**: Use multi-core systems (4+ cores recommended)
- **Memory**: 8-16GB RAM for optimal performance
- **Storage**: SSD storage with 100MB/s+ throughput
- **Network**: Stable internet for API calls

### Application Optimization

- **Model Selection**: Choose appropriate models for your use case
- **Batch Processing**: Process multiple videos efficiently
- **Caching**: Utilize built-in caching for repeated queries
- **Resource Limits**: Configure appropriate Docker resource limits

## 🆘 Support and Community

### Getting Help

1. **Documentation First**: Check this README and setup guides
2. **Community Support**:
   - Search existing GitHub Issues
   - Join discussions in Discussions tab
   - Check the VideoRAG paper for technical details

3. **Reporting Issues**: When submitting bug reports, include:
   - VideoRAG version and commit hash
   - Docker and system versions
   - Complete error logs and stack traces
   - Steps to reproduce the issue
   - Environment details (OS, resources)

### Development and Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a feature branch: `git checkout -b feature/new-feature`
4. **Make** your changes following our development guidelines
5. **Test** thoroughly: unit tests, integration tests, manual testing
6. **Submit** a pull request with detailed description

### Code Quality Standards

- TypeScript/JavaScript: Strict mode, ESLint compliance
- Python: PEP 8 standards, type hints
- Testing: Minimum 80% code coverage
- Documentation: Clear, comprehensive docstrings and comments

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **VideoRAG Framework**: The core algorithm powering intelligent video conversations
- **OpenAI**: GPT model family for conversational AI
- **Alibaba Cloud**: DashScope API for multimodal understanding
- **Meta (Facebook)**: ImageBind model for cross-modal embeddings
- **Open-source Community**: Countless libraries enabling this work

---

🎉 **Welcome to the future of video interaction! Chat with any video, discover insights, and unlock the potential of your video content with VideoRAG.**