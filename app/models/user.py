from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password_hash= db.Column(db.String(255), nullable=False)
    role         = db.Column(db.String(20), nullable=False, default='developer')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    created_tasks  = db.relationship('Task', foreign_keys='Task.creator_id',  backref='creator',  lazy='dynamic')
    comments       = db.relationship('TaskComment', backref='author', lazy='dynamic')
    activities     = db.relationship('ActivityLog', backref='user',   lazy='dynamic')

    @property
    def is_admin(self):   return self.role == 'admin'
    @property
    def is_manager(self): return self.role in ('admin', 'manager')

    def to_dict(self):
        return {'id':self.id,'name':self.name,'email':self.email,'role':self.role,
                'created_at':self.created_at.isoformat()}
