from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ALL_ROLES = ['developer', 'manager', 'viewer', 'admin', 'technician', 'accountant', 'ceo']

# Association table: user ↔ roles
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role',    db.String(20),                          primary_key=True)
)

class ManagerRole(db.Model):
    """Roles that a manager user is allowed to manage."""
    __tablename__ = 'manager_roles'
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role       = db.Column(db.String(20),                          primary_key=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Legacy single-role kept for backward compat; primary role = first in roles list
    role          = db.Column(db.String(20), nullable=False, default='developer')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    managed_roles = db.relationship('ManagerRole', backref='manager',
                                    cascade='all, delete-orphan',
                                    foreign_keys='ManagerRole.manager_id')

    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    created_tasks  = db.relationship('Task', foreign_keys='Task.creator_id',  backref='creator',  lazy='dynamic')
    comments       = db.relationship('TaskComment', backref='author', lazy='dynamic')
    activities     = db.relationship('ActivityLog', backref='user',   lazy='dynamic')

    def get_roles(self):
        """Return list of role strings for this user."""
        rows = db.session.execute(
            db.text('SELECT role FROM user_roles WHERE user_id = :uid'),
            {'uid': self.id}
        ).fetchall()
        return [r[0] for r in rows] if rows else [self.role]

    def has_role(self, *roles):
        return any(r in self.get_roles() for r in roles)

    def get_managed_roles(self):
        return [mr.role for mr in self.managed_roles]

    @property
    def is_admin(self):
        return self.has_role('admin')

    @property
    def is_manager(self):
        return self.has_role('admin', 'manager', 'ceo')

    @property
    def is_viewer(self):
        return self.has_role('viewer')

    @property
    def can_see_all_tasks(self):
        """Viewer and admin can see all tasks."""
        return self.has_role('viewer', 'admin')

    @property
    def can_create_task(self):
        """Admin and viewer cannot create tasks."""
        return not self.has_role('admin', 'viewer')

    def can_manage_user(self, other_user):
        """True if self is a manager/ceo/admin who manages at least one of other_user's roles."""
        if self.has_role('admin'):
            return True
        if self.has_role('ceo'):
            return True
        if self.has_role('manager'):
            my_managed = set(self.get_managed_roles())
            their_roles = set(other_user.get_roles())
            return bool(my_managed & their_roles)
        return False

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'email': self.email,
            'role': self.role, 'roles': self.get_roles(),
            'managed_roles': self.get_managed_roles(),
            'created_at': self.created_at.isoformat()
        }
