from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.task import Task, TaskComment, Attachment, ActivityLog, TaskHistory, Tag
from app.models.user import User
from app import db
from datetime import datetime, date
from werkzeug.utils import secure_filename
import os, uuid

tasks_bp = Blueprint('tasks', __name__)

ALLOWED = {'png','jpg','jpeg','gif','pdf','doc','docx','txt','log','zip'}

def allowed_file(f):
    return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED

def log_activity(action, task_id=None):
    db.session.add(ActivityLog(user_id=current_user.id, action=action, task_id=task_id))

def visible_task_ids():
    """Return a query filter for tasks the current user may see."""
    u = current_user
    # Admin, viewer, and CEO see everything
    if u.can_see_all_tasks or u.has_role('ceo'):
        return None  # no filter needed

    # Manager sees tasks assigned to themselves OR to users they manage
    if u.has_role('manager'):
        managed = u.get_managed_roles()
        # Get users who have ANY of the managed roles
        managed_user_ids = set()
        for user in User.query.all():
            user_roles = set(user.get_roles())
            if user_roles & set(managed):  # intersection
                managed_user_ids.add(user.id)
        managed_user_ids.add(u.id)
        return managed_user_ids

    # Developer / technician / accountant: see own tasks + tasks of same-role peers
    user_roles = u.get_roles()
    peer_ids = set([u.id])  # always include self
    for role in user_roles:
        for peer in User.query.all():
            if peer.has_role(role):
                peer_ids.add(peer.id)
    return peer_ids

def _users_in_roles(roles):
    """Return set of user IDs that have at least one of the given roles."""
    ids = set()
    for u in User.query.all():
        if any(u.has_role(r) for r in roles):
            ids.add(u.id)
    return ids

def get_visible_tasks(base_query=None):
    q = base_query or Task.query
    allowed_ids = visible_task_ids()
    if allowed_ids is None:
        return q
    return q.filter(
        db.or_(
            Task.assignee_id.in_(allowed_ids),
            Task.creator_id.in_(allowed_ids),
            Task.assignee_id == None
        )
    )

def can_edit(task):
    u = current_user
    if u.can_see_all_tasks or u.has_role('ceo'):
        return True
    if u.has_role('manager'):
        # manager can edit tasks of users they manage or themselves
        if task.creator_id == u.id or task.assignee_id == u.id:
            return True
        if task.assignee_id:
            assignee = User.query.get(task.assignee_id)
            return assignee and u.can_manage_user(assignee)
        return False
    # developer/technician/accountant: only own tasks
    return task.creator_id == u.id or task.assignee_id == u.id

def can_delete_task(task):
    """Only creator or admin/ceo/manager can delete."""
    if current_user.has_role('admin', 'ceo'):
        return True
    if current_user.has_role('manager'):
        return can_edit(task)
    return task.creator_id == current_user.id

def can_change_status(task):
    """Only assignee or creator can change status."""
    return task.assignee_id == current_user.id or task.creator_id == current_user.id

def can_change_assignee_or_priority(task):
    """Only creator, manager, ceo, admin can change assignee/priority."""
    if current_user.has_role('admin', 'ceo', 'manager'):
        return True
    return task.creator_id == current_user.id

def log_history(task_id, field, old_val, new_val):
    """Log task field change to history."""
    if old_val != new_val:
        h = TaskHistory(task_id=task_id, user_id=current_user.id,
                       field=field, old_value=str(old_val) if old_val else '',
                       new_value=str(new_val) if new_val else '')
        db.session.add(h)

def can_create_task():
    u = current_user
    if u.has_role('admin'):
        return False   # admin cannot create tasks
    if u.has_role('viewer'):
        return False
    return True

def can_assign_to(assignee_id, assignee_role=None):
    """Check if current user can assign a task to the given user."""
    u = current_user
    if u.has_role('admin'):
        return False  # admin cannot create/assign tasks
    if u.has_role('ceo', 'manager'):
        if assignee_id == u.id:
            return True
        assignee = User.query.get(assignee_id)
        return assignee and u.can_manage_user(assignee)
    # developer / technician / accountant: only self-assign
    return int(assignee_id) == u.id

# ── HTML pages ──────────────────────────────────────────────────────────────

@tasks_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/index.html')

@tasks_bp.route('/tasks')
@login_required
def index():
    users = _assignable_users()
    return render_template('tasks/index.html', users=users)

@tasks_bp.route('/tasks/board')
@login_required
def board():
    users = _assignable_users()
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
    users = _assignable_users()
    activities = ActivityLog.query.filter_by(task_id=task_id).order_by(ActivityLog.timestamp.desc()).limit(25).all()
    return render_template('tasks/detail.html', task=task, users=users, activities=activities, can_edit=can_edit(task))

def _assignable_users():
    """Users the current user can assign tasks to."""
    u = current_user
    if u.has_role('admin'):
        return []
    if u.has_role('ceo'):
        return User.query.order_by(User.name).all()
    if u.has_role('manager'):
        managed = u.get_managed_roles()
        ids = _users_in_roles(managed)
        ids.add(u.id)
        return User.query.filter(User.id.in_(ids)).order_by(User.name).all()
    # developer/technician/accountant: only self
    return [u]

# ── REST API ─────────────────────────────────────────────────────────────────

@tasks_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    from sqlalchemy import func
    today = date.today()
    base = get_visible_tasks()
    total = base.count()
    completed_today = base.filter(Task.status=='completed', func.date(Task.updated_at)==today).count()
    overdue = base.filter(Task.due_date < today, Task.status != 'completed').count()
    in_progress = base.filter_by(status='in_progress').count()
    status_counts   = db.session.query(Task.status,   func.count(Task.id)).filter(Task.id.in_([t.id for t in base])).group_by(Task.status).all()
    priority_counts = db.session.query(Task.priority, func.count(Task.id)).filter(Task.id.in_([t.id for t in base])).group_by(Task.priority).all()
    workload = db.session.query(User.name, func.count(Task.id)).join(Task, Task.assignee_id==User.id).filter(Task.id.in_([t.id for t in base])).group_by(User.id).all()
    from datetime import timedelta
    weekly = []
    for i in range(6,-1,-1):
        day = today - timedelta(days=i)
        cnt = base.filter(func.date(Task.updated_at)==day).count()
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
    q = get_visible_tasks()
    if s := request.args.get('status'):   q = q.filter_by(status=s)
    if p := request.args.get('priority'): q = q.filter_by(priority=p)
    if a := request.args.get('assignee'): q = q.filter_by(assignee_id=int(a))
    if kw := request.args.get('search'):  q = q.filter(Task.title.ilike(f'%{kw}%'))
    if request.args.get('overdue') == '1': q = q.filter(Task.due_date < date.today(), Task.status != 'completed')
    if sr := request.args.get('start_range'): q = q.filter(Task.due_date >= sr)
    if er := request.args.get('end_range'):   q = q.filter(Task.due_date <= er)
    return jsonify([t.to_dict() for t in q.order_by(Task.created_at.desc()).all()])

@tasks_bp.route('/api/tasks', methods=['POST'])
@login_required
def api_create():
    if not can_create_task():
        return jsonify({'error': 'Permission denied'}), 403
    d = request.json
    assignee_id   = d.get('assignee_id') or None
    assignee_role = d.get('assignee_role') or None

    if assignee_id and not can_assign_to(assignee_id, assignee_role):
        return jsonify({'error': 'You cannot assign tasks to this user'}), 403

    task = Task(
        title=d['title'], description=d.get('description',''),
        assignee_id=assignee_id, assignee_role=assignee_role,
        creator_id=current_user.id,
        status=d.get('status','not_started'), priority=d.get('priority','medium'),
        start_date=datetime.strptime(d['start_date'],'%Y-%m-%d').date() if d.get('start_date') else None,
        due_date=datetime.strptime(d['due_date'],'%Y-%m-%d').date()     if d.get('due_date')   else None,
        tags=d.get('tags','')
    )
    db.session.add(task)
    db.session.flush()
    log_activity(f'Created task "{task.title}"', task.id)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
@login_required
def api_get(task_id):
    return jsonify(Task.query.get_or_404(task_id).to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def api_update(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_edit(task):
        return jsonify({'error': 'Permission denied'}), 403
    d = request.json
    
    # Validate dates
    start_date = d.get('start_date')
    due_date = d.get('due_date')
    if start_date and due_date:
        if datetime.strptime(due_date, '%Y-%m-%d').date() < datetime.strptime(start_date, '%Y-%m-%d').date():
            return jsonify({'error': 'Due date cannot be before start date'}), 400
    
    old_status = task.status
    
    # Track changes
    if 'title' in d and d['title'] != task.title:
        log_history(task_id, 'title', task.title, d['title'])
        task.title = d['title']
    
    if 'description' in d and d['description'] != task.description:
        log_history(task_id, 'description', task.description, d['description'])
        task.description = d['description']
    
    if 'status' in d and d['status'] != task.status:
        if not can_change_status(task):
            return jsonify({'error': 'Only assignee or creator can change status'}), 403
        log_history(task_id, 'status', task.status, d['status'])
        task.status = d['status']
    
    if 'priority' in d and d['priority'] != task.priority:
        if not can_change_assignee_or_priority(task):
            return jsonify({'error': 'Only creator or manager can change priority'}), 403
        log_history(task_id, 'priority', task.priority, d['priority'])
        task.priority = d['priority']
    
    if 'tags' in d and d['tags'] != task.tags:
        log_history(task_id, 'tags', task.tags, d['tags'])
        task.tags = d['tags']
        # Store unique tags
        for tag_name in [t.strip() for t in d['tags'].split(',') if t.strip()]:
            if not Tag.query.filter_by(name=tag_name).first():
                db.session.add(Tag(name=tag_name))
    
    if 'assignee_id' in d:
        new_assignee = d['assignee_id'] or None
        if new_assignee != task.assignee_id:
            if not can_change_assignee_or_priority(task):
                return jsonify({'error': 'Only creator or manager can change assignee'}), 403
            if new_assignee and not can_assign_to(new_assignee, d.get('assignee_role')):
                return jsonify({'error': 'You cannot assign tasks to this user'}), 403
            log_history(task_id, 'assignee_id', task.assignee_id, new_assignee)
            task.assignee_id = new_assignee
            task.assignee_role = d.get('assignee_role') or task.assignee_role
    
    if start_date and start_date != (task.start_date.isoformat() if task.start_date else None):
        log_history(task_id, 'start_date', task.start_date, start_date)
        task.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    if due_date and due_date != (task.due_date.isoformat() if task.due_date else None):
        log_history(task_id, 'due_date', task.due_date, due_date)
        task.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    
    task.updated_at = datetime.utcnow()
    action = f'Changed status of "{task.title}" from {old_status} to {task.status}' if old_status != task.status else f'Updated task "{task.title}"'
    log_activity(action, task.id)
    db.session.commit()
    return jsonify(task.to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>/status', methods=['PATCH'])
@login_required
def api_status(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_change_status(task):
        return jsonify({'error': 'Only assignee or creator can change status'}), 403
    old = task.status
    new_status = request.json['status']
    log_history(task_id, 'status', old, new_status)
    task.status = new_status
    task.updated_at = datetime.utcnow()
    log_activity(f'Moved "{task.title}" → {task.status}', task.id)
    db.session.commit()
    return jsonify(task.to_dict())

@tasks_bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def api_delete(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_delete_task(task):
        return jsonify({'error': 'Only creator or manager can delete tasks'}), 403
    title = task.title
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

@tasks_bp.route('/api/tasks/<int:task_id>/comments', methods=['GET'])
@login_required
def api_comments_get(task_id):
    Task.query.get_or_404(task_id)
    return jsonify([c.to_dict() for c in TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at).all()])

@tasks_bp.route('/api/tasks/<int:task_id>/history', methods=['GET'])
@login_required
def api_history_get(task_id):
    """Get edit history for a task."""
    Task.query.get_or_404(task_id)
    history = TaskHistory.query.filter_by(task_id=task_id).order_by(TaskHistory.changed_at.desc()).all()
    return jsonify([h.to_dict() for h in history])

@tasks_bp.route('/api/tasks/<int:task_id>/comments', methods=['POST'])
@login_required
def api_comments_post(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.is_viewer:
        return jsonify({'error': 'Permission denied'}), 403
    comment = TaskComment(task_id=task_id, user_id=current_user.id, comment=request.json['comment'])
    db.session.add(comment)
    log_activity(f'Commented on "{task.title}"', task_id)
    db.session.commit()
    cd = comment.to_dict()
    return jsonify(cd), 201

@tasks_bp.route('/api/tasks/<int:task_id>/upload', methods=['POST'])
@login_required
def api_upload(task_id):
    task = Task.query.get_or_404(task_id)
    if not can_edit(task):
        return jsonify({'error': 'Permission denied'}), 403
    f = request.files.get('file')
    if not f or not f.filename or not allowed_file(f.filename):
        return jsonify({'error': 'Invalid file'}), 400
    ext   = f.filename.rsplit('.',1)[1].lower()
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
    tasks = get_visible_tasks(Task.query.filter(Task.due_date != None)).all()
    color_map = {'not_started':'#6c757d','in_progress':'#4f8ef7','blocked':'#ff3b5c','completed':'#00d17a'}
    events = [{'id':t.id,'title':t.title,
               'start':t.start_date.isoformat() if t.start_date else t.due_date.isoformat(),
               'end':t.due_date.isoformat(),
               'color':color_map.get(t.status,'#6c757d'),
               'extendedProps':{'status':t.status,'priority':t.priority,
                                'assignee':t.assignee.name if t.assignee else 'Unassigned'}}
              for t in tasks]
    return jsonify(events)

@tasks_bp.route('/api/timeline/tasks')
@login_required
def api_timeline():
    tasks = get_visible_tasks(Task.query.filter(Task.start_date != None, Task.due_date != None)).all()
    return jsonify([t.to_dict() for t in tasks])

@tasks_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    users = _assignable_users()
    return jsonify([u.to_dict() for u in users])

@tasks_bp.route('/api/assignable-users/<int:assignee_id>/roles')
@login_required
def api_user_roles(assignee_id):
    """Return roles of a user that the current user can assign under."""
    assignee = User.query.get_or_404(assignee_id)
    roles = assignee.get_roles()
    
    # If assigning to self, return all their roles
    if assignee_id == current_user.id:
        return jsonify(roles)
    
    # CEO can assign under any role
    if current_user.has_role('ceo'):
        return jsonify(roles)
    
    # Manager: filter to only roles they manage
    if current_user.has_role('manager'):
        managed = set(current_user.get_managed_roles())
        # If manager has no managed roles configured, they can still assign under 'manager' role
        if not managed:
            roles = [r for r in roles if r == 'manager']
        else:
            roles = [r for r in roles if r in managed]
    
    return jsonify(roles)

@tasks_bp.route('/api/tags', methods=['GET'])
@login_required
def api_tags():
    """Get all unique tags for autocomplete."""
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify([t.to_dict() for t in tags])

@tasks_bp.route('/api/debug/task-counts')
@login_required
def api_debug_counts():
    """Debug endpoint to show task counts across different views."""
    visible = get_visible_tasks()
    all_visible = visible.all()
    with_due = visible.filter(Task.due_date != None).all()
    with_start_and_due = visible.filter(Task.start_date != None, Task.due_date != None).all()
    
    return jsonify({
        'user': current_user.name,
        'roles': current_user.get_roles(),
        'total_visible': len(all_visible),
        'with_due_date': len(with_due),
        'with_start_and_due': len(with_start_and_due),
        'tasks': [{
            'id': t.id,
            'title': t.title,
            'assignee': t.assignee.name if t.assignee else 'Unassigned',
            'start_date': t.start_date.isoformat() if t.start_date else None,
            'due_date': t.due_date.isoformat() if t.due_date else None
        } for t in all_visible]
    })
