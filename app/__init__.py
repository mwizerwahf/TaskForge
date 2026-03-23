from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load appropriate config
    if os.environ.get('VERCEL') == '1':
        from config_vercel import Config
    else:
        from config import Config
    
    app.config.from_object(Config)
    
    # Create upload folder if not on Vercel
    if os.environ.get('VERCEL') != '1':
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    from app.routes.reports import reports_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 503

    # Only initialize database if not on Vercel (use migrations instead)
    if os.environ.get('VERCEL') != '1':
        with app.app_context():
            db.create_all()
            _seed_data()

    return app

def _seed_data():
    from app.models.user import User, user_roles
    from werkzeug.security import generate_password_hash
    if User.query.count() == 0:
        admin = User(
            name='System Admin',
            email='admin@taskforge.local',
            password_hash=generate_password_hash('changeme'),
            role='admin'
        )
        db.session.add(admin)
        db.session.flush()
        db.session.execute(
            db.text('INSERT INTO user_roles (user_id, role) VALUES (:uid, :role)'),
            {'uid': admin.id, 'role': 'admin'}
        )
        db.session.commit()
    else:
        # Migrate existing users: seed user_roles if empty
        count = db.session.execute(db.text('SELECT COUNT(*) FROM user_roles')).scalar()
        if count == 0:
            for u in User.query.all():
                db.session.execute(
                    db.text('INSERT OR IGNORE INTO user_roles (user_id, role) VALUES (:uid, :role)'),
                    {'uid': u.id, 'role': u.role}
                )
            db.session.commit()
