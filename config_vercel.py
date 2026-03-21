import os
from datetime import timedelta

class Config:
    # Security env
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
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
        }
    }
    
    # File Uploads - Vercel uses /tmp for temporary storage
    UPLOAD_FOLDER = '/tmp/uploads'
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
    
    # Supabase (optional - for file storage)
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
