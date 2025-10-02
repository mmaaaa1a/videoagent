# Multi-stage Dockerfile for VideoRAG Web Application
FROM node:20-alpine AS frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy package files
COPY Vimo-desktop/package*.json ./
COPY Vimo-desktop/pnpm-lock.yaml ./

# Install pnpm and dependencies
RUN npm install -g pnpm@9.10.0
RUN pnpm install --frozen-lockfile

# Copy frontend source code
COPY Vimo-desktop/src ./src
COPY Vimo-desktop/index.html ./
COPY Vimo-desktop/vite.config.ts ./

# Build frontend
RUN pnpm build

# Web frontend stage
FROM node:20-alpine AS web-frontend

WORKDIR /app/web

# Copy web package files
COPY web/package*.json ./

# Install dependencies
RUN npm install

# Copy web source code
COPY web/src ./src
COPY web/index.html ./
COPY web/vite.config.ts ./
COPY web/tsconfig.json ./
COPY web/tsconfig.node.json ./

# Build web frontend
RUN npm run build

# Python backend stage
FROM python:3.10-slim AS backend

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    ffmpeg \
    libsm6 \
    libxext6 \
    libfontconfig1 \
    libxrender1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy VideoRAG algorithm
COPY VideoRAG-algorithm ./VideoRAG-algorithm

# Copy Python backend
COPY Vimo-desktop/python_backend ./python_backend

# Create necessary directories
RUN mkdir -p /app/uploads /app/storage /app/logs

# Copy web frontend build files
COPY --from=web-frontend /app/web/dist ./static

# Set permissions
RUN chmod +x /app/python_backend/videorag_api.py

# Create startup script
RUN echo '#!/bin/bash\n\
cd /app\n\
python python_backend/videorag_web_api.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 64451

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:64451/api/health || exit 1

# Start the application
CMD ["/app/start.sh"]