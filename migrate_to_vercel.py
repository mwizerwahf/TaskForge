"""
Migration script to update app/__init__.py for Vercel compatibility
Run this script before deploying to Vercel
"""

import shutil
import os

def migrate():
    print("TaskForge Vercel Migration Script")
    print("=" * 50)
    
    # Backup original file
    original = "app/__init__.py"
    backup = "app/__init__.py.backup"
    vercel_version = "app/__init___vercel.py"
    
    if not os.path.exists(original):
        print("❌ Error: app/__init__.py not found")
        return
    
    # Create backup
    print(f"📦 Creating backup: {backup}")
    shutil.copy2(original, backup)
    print("✅ Backup created")
    
    # Copy Vercel version
    if os.path.exists(vercel_version):
        print(f"📝 Updating {original} with Vercel-compatible version")
        shutil.copy2(vercel_version, original)
        print("✅ File updated successfully")
    else:
        print(f"❌ Error: {vercel_version} not found")
        return
    
    print("\n" + "=" * 50)
    print("✅ Migration complete!")
    print("\nNext steps:")
    print("1. Review the changes in app/__init__.py")
    print("2. Test locally: python app.py")
    print("3. Commit changes: git add . && git commit -m 'Prepare for Vercel'")
    print("4. Push to repository: git push")
    print("5. Deploy on Vercel")
    print("\nTo rollback: cp app/__init__.py.backup app/__init__.py")

if __name__ == "__main__":
    migrate()
