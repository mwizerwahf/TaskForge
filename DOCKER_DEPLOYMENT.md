# Docker Deployment Guide

Deploy TaskForge using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. **Clone/Copy the repository**
   ```bash
   cd taskforge
   ```

2. **Configure environment (optional)**
   ```bash
   cp .env.docker .env
   # Edit .env and set SECRET_KEY
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   
   Contact the administrator to receive the database schema file, then run:
   ```bash
   docker exec -i taskforge-db psql -U taskforge -d taskforge < schema.sql
   ```

5. **Access the application**
   
   Open browser: `http://localhost:5000`
   
   Default login: `admin@taskforge.local` / `changeme`

## Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart application
docker-compose restart web

# Rebuild after code changes
docker-compose up -d --build

# Stop and remove all data
docker-compose down -v
```

## Configuration

Edit `docker-compose.yml` to customize:

- **Port**: Change `5000:5000` to `8080:5000` for port 8080
- **Database credentials**: Update `POSTGRES_USER`, `POSTGRES_PASSWORD`
- **Environment**: Set `FLASK_ENV=development` for debug mode

## Backup

```bash
# Backup database
docker exec taskforge-db pg_dump -U taskforge taskforge > backup.sql

# Restore database
docker exec -i taskforge-db psql -U taskforge taskforge < backup.sql
```

## Troubleshooting

**Database connection failed:**
```bash
docker-compose logs db
docker-compose restart db
```

**Application not starting:**
```bash
docker-compose logs web
docker-compose restart web
```

**Reset everything:**
```bash
docker-compose down -v
docker-compose up -d
# Re-import schema
```

## Production Notes

- Change `SECRET_KEY` in `.env` or `docker-compose.yml`
- Use strong database passwords
- Configure reverse proxy (nginx) for HTTPS
- Set up regular database backups
- Monitor logs: `docker-compose logs -f`
