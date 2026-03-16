# TaskForge Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Server Deployment](#production-server-deployment)
5. [Database Setup](#database-setup)
6. [SSL/HTTPS Configuration](#ssl-https-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python**: 3.9 or higher
- **PostgreSQL**: 13 or higher
- **RAM**: Minimum 1GB (2GB+ recommended)
- **Storage**: 10GB+ available

### Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd taskforge
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your settings
```

### 5. Setup PostgreSQL (Local)
```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE taskforge_db;
CREATE USER taskforge_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE taskforge_db TO taskforge_user;
\q
```

### 6. Initialize Database
```bash
python app.py
# Database tables will be created automatically
```

### 7. Run Development Server
```bash
python app.py
# Access at http://localhost:5000
```

**Default Admin Credentials:**
- Email: `admin@taskforge.local`
- Password: `changeme`

⚠️ **Change immediately after first login!**

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# 1. Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Create .env file
echo "SECRET_KEY=<your-generated-key>" > .env

# 3. Build and run
docker-compose up -d

# 4. Check logs
docker-compose logs -f web

# 5. Access application
# http://localhost:8000
```

### Docker Commands
```bash
# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Access database
docker-compose exec db psql -U taskforge_user -d taskforge_db

# Backup database
docker-compose exec db pg_dump -U taskforge_user taskforge_db > backup.sql
```

---

## Production Server Deployment

### Step 1: Server Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash taskforge
sudo usermod -aG www-data taskforge

# Create application directory
sudo mkdir -p /var/www/taskforge
sudo chown taskforge:www-data /var/www/taskforge
```

### Step 2: Deploy Application

```bash
# Switch to application user
sudo su - taskforge

# Clone repository
cd /var/www/taskforge
git clone <repository-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

**Production .env Configuration:**
```bash
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets.token_hex(32)>
DATABASE_URL=postgresql://taskforge_user:secure_password@localhost:5432/taskforge_db
UPLOAD_FOLDER=/var/www/taskforge/app/uploads
MAX_CONTENT_LENGTH=16777216
```

### Step 4: Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql

CREATE DATABASE taskforge_db;
CREATE USER taskforge_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE taskforge_db TO taskforge_user;

# Enable required extensions (if needed)
\c taskforge_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### Step 5: Initialize Application

```bash
# Create uploads directory
mkdir -p /var/www/taskforge/app/uploads
chmod 755 /var/www/taskforge/app/uploads

# Initialize database
source venv/bin/activate
python app.py
# Press Ctrl+C after database is initialized
```

### Step 6: Setup Systemd Service

```bash
# Create log directory
sudo mkdir -p /var/log/taskforge
sudo chown taskforge:www-data /var/log/taskforge

# Copy service file
sudo cp taskforge.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable taskforge
sudo systemctl start taskforge

# Check status
sudo systemctl status taskforge
```

### Step 7: Configure Nginx

```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/taskforge

# Edit domain name
sudo nano /etc/nginx/sites-available/taskforge
# Change: server_name taskforge.example.com;

# Enable site
sudo ln -s /etc/nginx/sites-available/taskforge /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 8: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

---

## Database Setup

### PostgreSQL Configuration

**Edit PostgreSQL config for production:**
```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

**Recommended settings:**
```conf
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Database Backup

**Automated backup script:**
```bash
#!/bin/bash
# /var/www/taskforge/backup.sh

BACKUP_DIR="/var/backups/taskforge"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="taskforge_db"
DB_USER="taskforge_user"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/taskforge_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "taskforge_*.sql.gz" -mtime +7 -delete

echo "Backup completed: taskforge_$DATE.sql.gz"
```

**Setup cron job:**
```bash
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /var/www/taskforge/backup.sh >> /var/log/taskforge/backup.log 2>&1
```

---

## SSL/HTTPS Configuration

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d taskforge.example.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Certificate

If using custom SSL certificate:

```bash
# Copy certificates
sudo cp fullchain.pem /etc/ssl/certs/taskforge.crt
sudo cp privkey.pem /etc/ssl/private/taskforge.key

# Set permissions
sudo chmod 644 /etc/ssl/certs/taskforge.crt
sudo chmod 600 /etc/ssl/private/taskforge.key

# Update nginx.conf with SSL configuration
sudo nano /etc/nginx/sites-available/taskforge
# Uncomment HTTPS server block and update paths
```

---

## Monitoring & Maintenance

### Application Logs

```bash
# View application logs
sudo journalctl -u taskforge -f

# View nginx access logs
sudo tail -f /var/log/nginx/access.log

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# View application logs
sudo tail -f /var/log/taskforge/error.log
```

### Health Checks

**Add health check endpoint** (already in code):
```python
# app/__init__.py or routes
@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except:
        return {'status': 'unhealthy', 'database': 'disconnected'}, 503
```

**Monitor with curl:**
```bash
curl http://localhost:8000/health
```

### Performance Monitoring

**Install monitoring tools:**
```bash
# Install htop for system monitoring
sudo apt install htop

# Install pg_stat_statements for PostgreSQL
sudo -u postgres psql -d taskforge_db
CREATE EXTENSION pg_stat_statements;
```

### Common Maintenance Tasks

```bash
# Restart application
sudo systemctl restart taskforge

# Reload nginx
sudo systemctl reload nginx

# Check disk space
df -h

# Check memory usage
free -h

# View active connections
sudo netstat -tulpn | grep :8000

# Database vacuum (optimize)
sudo -u postgres psql -d taskforge_db -c "VACUUM ANALYZE;"
```

### Update Application

```bash
# Switch to application user
sudo su - taskforge
cd /var/www/taskforge

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
exit
sudo systemctl restart taskforge
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs
sudo journalctl -u taskforge -n 50

# Check if port is in use
sudo netstat -tulpn | grep :8000

# Verify environment variables
sudo systemctl show taskforge --property=Environment
```

### Database connection issues
```bash
# Test database connection
psql -U taskforge_user -d taskforge_db -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

### Permission issues
```bash
# Fix uploads directory permissions
sudo chown -R taskforge:www-data /var/www/taskforge/app/uploads
sudo chmod -R 755 /var/www/taskforge/app/uploads
```

### High memory usage
```bash
# Check process memory
ps aux | grep gunicorn

# Restart application
sudo systemctl restart taskforge
```

---

## Security Checklist

- [ ] Change default admin password
- [ ] Generate secure SECRET_KEY
- [ ] Use strong database password
- [ ] Enable firewall (ufw)
- [ ] Configure SSL/HTTPS
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Regular security updates
- [ ] Database backups configured
- [ ] Restrict database access
- [ ] Monitor application logs
- [ ] Use environment variables for secrets
- [ ] Disable debug mode in production

---

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@taskforge.local

---

## License

[Specify your license here]
