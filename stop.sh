#!/bin/bash

# VideoRAG Web Application Stop Script
set -e

echo "🛑 Stopping VideoRAG Web Application..."

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
docker-compose down

# Optional: Remove Docker volumes (uncomment if you want to clean up data)
# echo "🗑️  Removing Docker volumes..."
# docker-compose down -v

# Optional: Remove Docker images (uncomment if you want to clean up images)
# echo "🗑️  Removing Docker images..."
# docker-compose down --rmi all

echo "✅ VideoRAG Web Application stopped successfully!"
echo ""
echo "📋 To start the application again, run: ./start.sh"