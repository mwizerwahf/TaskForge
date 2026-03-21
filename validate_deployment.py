"""
Pre-deployment validation script
Run this before deploying to Vercel to ensure everything is configured correctly
"""

import os
import sys

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filepath}")
    return exists

def check_env_var(var_name, required=True):
    """Check if environment variable is set"""
    value = os.environ.get(var_name)
    exists = value is not None and value != ""
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {var_name}: {'Set' if exists else 'Not set'}")
    return exists

def validate_database_url(url):
    """Validate database URL format"""
    if not url:
        return False
    if url.startswith('postgresql://') or url.startswith('postgres://'):
        return True
    return False

def main():
    print("=" * 60)
    print("TaskForge Vercel Deployment Validation")
    print("=" * 60)
    print()
    
    all_good = True
    
    # Check required files
    print("📁 Checking Required Files...")
    print("-" * 60)
    required_files = [
        "vercel.json",
        "config_vercel.py",
        "requirements_vercel.txt",
        "app.py",
        "app/__init__.py",
    ]
    
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_good = False
    
    print()
    
    # Check optional files
    print("📄 Checking Optional Files...")
    print("-" * 60)
    optional_files = [
        ".env.vercel",
        "VERCEL_SUPABASE_DEPLOYMENT.md",
        "DEPLOYMENT_CHECKLIST.md",
        "QUICKSTART_DEPLOYMENT.md",
    ]
    
    for filepath in optional_files:
        check_file_exists(filepath, required=False)
    
    print()
    
    # Check environment variables (for local testing)
    print("🔐 Checking Environment Variables (Local .env)...")
    print("-" * 60)
    print("Note: These should be set in Vercel dashboard, not locally")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = [
        ("SECRET_KEY", True),
        ("DATABASE_URL", True),
        ("FLASK_ENV", False),
        ("VERCEL", False),
        ("SUPABASE_URL", False),
        ("SUPABASE_KEY", False),
    ]
    
    for var_name, required in env_vars:
        check_env_var(var_name, required)
    
    print()
    
    # Validate DATABASE_URL format
    print("🔍 Validating Configuration...")
    print("-" * 60)
    
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        if validate_database_url(db_url):
            print("✅ DATABASE_URL format is valid")
        else:
            print("❌ DATABASE_URL format is invalid")
            print("   Expected: postgresql://... or postgres://...")
            all_good = False
    else:
        print("⚠️  DATABASE_URL not set (will be set in Vercel)")
    
    print()
    
    # Check vercel.json content
    print("📋 Checking vercel.json Configuration...")
    print("-" * 60)
    
    try:
        import json
        with open('vercel.json', 'r') as f:
            vercel_config = json.load(f)
            
        if 'builds' in vercel_config:
            print("✅ builds configuration found")
        else:
            print("❌ builds configuration missing")
            all_good = False
            
        if 'routes' in vercel_config:
            print("✅ routes configuration found")
        else:
            print("❌ routes configuration missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error reading vercel.json: {e}")
        all_good = False
    
    print()
    
    # Check requirements_vercel.txt
    print("📦 Checking requirements_vercel.txt...")
    print("-" * 60)
    
    try:
        with open('requirements_vercel.txt', 'r') as f:
            requirements = f.read()
            
        required_packages = [
            'Flask',
            'Flask-SQLAlchemy',
            'Flask-Login',
            'psycopg2-binary',
        ]
        
        for package in required_packages:
            if package in requirements:
                print(f"✅ {package} found")
            else:
                print(f"❌ {package} missing")
                all_good = False
                
        # Check for packages that shouldn't be there
        if 'Flask-SocketIO' in requirements:
            print("⚠️  Flask-SocketIO found (not supported on Vercel)")
        if 'eventlet' in requirements:
            print("⚠️  eventlet found (not needed on Vercel)")
            
    except Exception as e:
        print(f"❌ Error reading requirements_vercel.txt: {e}")
        all_good = False
    
    print()
    
    # Check app/__init__.py for Vercel compatibility
    print("🔧 Checking app/__init__.py for Vercel compatibility...")
    print("-" * 60)
    
    try:
        with open('app/__init__.py', 'r') as f:
            init_content = f.read()
            
        if "os.environ.get('VERCEL')" in init_content:
            print("✅ Vercel environment check found")
        else:
            print("⚠️  No Vercel environment check found")
            print("   Consider running: python migrate_to_vercel.py")
            
        if "config_vercel" in init_content:
            print("✅ config_vercel import found")
        else:
            print("⚠️  config_vercel import not found")
            
    except Exception as e:
        print(f"❌ Error reading app/__init__.py: {e}")
        all_good = False
    
    print()
    print("=" * 60)
    
    if all_good:
        print("✅ All critical checks passed!")
        print()
        print("Next steps:")
        print("1. Commit your changes: git add . && git commit -m 'Prepare for Vercel'")
        print("2. Push to repository: git push")
        print("3. Go to Vercel and import your repository")
        print("4. Set environment variables in Vercel dashboard")
        print("5. Deploy!")
        print()
        print("See QUICKSTART_DEPLOYMENT.md for detailed instructions")
    else:
        print("❌ Some checks failed!")
        print()
        print("Please fix the issues above before deploying.")
        print("See VERCEL_SUPABASE_DEPLOYMENT.md for help")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == "__main__":
    main()
