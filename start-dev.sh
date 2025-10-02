#!/bin/bash

# VideoRAG Web Application Development Startup Script
set -e

echo "🚀 Starting VideoRAG Web Application in Development Mode..."

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
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p storage uploads logs models

# Start the development application
echo "🐳 Building and starting development containers..."
docker-compose -f docker-compose.dev.yml up --build

echo "✅ VideoRAG Web Development Environment is ready!"
echo "🌐 Frontend development server: http://localhost:3000"
echo "🔧 Backend API server: http://localhost:64451"
echo ""
echo "📋 Development commands:"
echo "   View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   Stop environment: docker-compose -f docker-compose.dev.yml down"
echo "   Access container shell: docker-compose -f docker-compose.dev.yml exec videorag-web-dev bash"