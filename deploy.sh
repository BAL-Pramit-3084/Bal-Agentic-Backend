#!/bin/bash
# =============================================================================
# BAL-AGENTIC-BACKEND - DEPLOYMENT SCRIPT (Linux/Mac)
# =============================================================================
# Version: 3.0.0
# Usage: ./deploy.sh
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}BAL-AGENTIC-BACKEND - DEPLOYMENT SCRIPT${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""

# =============================================================================
# STEP 1: Pre-flight Checks
# =============================================================================
echo -e "${YELLOW}[1/6] Running pre-flight checks...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed${NC}"
    echo -e "${RED}Please install Docker from https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed${NC}"
    echo -e "${RED}Please install Docker Compose from https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}ERROR: Docker daemon is not running${NC}"
    echo -e "${RED}Please start Docker service${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Docker is running${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
        echo -e "${YELLOW}Then run this script again${NC}"
        exit 0
    else
        echo -e "${RED}ERROR: Neither .env nor .env.example found${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}  ✓ .env file found${NC}"

# Check required directories
REQUIRED_DIRS=("departments" "templates" "addons" "core" "config_modules")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}ERROR: Required directory not found: $dir${NC}"
        exit 1
    fi
done

echo -e "${GREEN}  ✓ All required directories present${NC}"
echo ""

# =============================================================================
# STEP 2: Create directories if they don't exist
# =============================================================================
echo -e "${YELLOW}[2/6] Creating directories...${NC}"

DIRS=(
    "generated_dashboards"
    "logs"
    "config_modules/generated_dashboards"
    "config_modules/logs"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}  ✓ Created: $dir${NC}"
    else
        echo -e "${GRAY}  ✓ Exists: $dir${NC}"
    fi
done

echo ""

# =============================================================================
# STEP 3: Stop existing containers
# =============================================================================
echo -e "${YELLOW}[3/6] Stopping existing containers...${NC}"

docker-compose down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Containers stopped successfully${NC}"
else
    echo -e "${GRAY}  ℹ No containers to stop (first deployment?)${NC}"
fi

echo ""

# =============================================================================
# STEP 4: Build Docker image
# =============================================================================
echo -e "${YELLOW}[4/6] Building Docker image...${NC}"
echo -e "${GRAY}  This may take a few minutes on first build...${NC}"

docker-compose build --no-cache
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Build completed successfully${NC}"
echo ""

# =============================================================================
# STEP 5: Start containers
# =============================================================================
echo -e "${YELLOW}[5/6] Starting BAL-Agentic-Backend...${NC}"

docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to start containers${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ Containers started successfully${NC}"
echo ""

# =============================================================================
# STEP 6: Health check
# =============================================================================
echo -e "${YELLOW}[6/6] Waiting for services to be healthy...${NC}"

MAX_RETRIES=30
RETRY_COUNT=0
HEALTHY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT + 1))

    if curl -f -s http://localhost:5100/health > /dev/null 2>&1; then
        HEALTHY=true
        break
    else
        echo -e "${GRAY}  Attempt $RETRY_COUNT/$MAX_RETRIES - Service not ready yet...${NC}"
    fi
done

echo ""

if [ "$HEALTHY" = true ]; then
    echo -e "${GREEN}=============================================================================${NC}"
    echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL!${NC}"
    echo -e "${GREEN}=============================================================================${NC}"
    echo ""
    echo -e "${CYAN}Agentic AI platform is running on: http://localhost:5100${NC}"
    echo ""
    echo -e "${YELLOW}Available endpoints:${NC}"
    echo -e "  Health Check:  ${NC}http://localhost:5100/health"
    echo -e "  Departments:   ${NC}http://localhost:5100/api/v1/departments"
    echo -e "  Dashboard:     ${NC}http://localhost:5100/api/v1/dashboard/<dept_id>?date=YYYY-MM-DD"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo -e "  View logs:     ${NC}docker-compose logs -f bal-agentic-backend"
    echo -e "  Stop service:  ${NC}docker-compose down"
    echo -e "  Restart:       ${NC}docker-compose restart bal-agentic-backend"
    echo -e "  Status:        ${NC}docker-compose ps"
    echo ""
    echo -e "${YELLOW}Container status:${NC}"
    docker-compose ps
else
    echo -e "${RED}=============================================================================${NC}"
    echo -e "${RED}⚠ WARNING: Service started but health check failed${NC}"
    echo -e "${RED}=============================================================================${NC}"
    echo ""
    echo -e "${YELLOW}Check logs with: docker-compose logs bal-agentic-backend${NC}"
    echo ""
    docker-compose logs --tail=50 bal-agentic-backend
fi

echo ""
echo -e "${CYAN}=============================================================================${NC}"