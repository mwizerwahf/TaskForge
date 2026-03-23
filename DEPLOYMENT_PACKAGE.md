# Deployment Package Checklist

## Files to Send

### Required Files
- [ ] Entire `taskforge/` folder (application code)
- [ ] `schema.sql` (database schema - send separately/securely)

### Documentation Included
- [ ] `README.md` - Overview and features
- [ ] `DOCKER_DEPLOYMENT.md` - Detailed Docker instructions
- [ ] `DEPLOYMENT_QUICKSTART.md` - Quick reference card

### Docker Files Included
- [ ] `Dockerfile` - Container definition
- [ ] `docker-compose.yml` - Service orchestration
- [ ] `.dockerignore` - Build optimization
- [ ] `.env.docker` - Environment template

### Helper Scripts
- [ ] `generate_secret_key.py` - Security key generator
- [ ] `init_db.py` - Database initialization (alternative to schema.sql)

## Pre-Deployment Instructions for Recipient

1. **Install Docker**
   - Download from: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version` and `docker-compose --version`

2. **Prepare Files**
   - Extract taskforge folder
   - Place `schema.sql` in the same directory

3. **Deploy**
   ```bash
   cd taskforge
   docker-compose up -d
   docker exec -i taskforge-db psql -U taskforge -d taskforge < schema.sql
   ```

4. **Access Application**
   - URL: http://localhost:5000
   - Login: admin@taskforge.local / changeme
   - Change password immediately after first login

## Security Recommendations

- [ ] Generate new SECRET_KEY: `python generate_secret_key.py`
- [ ] Change default admin password after first login
- [ ] Update database password in `docker-compose.yml`
- [ ] Use HTTPS in production (nginx reverse proxy)
- [ ] Set up regular database backups

## Support Contact

Provide your contact information for:
- Database schema questions
- Configuration assistance
- Troubleshooting support
- Feature requests

## Optional: Production Enhancements

- [ ] Set up nginx reverse proxy for HTTPS
- [ ] Configure automated backups
- [ ] Set up monitoring/logging
- [ ] Configure firewall rules
- [ ] Set resource limits in docker-compose.yml

## Verification Steps

After deployment, verify:
- [ ] Application accessible at http://localhost:5000
- [ ] Can login with default credentials
- [ ] Can create a test task
- [ ] Can upload a file attachment
- [ ] Real-time updates working (open two browsers)
- [ ] Can generate a PDF report

## Backup Instructions

```bash
# Database backup
docker exec taskforge-db pg_dump -U taskforge taskforge > backup.sql

# Uploads backup
docker cp taskforge-app:/app/app/uploads ./uploads_backup
```

## Rollback Plan

If issues occur:
```bash
docker-compose down -v
# Fix configuration
docker-compose up -d
# Re-import schema
```
