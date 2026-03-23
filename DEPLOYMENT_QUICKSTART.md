# TaskForge - Deployment Quick Reference

## For New Deployments

### Step 1: Install Docker
- Windows/Mac: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Linux: `curl -fsSL https://get.docker.com | sh`

### Step 2: Get Files
- Receive TaskForge folder + `schema.sql` from administrator

### Step 3: Deploy
```bash
cd taskforge
docker-compose up -d
docker exec -i taskforge-db psql -U taskforge -d taskforge < schema.sql
```

### Step 4: Access
- URL: `http://localhost:5000`
- Login: `admin@taskforge.local` / `changeme`

## Common Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f web

# Restart
docker-compose restart web

# Backup
docker exec taskforge-db pg_dump -U taskforge taskforge > backup_$(date +%Y%m%d).sql
```

## Change Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Change 8080 to desired port
```

Then: `docker-compose up -d`

## Troubleshooting

**Port already in use:**
```bash
docker-compose down
# Change port in docker-compose.yml
docker-compose up -d
```

**Database error:**
```bash
docker-compose restart db
docker-compose logs db
```

**Reset everything:**
```bash
docker-compose down -v
docker-compose up -d
# Re-import schema.sql
```

## Support

Contact your administrator for:
- Database schema file (`schema.sql`)
- Production SECRET_KEY
- Custom configuration
