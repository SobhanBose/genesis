#!/bin/bash

# Build script for FL API Docker image

set -e

echo "🐳 Building FL API Docker image..."

# Build the Docker image
docker build -t fl-api:latest .

echo "📊 Image size:"
docker images fl-api:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo "✅ Build complete!"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 fl-api:latest"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"