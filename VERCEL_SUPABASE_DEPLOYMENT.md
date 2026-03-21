# TaskForge: Supabase + Vercel Deployment Guide

Complete step-by-step guide to migrate TaskForge from SQLite to Supabase PostgreSQL and deploy on Vercel.

## Prerequisites

- Supabase account (https://supabase.com)
- Vercel account (https://vercel.com)
- Git repository (GitHub, GitLab, or Bitbucket)
- Local development environment with Python 3.9+

---

## Part 1: Supabase Database Setup

### Step 1: Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click **"New Project"**
3. Fill in project details:
   - **Name**: `taskforge`
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier is sufficient for testing
4. Click **"Create new project"** (takes ~2 minutes)

### Step 2: Get Database Connection String

1. In your Supabase project dashboard, go to **Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **URI** tab
4. Copy the connection string (looks like):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual database password
6. **Save this connection string** - you'll need it multiple times

### Step 3: Export Current Database Schema

Run locally to export your current schema:

```bash
# If using SQLite (current setup)
sqlite3 taskforge.db .dump > schema_export.sql

# Or if you have existing PostgreSQL data
pg_dump -h localhost -U taskforge_user -d taskforge_db --schema-only > schema_export.sql
```

### Step 4: Create Tables in Supabase

**Option A: Using Supabase SQL Editor (Recommended)**

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New query"**
3. Copy and paste your schema from `schema.sql` file
4. Click **"Run"** to execute

**Option B: Using Flask-Migrate**

1. Update your local `.env` file with Supabase connection string:
   ```bash
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

2. Run migrations:
   ```bash
   # Initialize migrations (if not already done)
   flask db init

   # Create migration
   flask db migrate -m "Initial Supabase migration"

   # Apply to Supabase
   flask db upgrade
   ```

### Step 5: Verify Database Setup

1. In Supabase dashboard, go to **Table Editor**
2. Verify these tables exist:
   - `user`
   - `task`
   - `comment`
   - `attachment`
   - `activity_log`

### Step 6: Create Initial Admin User

1. In Supabase **SQL Editor**, run:
   ```sql
   INSERT INTO "user" (username, email, password_hash, role, is_active, created_at)
   VALUES (
     'admin',
     'admin@taskforge.local',
     'scrypt:32768:8:1$CHANGE_THIS_HASH',  -- You'll update this after first login
     'admin',
     true,
     NOW()
   );
   ```

2. Or use Python locally:
   ```bash
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"
   ```
   Then insert the hash into the SQL above.

---

## Part 2: Prepare Application for Vercel

### Step 7: Update Configuration

Create `config_vercel.py`:

```python
import os
from datetime import timedelta

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Database - Vercel compatible
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # File Uploads - Use Vercel Blob or S3 for production
    UPLOAD_FOLDER = '/tmp/uploads'  # Vercel uses /tmp for temporary storage
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'log', 'zip'}
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_ENABLED = True
```

### Step 8: Create Vercel Configuration

Create `vercel.json` in project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/app/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  }
}
```

### Step 9: Update Requirements for Vercel

Create `requirements_vercel.txt`:

```txt
Flask==3.0.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Werkzeug==3.0.3
SQLAlchemy==2.0.36
reportlab==4.2.2
Pillow==10.4.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

**Note**: Removed Flask-SocketIO and related packages because Vercel serverless functions don't support WebSockets. You'll need to disable real-time features or use Vercel's Edge Functions with Pusher/Ably.

### Step 10: Create Vercel Entry Point

Create `api/index.py`:

```python
from app import create_app

app = create_app()

# Vercel serverless function handler
def handler(request):
    return app(request.environ, request.start_response)
```

Or update `app.py` to be Vercel-compatible:

```python
from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

# For Vercel
if __name__ != '__main__':
    # Production mode on Vercel
    pass
else:
    # Local development
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Step 11: Handle File Uploads (Important!)

Vercel's serverless functions have read-only filesystem except `/tmp`. You have 3 options:

**Option A: Disable file uploads temporarily**
**Option B: Use Supabase Storage**
**Option C: Use Vercel Blob Storage**

For **Option B (Supabase Storage)** - Recommended:

1. Install Supabase client:
   ```bash
   pip install supabase
   ```

2. Update `requirements_vercel.txt`:
   ```txt
   supabase==2.3.0
   ```

3. Create `app/utils/storage.py`:
   ```python
   import os
   from supabase import create_client, Client
   
   supabase_url = os.environ.get('SUPABASE_URL')
   supabase_key = os.environ.get('SUPABASE_KEY')
   supabase: Client = create_client(supabase_url, supabase_key)
   
   def upload_file(file, filename):
       bucket_name = 'taskforge-uploads'
       response = supabase.storage.from_(bucket_name).upload(filename, file)
       return response
   
   def get_file_url(filename):
       bucket_name = 'taskforge-uploads'
       return supabase.storage.from_(bucket_name).get_public_url(filename)
   ```

4. In Supabase dashboard:
   - Go to **Storage**
   - Create bucket: `taskforge-uploads`
   - Set to **Public** or configure policies

### Step 12: Disable WebSocket Features

Update `app/__init__.py` to conditionally initialize SocketIO:

```python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Only initialize SocketIO in non-Vercel environments
socketio = None
if os.environ.get('VERCEL') != '1':
    from flask_socketio import SocketIO
    socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Load config
    if os.environ.get('VERCEL') == '1':
        from config_vercel import Config
    else:
        from config import Config
    
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    if socketio:
        socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes import auth, tasks, users, reports, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(users.bp)
    app.register_blueprint(reports.bp)
    if socketio:
        app.register_blueprint(api.bp)
    
    return app
```

---

## Part 3: Deploy to Vercel

### Step 13: Push Code to Git

```bash
git add .
git commit -m "Prepare for Vercel deployment with Supabase"
git push origin main
```

### Step 14: Connect Vercel to Repository

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Import your Git repository
4. Select the repository containing TaskForge

### Step 15: Configure Environment Variables

In Vercel project settings, add these environment variables:

```
SECRET_KEY=<generate-with-python-secrets.token_hex(32)>
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
FLASK_ENV=production
VERCEL=1
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
```

To get Supabase keys:
1. Go to Supabase dashboard → **Settings** → **API**
2. Copy **Project URL** → Use as `SUPABASE_URL`
3. Copy **anon public** key → Use as `SUPABASE_KEY`

### Step 16: Configure Build Settings

In Vercel:
- **Framework Preset**: Other
- **Build Command**: `pip install -r requirements_vercel.txt`
- **Output Directory**: Leave empty
- **Install Command**: `pip install -r requirements_vercel.txt`

### Step 17: Deploy

1. Click **"Deploy"**
2. Wait for build to complete (~2-3 minutes)
3. Vercel will provide a URL: `https://taskforge-xxxxx.vercel.app`

### Step 18: Test Deployment

1. Visit your Vercel URL
2. Try logging in with admin credentials
3. Test basic functionality:
   - Create a task
   - View tasks
   - Update task status
   - Generate report

---

## Part 4: Post-Deployment Configuration

### Step 19: Set Up Custom Domain (Optional)

1. In Vercel project → **Settings** → **Domains**
2. Add your custom domain
3. Configure DNS records as instructed by Vercel

### Step 20: Enable Supabase Row Level Security (RLS)

For production security:

1. In Supabase dashboard → **Authentication** → **Policies**
2. Enable RLS on tables
3. Create policies for your application

Example policy:
```sql
-- Enable RLS
ALTER TABLE task ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all tasks
CREATE POLICY "Allow authenticated read" ON task
  FOR SELECT
  USING (auth.role() = 'authenticated');
```

### Step 21: Monitor and Debug

**Vercel Logs:**
- Go to your project → **Deployments** → Click deployment → **Functions** tab
- View real-time logs

**Supabase Logs:**
- Go to **Logs** → **Postgres Logs**
- Monitor database queries and errors

---

## Troubleshooting

### Issue: Database Connection Timeout

**Solution**: Check Supabase connection pooling settings:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {
        'connect_timeout': 10,
    }
}
```

### Issue: Static Files Not Loading

**Solution**: Update `vercel.json` routes:
```json
{
  "src": "/static/(.*)",
  "dest": "/app/static/$1"
}
```

### Issue: 500 Internal Server Error

**Solution**: Check Vercel function logs and ensure all environment variables are set correctly.

### Issue: File Uploads Failing

**Solution**: Implement Supabase Storage as described in Step 11.

---

## Limitations on Vercel

1. **No WebSockets**: Real-time features disabled (Kanban drag-drop won't sync in real-time)
2. **Serverless Functions**: 10-second timeout on Hobby plan, 60s on Pro
3. **File Storage**: Use external storage (Supabase Storage, AWS S3, Vercel Blob)
4. **Cold Starts**: First request may be slow after inactivity

---

## Alternative: Keep WebSockets

If you need real-time features, consider:

1. **Deploy Flask app on Railway/Render** (supports WebSockets)
2. **Use Vercel for frontend only** + separate backend
3. **Replace SocketIO with Pusher/Ably** (works with serverless)

---

## Cost Estimate

- **Supabase Free Tier**: 500MB database, 1GB file storage, 2GB bandwidth
- **Vercel Hobby**: Free for personal projects, 100GB bandwidth
- **Total**: $0/month for small projects

---

## Next Steps

1. Set up monitoring (Sentry, LogRocket)
2. Configure backups (Supabase automatic backups)
3. Set up CI/CD pipeline
4. Add health check endpoint
5. Configure rate limiting

---

## Support

For issues:
- Vercel Docs: https://vercel.com/docs
- Supabase Docs: https://supabase.com/docs
- Flask on Vercel: https://vercel.com/docs/frameworks/flask
