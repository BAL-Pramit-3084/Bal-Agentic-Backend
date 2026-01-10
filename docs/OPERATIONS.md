# Operations Guide

Quick reference for operating the BAL Dashboard System in production.

---

## Quick Commands

### Start/Stop
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps
```

### Logs
```bash
# Live logs (follow mode)
docker-compose logs -f bal-dashboard

# Last 100 lines
docker-compose logs --tail=100 bal-dashboard

# Search for errors
docker-compose logs bal-dashboard 2>&1 | grep -i error

# View log files directly
cat logs/app.log | tail -100
cat logs/error.log
```

### Health Check
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' bal-dashboard

# Manual health check
curl http://localhost:5100/health
```

---

## Deployment

### Deploy New Version
```bash
# Windows
scripts\deploy.bat

# Linux/Mac
./scripts/deploy.sh

# Force rebuild (clears cache)
./scripts/deploy.sh --rebuild
```

### Rollback
```bash
./scripts/deploy.sh --rollback
```

### Update Code Only (No Rebuild)
```bash
docker-compose down
git pull
docker-compose up -d
```

---

## Monitoring

### Check Application Status
```bash
curl http://localhost:5100/health
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "components": {
    "database": "connected",
    "claude_api": "available",
    "jwt_auth": "enabled",
    "departments": 4
  }
}
```

### Check Resource Usage
```bash
docker stats bal-dashboard
```

---

## Troubleshooting

### Container Won't Start

1. Check logs:
   ```bash
   docker-compose logs bal-dashboard
   ```

2. Check .env file exists:
   ```bash
   ls -la .env
   ```

3. Verify database connectivity:
   ```bash
   docker exec -it bal-dashboard python -c "from core.mcp_server import MCPServer; m=MCPServer(); print(m.discover())"
   ```

### Database Connection Failed

1. Check MySQL host is reachable from container:
   ```bash
   docker exec -it bal-dashboard ping -c 3 <MYSQL_HOST>
   ```

2. Verify credentials in .env

3. Check if MySQL allows remote connections

### Claude API Errors

1. Check API key is valid in .env
2. Check API quota/limits
3. View specific error in logs:
   ```bash
   docker-compose logs bal-dashboard 2>&1 | grep -i claude
   ```

### Dashboard Generation Failed

1. Check specific error:
   ```bash
   docker-compose logs --tail=50 bal-dashboard | grep -i error
   ```

2. Verify templates exist:
   ```bash
   docker exec -it bal-dashboard ls -la templates/
   ```

3. Check disk space for generated dashboards:
   ```bash
   df -h
   du -sh generated_dashboards/
   ```

---

## Maintenance

### Clean Up Old Dashboards
```bash
# Run cleanup script (removes dashboards older than 15 days)
docker exec -it bal-dashboard python cleanup_dashbaord.py
```

### Backup Logs
```bash
# Create backup with timestamp
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### Update Dependencies
```bash
# Update requirements.txt, then:
docker-compose build --no-cache
docker-compose up -d
```

---

## Adding New Department

1. Create department folder:
   ```
   departments/new_dept/
   ├── __init__.py
   ├── formatter.py
   ├── template_engine.py
   └── claude_analyzer.py
   ```

2. Add template:
   ```
   templates/new_dept_dashboard.html
   ```

3. Register in `dashboards/departments_config.py`

4. Add handler in `app_main.py`

5. Update imports in `app_main.py`

6. Test locally, then deploy:
   ```bash
   ./scripts/deploy.sh
   ```

---

## Important Files

| File | Purpose |
|------|---------|
| `.env` | Configuration (secrets) |
| `VERSION` | Current version number |
| `CHANGELOG.md` | Version history |
| `logs/app.log` | Application logs |
| `logs/error.log` | Error logs only |
| `generated_dashboards/` | Generated HTML files |

---

## Emergency Contacts

- **Application Issues**: [Your team contact]
- **Database Issues**: [DBA contact]
- **Infrastructure**: [IT contact]
