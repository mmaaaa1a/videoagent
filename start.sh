#!/bin/bash

# VideoRAG Web Application Startup Script
set -e

echo "🚀 Starting VideoRAG Web Application..."

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $port is already in use"
        return 1
    else
        echo "Port $port is available"
        return 0
    fi
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running again."
    echo "   Required variables:"
    echo "   - OPENAI_API_KEY"
    echo "   - ALI_DASHSCOPE_API_KEY"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p storage uploads logs models

# Check if ports are available
API_PORT=64451
if ! check_port $API_PORT; then
    echo "❌ Port $API_PORT is already in use. Please stop the service using this port or change the port in docker-compose.yml"
    exit 1
fi

# Start the application
echo "🐳 Building and starting Docker containers..."
docker-compose up --build -d

# Wait for the service to be ready
echo "⏳ Waiting for VideoRAG service to be ready..."
sleep 10

# Check if service is running
if curl -f http://localhost:$API_PORT/api/health > /dev/null 2>&1; then
    echo "✅ VideoRAG Web Application is running successfully!"
    echo "🌐 Access the application at: http://localhost:$API_PORT"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop application: docker-compose down"
    echo "   Restart application: docker-compose restart"
    echo ""
    echo "📁 Data directories:"
    echo "   - Uploads: ./uploads"
    echo "   - Storage: ./storage"
    echo "   - Logs: ./logs"
    echo "   - Models: ./models"
else
    echo "❌ Failed to start VideoRAG service. Check logs with: docker-compose logs"
    exit 1
fi