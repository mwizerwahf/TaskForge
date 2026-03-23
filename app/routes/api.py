from flask import Blueprint
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from app import socketio

api_bp = Blueprint('api', __name__)

@socketio.on('connect')
def on_connect():
    if current_user.is_authenticated:
        emit('connected', {'user': current_user.name, 'role': current_user.role})

@socketio.on('disconnect')
def on_disconnect():
    pass

@socketio.on('join_task')
def on_join(data):
    join_room(f"task_{data['task_id']}")

@socketio.on('leave_task')
def on_leave(data):
    leave_room(f"task_{data['task_id']}")
