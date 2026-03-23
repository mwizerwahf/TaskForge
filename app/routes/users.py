from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User, ManagerRole, ALL_ROLES, user_roles
from app import db

users_bp = Blueprint('users', __name__)

def _sync_roles(user, roles_list):
    """Replace user's roles with the given list."""
    db.session.execute(
        db.text('DELETE FROM user_roles WHERE user_id = :uid'),
        {'uid': user.id}
    )
    for r in roles_list:
        if r in ALL_ROLES:
            db.session.execute(
                db.text('INSERT INTO user_roles (user_id, role) VALUES (:uid, :role)'),
                {'uid': user.id, 'role': r}
            )
    # keep legacy role column in sync (primary role = first in list)
    if roles_list:
        user.role = roles_list[0]

def _sync_managed_roles(user, managed_list):
    ManagerRole.query.filter_by(manager_id=user.id).delete()
    for r in managed_list:
        if r in ALL_ROLES:
            db.session.add(ManagerRole(manager_id=user.id, role=r))

@users_bp.route('/users')
@login_required
def index():
    if not current_user.is_admin:
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users/index.html', users=users, all_roles=ALL_ROLES)

@users_bp.route('/api/users', methods=['POST'])
@login_required
def api_create():
    if not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    d = request.json
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error': 'Email already in use'}), 400

    roles_list   = d.get('roles') or [d.get('role', 'developer')]
    primary_role = roles_list[0] if roles_list else 'developer'

    u = User(name=d['name'], email=d['email'],
             password_hash=generate_password_hash(d['password']),
             role=primary_role)
    db.session.add(u)
    db.session.flush()  # get u.id

    _sync_roles(u, roles_list)

    managed = d.get('managed_roles', [])
    if managed:
        _sync_managed_roles(u, managed)

    db.session.commit()
    return jsonify(u.to_dict()), 201

@users_bp.route('/api/users/<int:uid>', methods=['PUT'])
@login_required
def api_update(uid):
    if not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    u = User.query.get_or_404(uid)
    d = request.json
    if 'name'  in d: u.name  = d['name']
    if 'email' in d: u.email = d['email']
    if d.get('password'):
        u.password_hash = generate_password_hash(d['password'])

    if 'roles' in d:
        _sync_roles(u, d['roles'])
    elif 'role' in d:
        _sync_roles(u, [d['role']])
        u.role = d['role']

    if 'managed_roles' in d:
        _sync_managed_roles(u, d['managed_roles'])

    db.session.commit()
    return jsonify(u.to_dict())

@users_bp.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
def api_delete(uid):
    if not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    if uid == current_user.id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    u = User.query.get_or_404(uid)
    # Manually delete user_roles first
    db.session.execute(
        db.text('DELETE FROM user_roles WHERE user_id = :uid'),
        {'uid': uid}
    )
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})

@users_bp.route('/api/users/<int:uid>/password', methods=['PUT'])
@login_required
def api_update_password(uid):
    """Admin can update any user's password."""
    if not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    u = User.query.get_or_404(uid)
    d = request.json
    new_pw = d.get('password', '')
    if len(new_pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    u.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({'success': True})
