# FL API Docker Deployment

This directory contains Docker configuration for the Federated Learning API server.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using Docker directly

```bash
# Build the image
./build.sh

# Run the container
docker run -d \
  --name fl-api \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/models:/app/models \
  fl-api:latest
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Key variables:
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEBUG`: Debug mode (default: false)

### Persistent Data

The following directories are mounted as volumes for data persistence:
- `./data` - Run metadata and storage
- `./logs` - Application logs
- `./results` - Training results
- `./models` - ML models

## Image Optimization

The Docker image is optimized for minimal size:
- Multi-stage build to exclude build dependencies
- Python slim base image
- Removed unnecessary files and caches
- Non-root user for security
- Health checks for container orchestration

## API Endpoints

Once running, the API will be available at:
- Health check: http://localhost:8000/api/v1/health
- API documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## Monitoring

### Health Checks

The container includes built-in health checks:
```bash
# Check container health
docker ps

# View health check logs
docker inspect fl-api | grep -A 10 Health
```

### Logs

```bash
# View container logs
docker logs fl-api

# Follow logs in real-time
docker logs -f fl-api

# With docker-compose
docker-compose logs -f fl-api
```

## Development

### Building

```bash
# Build the image
docker build -t fl-api:latest .

# Build with specific tag
docker build -t fl-api:v1.0.0 .
```

### Debugging

```bash
# Run with interactive shell
docker run -it --rm fl-api:latest /bin/bash

# Override entrypoint for debugging
docker run -it --rm --entrypoint /bin/bash fl-api:latest
```

## Production Deployment

For production deployment, consider:

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Secrets Management**: Use Docker secrets or external secret management
3. **Load Balancing**: Use multiple replicas behind a load balancer
4. **Monitoring**: Integrate with monitoring solutions (Prometheus, etc.)
5. **Backup**: Regular backup of persistent volumes

### Example Production Docker Compose

```yaml
version: '3.8'
services:
  fl-api:
    image: fl-api:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    environment:
      - LOG_LEVEL=warning
      - DEBUG=false
    volumes:
      - fl_data:/app/data
      - fl_logs:/app/logs
      - fl_results:/app/results
      - fl_models:/app/models
    networks:
      - fl-network

volumes:
  fl_data:
  fl_logs:
  fl_results:
  fl_models:

networks:
  fl-network:
    external: true
```