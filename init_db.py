"""
Database initialization script for Docker deployment
Run this inside the container to create tables and admin user
"""
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("✓ Tables created")
    
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@taskforge.here').first():
        print("Creating admin user...")
        admin = User(
            name='System Admin',
            email='admin@taskforge.here',
            password_hash=generate_password_hash('initpass'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created")
        print("  Email: admin@taskforge.here")
        print("  Password: changeme")
    else:
        print("✓ Admin user already exists")
    
    print("\nDatabase initialization complete!")
