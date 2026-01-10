# 📋 BAL-Agentic-Backend Platform - Quick Reference Card

## 🚀 Deploy (First Time)

```bash
# Linux/Mac
./deploy.sh

# Windows
.\deploy.ps1
```

---

## 🔄 Daily Operations

### Start/Stop

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart (after adding department)
docker-compose restart bal-agentic-backend
```

### Monitor

```bash
# Health check
curl http://localhost:5100/health

# View logs
docker-compose logs -f bal-agentic-backend

# Resource usage
docker stats bal-agentic-backend-platform

# Container status
docker-compose ps
```

---

## 🏢 Add New Department

### Quick Method

```bash
# 1. Create folder structure
mkdir -p departments/newdept
cd departments/newdept

# 2. Create files (copy from existing dept)
touch __init__.py
touch formatter.py
touch claude_analyzer.py
touch template_engine.py

# 3. Update config
nano dashboards/departments_config.py
# Add DEPARTMENT_NEWDEPT definition

# 4. Create template
cp templates/furnace_dashboard.html templates/newdept_dashboard.html

# 5. Restart (NO REBUILD NEEDED!)
docker-compose restart bal-agentic-backend
```

---

## 🔧 Common Issues

### Container won't start

```bash
# Check logs
docker-compose logs bal-agentic-backend

# Common fixes:
docker-compose down
docker-compose up -d --force-recreate
```

### New department not showing

```bash
# 1. Verify config
python -c "from dashboards.departments_config import ALL_DEPARTMENTS; print(ALL_DEPARTMENTS.keys())"

# 2. Restart
docker-compose restart bal-agentic-backend

# 3. Check logs
docker-compose logs bal-agentic-backend | grep -i newdept
```

### Permission errors

```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) .

# Or run as sudo
sudo docker-compose up -d
```

---

## 📊 Testing

```bash
# Health
curl http://localhost:5100/health

# Departments list
curl http://localhost:5100/api/v1/departments

# Generate dashboard
curl "http://localhost:5100/api/v1/dashboard/furnace?date=2024-12-01" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🛟 Emergency Commands

```bash
# Complete reset
docker-compose down
docker system prune -a -f
docker-compose up --build -d

# View last 100 logs
docker-compose logs --tail=100 bal-agentic-backend

# Access container shell
docker exec -it bal-agentic-backend-platform /bin/bash

# Export logs to file
docker-compose logs bal-agentic-backend > debug.log
```

---

## 📈 Resource Tuning

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: "4.0" # Increase for more users
      memory: 8G # Increase for heavy loads
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

---

## 🔐 Security Checklist

- [ ] `.env` file has strong secrets
- [ ] `.env` is in `.gitignore`
- [ ] Database passwords are strong
- [ ] JWT secret is random and long
- [ ] Container is running as non-root
- [ ] Ports are firewalled (only 5100 open)

---

## 📞 Quick Contacts

- **Container Name:** `bal-agentic-backend-platform`
- **Port:** `5100`
- **Health Endpoint:** `http://localhost:5100/health`
- **API Docs:** See `DEPLOYMENT.md`

---

## 💡 Pro Tips

1. **Hot-reload works for:**

   - New departments (just restart)
   - Template changes (just restart)
   - Config updates (just restart)

2. **Rebuild only needed for:**

   - Python dependency changes
   - Dockerfile changes
   - Base image updates

3. **Always check logs first:**

   ```bash
   docker-compose logs bal-agentic-backend | tail -50
   ```

4. **Backup regularly:**
   ```bash
   ./manage.sh backup
   ```

---

**Keep this card handy! 📌**
