from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User
from app import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def index():
    if not current_user.is_admin: abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users/index.html', users=users)

@users_bp.route('/api/users', methods=['POST'])
@login_required
def api_create():
    if not current_user.is_admin: return jsonify({'error':'Forbidden'}), 403
    d = request.json
    if User.query.filter_by(email=d['email']).first():
        return jsonify({'error':'Email already in use'}), 400
    u = User(name=d['name'], email=d['email'], password_hash=generate_password_hash(d['password']), role=d.get('role','developer'))
    db.session.add(u)
    db.session.commit()
    return jsonify(u.to_dict()), 201

@users_bp.route('/api/users/<int:uid>', methods=['PUT'])
@login_required
def api_update(uid):
    if not current_user.is_admin: return jsonify({'error':'Forbidden'}), 403
    u = User.query.get_or_404(uid)
    d = request.json
    if 'name' in d: u.name = d['name']
    if 'email' in d: u.email = d['email']
    if 'role' in d: u.role = d['role']
    if d.get('password'): u.password_hash = generate_password_hash(d['password'])
    db.session.commit()
    return jsonify(u.to_dict())

@users_bp.route('/api/users/<int:uid>', methods=['DELETE'])
@login_required
def api_delete(uid):
    if not current_user.is_admin: return jsonify({'error':'Forbidden'}), 403
    if uid == current_user.id: return jsonify({'error':'Cannot delete yourself'}), 400
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success':True})
