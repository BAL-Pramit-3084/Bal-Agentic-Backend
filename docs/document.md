# 🚀 BAL-Agentic-Backend Platform - Docker Deployment Guide

**Version:** 3.0.0
**Architecture:** Modular Monolith with Plugin System
**Target:** Windows Server / Linux with Docker Engine

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Deployment Steps](#deployment-steps)
4. [Adding New Departments](#adding-new-departments)
5. [Management Commands](#management-commands)
6. [Troubleshooting](#troubleshooting)
7. [Production Considerations](#production-considerations)

---

## ⚡ Quick Start

```bash
# 1. Clone/copy your project to the server

# 2. Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your database credentials and API keys

# 3. Deploy!
# For Linux/Mac:
chmod +x deploy.sh
./deploy.sh

# For Windows (PowerShell):
.\deploy.ps1
```

That's it! Your platform will be running on `http://localhost:5100`

---

## 📦 Prerequisites

### Required Software

1. **Docker Engine** (v20.10+)

   - Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: `sudo apt-get install docker.io docker-compose`

2. **Docker Compose** (v2.0+)
   - Usually included with Docker Desktop
   - Linux: `sudo apt-get install docker-compose-plugin`

### Required Files

Your project should have this structure:

```
BAL-Agentic-Backend/
├── .env                    # Configuration (CREATE THIS!)
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── app_main.py            # Flask application
├── departments/           # Department modules (hot-reload)
├── templates/             # HTML templates (hot-reload)
├── addons/                # Plugins (hot-reload)
├── core/                  # Core services
├── config_modules/        # Configuration
└── ...
```

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your actual credentials
nano .env  # or use notepad on Windows
```

**Required environment variables:**

```env
# Database
DB_HOST=your-mysql-server
DB_PORT=3306
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME_1=balcorpdb
DB_NAME_2=balpms

# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxx

# JWT (coordinate with frontend team)
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Flask
FLASK_ENV=production
DEBUG_MODE=false
PORT=5100
```

### Step 2: Deploy

**Option A: Using Deploy Script (Recommended)**

```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows PowerShell
.\deploy.ps1
```

**Option B: Manual Deployment**

```bash
# Create directories
mkdir -p generated_dashboards logs

# Build image
docker-compose build --no-cache

# Start containers
docker-compose up -d

# Check health
curl http://localhost:5100/health
```

### Step 3: Verify Deployment

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f bal-agentic-backend

# Test health endpoint
curl http://localhost:5100/health

# Test departments endpoint
curl http://localhost:5100/api/v1/departments
```

---

## 🏢 Adding New Departments

### Method 1: Using Management Script (Linux/Mac)

```bash
chmod +x manage.sh
./manage.sh add-dept

# Follow interactive prompts
```

### Method 2: Manual Creation

1. **Create department folder:**

```bash
mkdir -p departments/finance
cd departments/finance
```

2. **Create required files:**

```
departments/finance/
├── __init__.py
├── formatter.py              # Data processing
├── claude_analyzer.py        # AI insights
└── template_engine.py        # Template handling
```

3. **Update configuration:**

Edit `dashboards/departments_config.py`:

```python
DEPARTMENT_FINANCE = DepartmentDefinition(
    id="finance",
    name="Finance",
    icon="💰",
    description="Financial metrics and reporting",
    enabled=True,
    tables=[
        TableDefinition(
            name="finance_transactions",
            structure_type="normalized",
            primary_date_column="TRANSACTION_DATE",
            columns=["..."]
        )
    ],
    template_file="finance_dashboard.html",
    func_plant_filter=None,
    data_processor="finance"
)

# Add to registry
ALL_DEPARTMENTS = {
    "env": DEPARTMENT_ENV,
    "furnace": DEPARTMENT_FURNACE,
    "qc": DEPARTMENT_QC,
    "scm": DEPARTMENT_SCM,
    "crm": DEPARTMENT_CRM,
    "finance": DEPARTMENT_FINANCE,  # ← Add this
}
```

4. **Create template:**

```bash
cp templates/furnace_dashboard.html templates/finance_dashboard.html
# Edit template as needed
```

5. **Restart container (no rebuild needed!):**

```bash
docker-compose restart bal-agentic-backend
```

**That's it!** The new department is now available via the API.

---

## 🛠️ Management Commands

### Using manage.sh (Linux/Mac)

```bash
# Make executable
chmod +x manage.sh

# View all commands
./manage.sh

# Common operations
./manage.sh start          # Start platform
./manage.sh stop           # Stop platform
./manage.sh restart        # Restart (picks up new departments)
./manage.sh logs           # View real-time logs
./manage.sh health         # Check service health
./manage.sh status         # Container status
./manage.sh stats          # Resource usage
./manage.sh shell          # Open shell in container
./manage.sh backup         # Backup dashboards & logs
./manage.sh list-deps      # List all departments
```

### Using Docker Compose Directly

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart bal-agentic-backend

# View logs
docker-compose logs -f bal-agentic-backend

# Check status
docker-compose ps

# View resource usage
docker stats bal-agentic-backend-platform
```

---

## 🔧 Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs bal-agentic-backend

# Common causes:
# 1. Missing .env file
# 2. Wrong database credentials
# 3. Port 5100 already in use
```

**Solution:**

```bash
# Verify .env exists
ls -la .env

# Check port usage
netstat -an | grep 5100  # Linux
netstat -an | findstr 5100  # Windows

# Restart Docker daemon
sudo systemctl restart docker  # Linux
# Restart Docker Desktop on Windows
```

### Issue: Health check failing

```bash
# Test health endpoint manually
curl http://localhost:5100/health

# Check container is running
docker ps | grep bal-agentic-backend

# View detailed logs
docker-compose logs --tail=100 bal-agentic-backend
```

### Issue: New department not appearing

```bash
# 1. Verify files exist
ls -la departments/your_dept/

# 2. Check configuration
python -c "from dashboards.departments_config import ALL_DEPARTMENTS; print(ALL_DEPARTMENTS.keys())"

# 3. Restart container
docker-compose restart bal-agentic-backend

# 4. Check logs for errors
docker-compose logs bal-agentic-backend | grep -i error
```

### Issue: Permission denied on Windows

```powershell
# Run PowerShell as Administrator
# Or adjust execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 🏭 Production Considerations

### Resource Allocation

Current settings in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "2.0" # Adjust based on your server
      memory: 4G # Adjust based on your server
```

**Recommendations:**

- **For 100 users:** 2 CPU cores, 4GB RAM (current)
- **For 300+ users:** 4 CPU cores, 8GB RAM
- Monitor with: `docker stats bal-agentic-backend-platform`

### Scaling

To run multiple instances:

```bash
# Edit docker-compose.yml:
# Remove 'container_name' line
# Then scale:
docker-compose up -d --scale bal-agentic-backend=3

# Add load balancer (nginx) in front
```

### Backup Strategy

**Automated backup:**

```bash
# Add to crontab (Linux)
0 2 * * * /path/to/manage.sh backup

# Or use Task Scheduler on Windows
```

**What to backup:**

- `./generated_dashboards/` - All generated dashboards
- `./logs/` - Audit trail
- `.env` - Configuration (secure this!)

### Monitoring

```bash
# Real-time logs
docker-compose logs -f bal-agentic-backend

# Resource usage
docker stats bal-agentic-backend-platform

# Container health
curl http://localhost:5100/health
```

### Security Checklist

- [ ] Strong JWT secret in `.env`
- [ ] Database credentials secured
- [ ] `.env` not committed to git
- [ ] Container running as non-root user (default)
- [ ] Regular security updates: `docker-compose pull && docker-compose up -d`

---

## 📊 API Endpoints

After deployment, these endpoints are available:

| Endpoint                      | Method | Description          |
| ----------------------------- | ------ | -------------------- |
| `/health`                     | GET    | Service health check |
| `/api/v1/departments`         | GET    | List all departments |
| `/api/v1/dashboard/<dept_id>` | GET    | Generate dashboard   |
| `/preview/<file_id>`          | GET    | Preview dashboard    |
| `/download/<file_id>`         | GET    | Download dashboard   |
| `/api/v1/chat`                | POST   | AI chatbot           |

**Example:**

```bash
# Health check
curl http://localhost:5100/health

# List departments
curl http://localhost:5100/api/v1/departments

# Generate furnace dashboard
curl "http://localhost:5100/api/v1/dashboard/furnace?date=2024-12-01" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🆘 Support

If you encounter issues:

1. **Check logs:** `docker-compose logs bal-agentic-backend`
2. **Verify configuration:** Ensure `.env` is correct
3. **Check health:** `curl http://localhost:5100/health`
4. **Restart:** `docker-compose restart bal-agentic-backend`
5. **Rebuild:** `docker-compose up --build --force-recreate`

---

## 📝 Change Log

### Version 3.0.0 (Current)

- ✅ Modular architecture with hot-reload
- ✅ One-command deployment
- ✅ Management scripts
- ✅ Production-ready configuration
- ✅ Multi-stage Docker build
- ✅ Resource limits
- ✅ Health monitoring

---

**Happy Deploying! 🚀**
