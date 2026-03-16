from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    from app.routes.api import api_bp
    from app.routes.reports import reports_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(users_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app

def _seed_data():
    from app.models.user import User
    from werkzeug.security import generate_password_hash
    if User.query.count() == 0:
        admin = User(
            name='System Admin',
            email='admin@taskforge.local',
            password_hash=generate_password_hash('changeme'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
