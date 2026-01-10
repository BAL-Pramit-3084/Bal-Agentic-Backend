#!/bin/bash
# =============================================================================
# BAL-AGENTIC-BACKEND PLATFORM - MANAGEMENT SCRIPT
# =============================================================================
# Quick access to common operations
# Usage: ./manage.sh [command]
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

CONTAINER_NAME="bal-agentic-backend-platform"

# Show usage
show_usage() {
    echo -e "${CYAN}=============================================================================${NC}"
    echo -e "${CYAN}BAL-Agentic-Backend Platform - Management Commands${NC}"
    echo -e "${CYAN}=============================================================================${NC}"
    echo ""
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Available commands:"
    echo ""
    echo -e "${YELLOW}Deployment:${NC}"
    echo "  start          - Start the platform"
    echo "  stop           - Stop the platform"
    echo "  restart        - Restart the platform"
    echo "  rebuild        - Rebuild and restart"
    echo "  deploy         - Full deployment (build + start)"
    echo ""
    echo -e "${YELLOW}Monitoring:${NC}"
    echo "  status         - Check container status"
    echo "  health         - Check service health"
    echo "  logs           - View logs (real-time)"
    echo "  logs-tail      - View last 100 log lines"
    echo "  stats          - View resource usage"
    echo ""
    echo -e "${YELLOW}Maintenance:${NC}"
    echo "  shell          - Open shell inside container"
    echo "  clean          - Remove old containers and images"
    echo "  backup         - Backup generated dashboards and logs"
    echo ""
    echo -e "${YELLOW}Departments:${NC}"
    echo "  list-deps      - List all departments"
    echo "  add-dept       - Add new department (interactive)"
    echo ""
    echo "Examples:"
    echo "  ./manage.sh start"
    echo "  ./manage.sh logs"
    echo "  ./manage.sh health"
    echo ""
}

# Check if Docker is running
check_docker() {
    if ! docker ps &> /dev/null; then
        echo -e "${RED}ERROR: Docker daemon is not running${NC}"
        exit 1
    fi
}

# Start containers
cmd_start() {
    echo -e "${YELLOW}Starting BAL-Agentic-Backend platform...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✓ Platform started${NC}"
    cmd_status
}

# Stop containers
cmd_stop() {
    echo -e "${YELLOW}Stopping BAL-Agentic-Backend platform...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Platform stopped${NC}"
}

# Restart containers
cmd_restart() {
    echo -e "${YELLOW}Restarting BAL-Agentic-Backend platform...${NC}"
    docker-compose restart
    echo -e "${GREEN}✓ Platform restarted${NC}"
    cmd_health
}

# Rebuild and restart
cmd_rebuild() {
    echo -e "${YELLOW}Rebuilding BAL-Agentic-Backend platform...${NC}"
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo -e "${GREEN}✓ Platform rebuilt and started${NC}"
    cmd_health
}

# Full deployment
cmd_deploy() {
    ./deploy.sh
}

# Check status
cmd_status() {
    echo -e "${YELLOW}Container Status:${NC}"
    docker-compose ps
}

# Health check
cmd_health() {
    echo -e "${YELLOW}Checking service health...${NC}"

    if curl -f -s http://localhost:5100/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is healthy${NC}"
        echo ""
        echo "Response:"
        curl -s http://localhost:5100/health | python -m json.tool 2>/dev/null || curl -s http://localhost:5100/health
    else
        echo -e "${RED}✗ Service is not responding${NC}"
        echo "Check logs with: ./manage.sh logs"
    fi
}

# View logs
cmd_logs() {
    echo -e "${YELLOW}Viewing logs (Press Ctrl+C to exit)...${NC}"
    docker-compose logs -f bal-agentic-backend
}

# View log tail
cmd_logs_tail() {
    echo -e "${YELLOW}Last 100 log lines:${NC}"
    docker-compose logs --tail=100 bal-agentic-backend
}

# View resource stats
cmd_stats() {
    echo -e "${YELLOW}Resource Usage:${NC}"
    docker stats $CONTAINER_NAME --no-stream
}

# Open shell
cmd_shell() {
    echo -e "${YELLOW}Opening shell in container...${NC}"
    docker exec -it $CONTAINER_NAME /bin/bash
}

# Clean up
cmd_clean() {
    echo -e "${YELLOW}Cleaning up old containers and images...${NC}"
    docker-compose down
    docker system prune -f
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Backup
cmd_backup() {
    BACKUP_DIR="backups/backup_$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}Creating backup in $BACKUP_DIR...${NC}"

    mkdir -p "$BACKUP_DIR"

    # Backup generated dashboards
    if [ -d "generated_dashboards" ]; then
        cp -r generated_dashboards "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backed up generated dashboards${NC}"
    fi

    # Backup logs
    if [ -d "logs" ]; then
        cp -r logs "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backed up logs${NC}"
    fi

    # Backup config
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backed up configuration${NC}"
    fi

    echo -e "${GREEN}✓ Backup complete: $BACKUP_DIR${NC}"
}

# List departments
cmd_list_deps() {
    echo -e "${YELLOW}Installed Departments:${NC}"
    echo ""

    if [ -d "departments" ]; then
        for dept in departments/*/; do
            if [ -d "$dept" ]; then
                dept_name=$(basename "$dept")
                echo -e "  📁 ${GREEN}$dept_name${NC}"

                # Check for required files
                if [ -f "$dept/__init__.py" ]; then echo -e "     ✓ __init__.py"; fi
                if [ -f "$dept/formatter.py" ]; then echo -e "     ✓ formatter.py"; fi
                if [ -f "$dept/claude_analyzer.py" ]; then echo -e "     ✓ claude_analyzer.py"; fi
                if [ -f "$dept/template_engine.py" ]; then echo -e "     ✓ template_engine.py"; fi
                echo ""
            fi
        done
    else
        echo -e "${RED}No departments directory found${NC}"
    fi
}

# Add new department (interactive)
cmd_add_dept() {
    echo -e "${CYAN}=============================================================================${NC}"
    echo -e "${CYAN}Add New Department${NC}"
    echo -e "${CYAN}=============================================================================${NC}"
    echo ""

    read -p "Enter department ID (lowercase, e.g., 'finance'): " dept_id
    read -p "Enter department name (e.g., 'Finance'): " dept_name

    DEPT_DIR="departments/$dept_id"

    if [ -d "$DEPT_DIR" ]; then
        echo -e "${RED}ERROR: Department '$dept_id' already exists${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Creating department structure...${NC}"

    mkdir -p "$DEPT_DIR"

    # Create __init__.py
    cat > "$DEPT_DIR/__init__.py" <<EOF
"""
$dept_name Department Module
"""
from .formatter import ${dept_name}DataProcessor
from .template_engine import ${dept_name}TemplateEngine
from .claude_analyzer import ${dept_name}ClaudeInsightsGenerator

__all__ = [
    '${dept_name}DataProcessor',
    '${dept_name}TemplateEngine',
    '${dept_name}ClaudeInsightsGenerator'
]
EOF

    echo -e "${GREEN}✓ Created $DEPT_DIR/__init__.py${NC}"
    echo -e "${YELLOW}✎ TODO: Create formatter.py, template_engine.py, claude_analyzer.py${NC}"
    echo -e "${YELLOW}✎ TODO: Update dashboards/departments_config.py${NC}"
    echo -e "${YELLOW}✎ TODO: Create template in templates/${dept_id}_dashboard.html${NC}"
    echo ""
    echo -e "${GREEN}✓ Department structure created${NC}"
}

# =============================================================================
# MAIN
# =============================================================================
check_docker

if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

case "$1" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    rebuild)
        cmd_rebuild
        ;;
    deploy)
        cmd_deploy
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    logs)
        cmd_logs
        ;;
    logs-tail)
        cmd_logs_tail
        ;;
    stats)
        cmd_stats
        ;;
    shell)
        cmd_shell
        ;;
    clean)
        cmd_clean
        ;;
    backup)
        cmd_backup
        ;;
    list-deps)
        cmd_list_deps
        ;;
    add-dept)
        cmd_add_dept
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac