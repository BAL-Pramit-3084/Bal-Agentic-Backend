#!/bin/bash
# =============================================================================
# BALASORE ALLOYS DASHBOARD - DEPLOYMENT SCRIPT
# =============================================================================
#
# Usage:
#   ./scripts/deploy.sh              # Build and deploy
#   ./scripts/deploy.sh --rebuild    # Force rebuild
#   ./scripts/deploy.sh --rollback   # Rollback to previous version
#
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="bal-dashboard"
IMAGE_NAME="bal-dashboard"
COMPOSE_FILE="docker-compose.yml"

# Get version from VERSION file
VERSION=$(cat VERSION 2>/dev/null || echo "unknown")

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  BAL DASHBOARD DEPLOYMENT v${VERSION}${NC}"
echo -e "${GREEN}======================================${NC}"

# Parse arguments
REBUILD=false
ROLLBACK=false

for arg in "$@"; do
    case $arg in
        --rebuild)
            REBUILD=true
            ;;
        --rollback)
            ROLLBACK=true
            ;;
    esac
done

# Rollback function
if [ "$ROLLBACK" = true ]; then
    echo -e "${YELLOW}Rolling back to previous version...${NC}"
    docker-compose down
    docker image tag ${IMAGE_NAME}:previous ${IMAGE_NAME}:latest 2>/dev/null || {
        echo -e "${RED}No previous version found to rollback!${NC}"
        exit 1
    }
    docker-compose up -d
    echo -e "${GREEN}Rollback complete!${NC}"
    exit 0
fi

# Pre-deployment checks
echo -e "\n${YELLOW}[1/5] Pre-deployment checks...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Copy .env.example to .env and configure it."
    exit 1
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ All checks passed${NC}"

# Backup current image
echo -e "\n${YELLOW}[2/5] Backing up current image...${NC}"
docker image tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:previous 2>/dev/null || echo "  No previous image to backup"
echo -e "${GREEN}  ✓ Backup complete${NC}"

# Build new image
echo -e "\n${YELLOW}[3/5] Building new image...${NC}"

if [ "$REBUILD" = true ]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

# Tag with version
docker tag ${IMAGE_NAME}:latest ${IMAGE_NAME}:${VERSION}
echo -e "${GREEN}  ✓ Build complete (v${VERSION})${NC}"

# Stop old container
echo -e "\n${YELLOW}[4/5] Stopping old container...${NC}"
docker-compose down || true
echo -e "${GREEN}  ✓ Old container stopped${NC}"

# Start new container
echo -e "\n${YELLOW}[5/5] Starting new container...${NC}"
docker-compose up -d

# Wait for health check
echo -e "\n${YELLOW}Waiting for health check...${NC}"
sleep 5

# Check if container is healthy
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' ${APP_NAME} 2>/dev/null || echo "unknown")

if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}  ✓ Container is healthy!${NC}"
else
    echo -e "${YELLOW}  ! Health status: ${HEALTH}${NC}"
    echo "  Checking logs..."
    docker-compose logs --tail=20
fi

# Final status
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}  DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "  Version: ${VERSION}"
echo -e "  Container: ${APP_NAME}"
echo -e "  URL: http://localhost:5100"
echo -e ""
echo -e "  Commands:"
echo -e "    Logs:    docker-compose logs -f"
echo -e "    Stop:    docker-compose down"
echo -e "    Restart: docker-compose restart"
echo -e "    Shell:   docker exec -it ${APP_NAME} bash"
echo -e "${GREEN}======================================${NC}"
