# TaskForge - Production Deployment Quick Start

## 🚀 Three Ways to Deploy

### Option 1: Docker (Fastest - 5 minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd taskforge

# 2. Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# 3. Create .env file
echo "SECRET_KEY=<your-generated-key>" > .env

# 4. Deploy
docker-compose up -d

# 5. Access
# http://localhost:8000
```

**Default Credentials:**
- Email: `admin@taskforge.local`
- Password: `changeme`

---

### Option 2: Automated Script (Ubuntu/Debian - 10 minutes)

```bash
# 1. Clone repository
git clone <repository-url>
cd taskforge

# 2. Make script executable
chmod +x deploy.sh

# 3. Run deployment script
sudo ./deploy.sh

# Follow the prompts
```

---

### Option 3: Manual Deployment (Full Control - 30 minutes)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed step-by-step instructions.

---

## 📋 What's Included

### Production Files Created

1. **`.env.example`** - Environment variables template
2. **`Dockerfile`** - Container configuration
3. **`docker-compose.yml`** - Multi-container setup
4. **`nginx.conf`** - Reverse proxy configuration
5. **`taskforge.service`** - Systemd service file
6. **`deploy.sh`** - Automated deployment script
7. **`DEPLOYMENT.md`** - Comprehensive deployment guide
8. **`PRODUCTION_CHECKLIST.md`** - Pre/post deployment checklist

### Key Changes for Production

✅ **PostgreSQL** instead of SQLite
✅ **Gunicorn** production server
✅ **Environment variables** for configuration
✅ **Security hardening** (secure cookies, CSRF protection)
✅ **Health check endpoint** (`/health`)
✅ **Docker support** with compose
✅ **Nginx configuration** with WebSocket support
✅ **Systemd service** for auto-restart
✅ **Logging** configuration
✅ **SSL/HTTPS** ready

---

## 🔧 Configuration

### Required Environment Variables

```bash
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets.token_hex(32)>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
UPLOAD_FOLDER=/path/to/uploads
MAX_CONTENT_LENGTH=16777216
```

### Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🗄️ Database Setup

### PostgreSQL Installation

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE taskforge_db;
CREATE USER taskforge_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE taskforge_db TO taskforge_user;
\q
```

---

## 🔒 Security Checklist

- [ ] Change default admin password
- [ ] Generate secure SECRET_KEY
- [ ] Use strong database password
- [ ] Configure SSL/HTTPS
- [ ] Enable firewall
- [ ] Set secure cookie flags
- [ ] Regular security updates

---

## 📊 Monitoring

### Check Application Status

```bash
# Systemd service
sudo systemctl status taskforge

# View logs
sudo journalctl -u taskforge -f

# Health check
curl http://localhost:8000/health
```

### Database Backup

```bash
# Manual backup
pg_dump -U taskforge_user taskforge_db > backup.sql

# Automated (add to crontab)
0 2 * * * pg_dump -U taskforge_user taskforge_db | gzip > /backups/taskforge_$(date +\%Y\%m\%d).sql.gz
```

---

## 🌐 SSL/HTTPS Setup

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d taskforge.example.com

# Auto-renewal is configured automatically
```

---

## 🐛 Troubleshooting

### Application won't start

```bash
# Check logs
sudo journalctl -u taskforge -n 50

# Verify environment
cat /var/www/taskforge/.env

# Test database connection
psql -U taskforge_user -d taskforge_db -h localhost
```

### Port already in use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Permission issues

```bash
# Fix ownership
sudo chown -R taskforge:www-data /var/www/taskforge

# Fix uploads directory
sudo chmod -R 755 /var/www/taskforge/app/uploads
```

---

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Deployment checklist
- **[README.md](README.md)** - Application documentation

---

## 🆘 Support

- **Issues**: [GitHub Issues](repository-url/issues)
- **Email**: support@taskforge.local
- **Documentation**: [docs-url]

---

## 📝 Post-Deployment

1. ✅ Access application at your domain
2. ✅ Login with default credentials
3. ✅ **Change admin password immediately**
4. ✅ Create additional users
5. ✅ Configure SSL certificate
6. ✅ Setup automated backups
7. ✅ Configure monitoring
8. ✅ Review security settings

---

## 🎯 Quick Commands Reference

```bash
# Start application
sudo systemctl start taskforge

# Stop application
sudo systemctl stop taskforge

# Restart application
sudo systemctl restart taskforge

# View logs
sudo journalctl -u taskforge -f

# Reload Nginx
sudo systemctl reload nginx

# Database backup
pg_dump -U taskforge_user taskforge_db > backup.sql

# Update application
cd /var/www/taskforge
git pull
sudo systemctl restart taskforge
```

---

**Ready to deploy? Choose your deployment method above and get started!** 🚀
