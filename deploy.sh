#!/bin/bash

# AI SAMRAT Production Deployment Script
# This script deploys the AI SAMRAT application to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ai-samrat"
DOCKER_REGISTRY="your-registry.com"
VERSION=${1:-latest}
ENVIRONMENT=${2:-production}

echo -e "${GREEN}🚀 Starting AI SAMRAT Deployment${NC}"
echo -e "${YELLOW}Version: $VERSION${NC}"
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${GREEN}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p uploads
mkdir -p reports
mkdir -p nginx/ssl
mkdir -p static

# Set permissions
chmod 755 logs uploads reports static

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📋 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env file with your production values!${NC}"
    echo -e "${RED}⚠️  Especially update SECRET_KEY and domain settings!${NC}"
    read -p "Press Enter after editing .env file..."
fi

# Build and start services
echo -e "${GREEN}🔨 Building Docker images...${NC}"
docker-compose build

echo -e "${GREEN}🚢 Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${GREEN}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${GREEN}🏥 Checking service health...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose logs app
    exit 1
fi

# Check if frontend is accessible
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend might not be ready yet (HTTPS configuration needed)${NC}"
fi

# Show running containers
echo -e "${GREEN}📊 Running containers:${NC}"
docker-compose ps

# Show logs
echo -e "${GREEN}📝 Recent logs:${NC}"
docker-compose logs --tail=20

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📍 Application is running at: http://localhost${NC}"
echo -e "${GREEN}📍 Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}📍 Health check: http://localhost:8000/health${NC}"

# Show useful commands
echo -e "${YELLOW}📖 Useful commands:${NC}"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update application: git pull && docker-compose up -d --build"

echo -e "${GREEN}✨ Deployment complete!${NC}"
