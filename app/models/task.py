from app import db
from datetime import datetime

class Task(db.Model):
    __tablename__ = 'tasks'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    creator_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status      = db.Column(db.String(30),  nullable=False, default='not_started')
    priority    = db.Column(db.String(20),  nullable=False, default='medium')
    start_date  = db.Column(db.Date, nullable=True)
    due_date    = db.Column(db.Date, nullable=True)
    tags        = db.Column(db.String(200), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments    = db.relationship('TaskComment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    attachments = db.relationship('Attachment',  backref='task', lazy='dynamic', cascade='all, delete-orphan')
    activities  = db.relationship('ActivityLog', backref='task', lazy='dynamic', cascade='all, delete-orphan')

    STATUS_LABELS = {'not_started':'Not Started','in_progress':'In Progress','blocked':'Blocked','completed':'Completed'}

    @property
    def is_overdue(self):
        return bool(self.due_date and self.status != 'completed' and self.due_date < datetime.utcnow().date())
    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)
    @property
    def tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else []

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'assignee_id': self.assignee_id,
            'assignee_name': self.assignee.name if self.assignee else 'Unassigned',
            'creator_id': self.creator_id,
            'status': self.status, 'status_label': self.status_label,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date':   self.due_date.isoformat()   if self.due_date   else None,
            'is_overdue': self.is_overdue, 'tags': self.tags_list,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class TaskComment(db.Model):
    __tablename__ = 'task_comments'
    id         = db.Column(db.Integer, primary_key=True)
    task_id    = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id':self.id,'task_id':self.task_id,'user_id':self.user_id,
                'author_name':self.author.name,'comment':self.comment,
                'created_at':self.created_at.isoformat()}

class Attachment(db.Model):
    __tablename__ = 'attachments'
    id            = db.Column(db.Integer, primary_key=True)
    task_id       = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    file_path     = db.Column(db.String(500), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    uploaded_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    uploader      = db.relationship('User', foreign_keys=[uploaded_by])

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action    = db.Column(db.String(200), nullable=False)
    task_id   = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {'id':self.id,'user_name':self.user.name,'action':self.action,
                'task_id':self.task_id,
                'task_title': self.task.title if self.task else None,
                'timestamp':self.timestamp.isoformat()}
