#!/bin/bash

# TaskForge Production Deployment Script
# Run as root or with sudo

set -e

echo "=========================================="
echo "TaskForge Production Deployment"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root or with sudo"
    exit 1
fi

# Variables
APP_USER="taskforge"
APP_DIR="/var/www/taskforge"
DB_NAME="taskforge_db"
DB_USER="taskforge_user"

# Generate random password
DB_PASS=$(openssl rand -base64 32)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "Step 1: Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git

echo ""
echo "Step 2: Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash $APP_USER
    usermod -aG www-data $APP_USER
fi

echo ""
echo "Step 3: Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo ""
echo "Step 4: Creating application directory..."
mkdir -p $APP_DIR
chown $APP_USER:www-data $APP_DIR

echo ""
echo "Step 5: Cloning repository..."
read -p "Enter repository URL: " REPO_URL
sudo -u $APP_USER git clone $REPO_URL $APP_DIR || echo "Repository already cloned"

echo ""
echo "Step 6: Setting up Python environment..."
cd $APP_DIR
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

echo ""
echo "Step 7: Creating environment file..."
cat > $APP_DIR/.env <<EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME
UPLOAD_FOLDER=$APP_DIR/app/uploads
MAX_CONTENT_LENGTH=16777216
EOF

chown $APP_USER:www-data $APP_DIR/.env
chmod 600 $APP_DIR/.env

echo ""
echo "Step 8: Creating uploads directory..."
mkdir -p $APP_DIR/app/uploads
chown -R $APP_USER:www-data $APP_DIR/app/uploads
chmod -R 755 $APP_DIR/app/uploads

echo ""
echo "Step 9: Initializing database..."
sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && timeout 10 python app.py" || true

echo ""
echo "Step 10: Setting up systemd service..."
mkdir -p /var/log/taskforge
chown $APP_USER:www-data /var/log/taskforge

cp $APP_DIR/taskforge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable taskforge
systemctl start taskforge

echo ""
echo "Step 11: Configuring Nginx..."
read -p "Enter your domain name (e.g., taskforge.example.com): " DOMAIN_NAME

sed "s/taskforge.example.com/$DOMAIN_NAME/g" $APP_DIR/nginx.conf > /etc/nginx/sites-available/taskforge
ln -sf /etc/nginx/sites-available/taskforge /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "Step 12: Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Application URL: http://$DOMAIN_NAME"
echo ""
echo "Default Admin Credentials:"
echo "  Email: admin@taskforge.local"
echo "  Password: changeme"
echo ""
echo "⚠️  IMPORTANT: Change the admin password immediately!"
echo ""
echo "Database Credentials (saved in .env):"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASS"
echo ""
echo "Useful Commands:"
echo "  Check status: sudo systemctl status taskforge"
echo "  View logs: sudo journalctl -u taskforge -f"
echo "  Restart app: sudo systemctl restart taskforge"
echo ""
echo "Next Steps:"
echo "  1. Change admin password"
echo "  2. Configure SSL with: sudo certbot --nginx -d $DOMAIN_NAME"
echo "  3. Setup database backups"
echo ""
