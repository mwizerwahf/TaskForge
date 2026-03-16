from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.task import Task, TaskComment, Attachment, ActivityLog
from app.models.user import User
from app import db, socketio
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os, uuid

tasks_bp = Blueprint('tasks', __name__)

ALLOWED = {'png','jpg','jpeg','gif','pdf','doc','docx','txt','log','zip'}

def allowed_file(f):
    return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED

def log_activity(action, task_id=None):
    db.session.add(ActivityLog(user_id=current_user.id, action=action, task_id=task_id))

def can_edit(task):
    """Check if user can edit task. Creator, admins, managers, and assignees can edit."""
    if current_user.role in ('admin', 'manager'): return True
    if task.creator_id == current_user.id: return True
    if task.assignee_id == current_user.id: return True
    return False

# ── HTML pages ──────────────────────────────────────────────────────────────

@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/index.html')

@tasks_bp.route('/tasks')
@login_required
def index():
    users = User.query.order_by(User.name).all()
    return render_template('tasks/index.html', users=users)

@tasks_bp.route('/tasks/board')
@login_required
def board():
    users = User.query.order_by(User.name).all()
    return render_template('tasks/board.html', users=users)

@tasks_bp.route('/tasks/calendar')
@login_required
def calendar():
    return render_template('tasks/calendar.html')

@tasks_bp.route('/tasks/timeline')
@login_required
def timeline():
    return render_template('tasks/timeline.html')

@tasks_bp.route('/tasks/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    users = User.query.order_by(User.name).all()
    activities = ActivityLog.query.filter_by(task_id=task_id).order_by(ActivityLog.timestamp.desc()).limit(25).all()
    return render_template('tasks/detail.html', task=task, users=users, activities=activities, can_edit=can_edit(task))

@login_required
def users_page():
    if not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users/index.html', users=users)

@login_required
def reports_page():
    from app.models.user import User as U
    users = U.query.order_by(U.name).all()
    today = date.today().isoformat()
    return render_template('reports/index.html', users=users, today=today)

# ── REST API ─────────────────────────────────────────────────────────────────

@tasks_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    from sqlalchemy import func
    today = date.today()
    total = Task.query.count()
    completed_today = Task.query.filter(Task.status=='completed', func.date(Task.updated_at)==today).count()
    overdue = Task.query.filter(Task.due_date < today, Task.status != 'completed').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    status_counts = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    priority_counts = db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    workload = db.session.query(User.name, func.count(Task.id)).join(Task, Task.assignee_id==User.id).group_by(User.id).all()
    from datetime import timedelta
    weekly = []
    for i in range(6,-1,-1):
        day = today - timedelta(days=i)
        cnt = Task.query.filter(func.date(Task.updated_at)==day).count()
        weekly.append({'date': day.strftime('%a'), 'count': cnt})
    recent = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    return jsonify({
        'total': total, 'completed_today': completed_today,
        'overdue': overdue, 'in_progress': in_progress,
        'status_distribution': [{'status':s,'count':c} for s,c in status_counts],
        'priority_distribution': [{'priority':p,'count':c} for p,c in priority_counts],
        'developer_workload': [{'name':n,'count':c} for n,c in workload],
        'weekly_activity': weekly,
        'recent_activity': [a.to_dict() for a in recent]
    })

@tasks_bp.route('/api/tasks', methods=['GET'])
@login_required
def api_list():
    q = Task.query
    if s := request.args.get('status'): q = q.filter_by(status=s)
    if p := request.args.get('priority'): q = q.filter_by(priority=p)
    if a := request.args.get('assignee'): q = q.filter_by(assignee_id=int(a))
    if kw := request.args.get('search'): q = q.filter(Task.title.ilike(f'%{kw}%'))
    if request.args.get('overdue') == '1': q = q.filter(Task.due_date < date.today(), Task.status != 'completed')
    if sr := request.args.get('start_range'): q = q.filter(Task.due_date >= sr)
    if er := request.args.get('end_range'): q = q.filter(Task.due_date <= er)
    return jsonify([t.to_dict() for t in q.order_by(Task.created_at.desc()).all()])

@tasks_bp.route('/api/tasks', methods=['POST'])
@login_required
def api_create():
    if current_user.role == 'viewer': return jsonify({'error':'Permission denied'}), 403
    d = request.json
    task = Task(
        title=d['title'], description=d.get('description',''),
        assignee_id=d.get('assignee_id') or None, creator_id=current_user.id,
        status=d.get('status','not_started'), priority=d.get('priority','medium'),
        start_date=datetime.strptime(d['start_date'],'%Y-%m-%d').date() if d.get('start_date') else None,
        due_date=datetime.strptime(d['due_date'],'%Y-%m-%d').date() if d.get('due_date') else None,
        tags=d.get('tags','')
    )
    db.session.add(task)
    db.session.flush()
    log_activity(f'Created task "{task.title}"', task.id)
    db.session.commit()
    socketio.emit('task_created', task.to_dict())
    return jsonify(task.to_dict()), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def api_get(task_id):
    return jsonify(Task.query.get_or_404(task_id).to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def api_update(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_edit(task): return jsonify({'error':'Permission denied'}), 403
    d = request.json
    old_status = task.status
    for f in ['title','description','status','priority','tags']:
        if f in d: setattr(task, f, d[f])
    if 'assignee_id' in d: task.assignee_id = d['assignee_id'] or None
    if d.get('start_date'): task.start_date = datetime.strptime(d['start_date'],'%Y-%m-%d').date()
    if d.get('due_date'): task.due_date = datetime.strptime(d['due_date'],'%Y-%m-%d').date()
    task.updated_at = datetime.utcnow()
    action = f'Changed status of "{task.title}" from {old_status} to {task.status}' if old_status != task.status else f'Updated task "{task.title}"'
    log_activity(action, task.id)
    db.session.commit()
    socketio.emit('task_updated', task.to_dict())
    return jsonify(task.to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>/status', methods=['PATCH'])
@login_required
def api_status(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_edit(task): return jsonify({'error':'Permission denied'}), 403
    old = task.status
    task.status = request.json['status']
    task.updated_at = datetime.utcnow()
    log_activity(f'Moved "{task.title}" → {task.status}', task.id)
    db.session.commit()
    socketio.emit('task_status_changed', {'task_id':task_id,'old_status':old,'new_status':task.status,'task':task.to_dict()})
    return jsonify(task.to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def api_delete(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.role not in ('admin','manager'): return jsonify({'error':'Permission denied'}), 403
    title = task.title
    db.session.delete(task)
    db.session.commit()
    socketio.emit('task_deleted', {'task_id':task_id,'title':title})
    return jsonify({'success':True})

@tasks_bp.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
@login_required
def api_comments_get(task_id):
    Task.query.get_or_404(task_id)
    return jsonify([c.to_dict() for c in TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at).all()])

@tasks_bp.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
@login_required
def api_comments_post(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.role == 'viewer': return jsonify({'error':'Permission denied'}), 403
    comment = TaskComment(task_id=task_id, user_id=current_user.id, comment=request.json['comment'])
    db.session.add(comment)
    log_activity(f'Commented on "{task.title}"', task_id)
    db.session.commit()
    cd = comment.to_dict()
    socketio.emit('comment_added', {'task_id':task_id,'comment':cd})
    return jsonify(cd), 201

@tasks_bp.route('/api/tasks/<int:task_id>/upload', methods=['POST'])
@login_required
def api_upload(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_edit(task): return jsonify({'error':'Permission denied'}), 403
    f = request.files.get('file')
    if not f or not f.filename or not allowed_file(f.filename):
        return jsonify({'error':'Invalid file'}), 400
    ext = f.filename.rsplit('.',1)[1].lower()
    fname = f'{uuid.uuid4().hex}.{ext}'
    f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
    att = Attachment(task_id=task_id, file_path=fname, original_name=secure_filename(f.filename), uploaded_by=current_user.id)
    db.session.add(att)
    log_activity(f'Uploaded file to "{task.title}"', task_id)
    db.session.commit()
    return jsonify({'id':att.id,'name':att.original_name}), 201

@tasks_bp.route('/api/calendar/tasks')
@login_required
def api_calendar():
    tasks = Task.query.filter(Task.due_date != None).all()
    color_map = {'not_started':'#6c757d','in_progress':'#4f8ef7','blocked':'#ff3b5c','completed':'#00d17a'}
    events = [{'id':t.id,'title':t.title,'start':t.start_date.isoformat() if t.start_date else t.due_date.isoformat(),'end':t.due_date.isoformat(),'color':color_map.get(t.status,'#6c757d'),'extendedProps':{'status':t.status,'priority':t.priority,'assignee':t.assignee.name if t.assignee else 'Unassigned'}} for t in tasks]
    return jsonify(events)

@tasks_bp.route('/api/timeline/tasks')
@login_required
def api_timeline():
    tasks = Task.query.filter(Task.start_date != None, Task.due_date != None).all()
    return jsonify([t.to_dict() for t in tasks])

@tasks_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    return jsonify([u.to_dict() for u in User.query.order_by(User.name).all()])
