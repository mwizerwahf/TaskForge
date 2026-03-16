# TaskForge

Enterprise-grade task management platform built with Flask, featuring real-time collaboration, role-based access control, and comprehensive reporting capabilities.

## Architecture Overview

TaskForge is a full-stack web application implementing a modern MVC architecture with real-time bidirectional communication. The system leverages Flask's modular blueprint structure for maintainability and scalability.

### Core Components

- **Backend**: Flask 3.x with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL-ready (production)
- **Real-time Layer**: Flask-SocketIO with WebSocket transport
- **Authentication**: Flask-Login with session-based auth
- **Frontend**: Server-side rendered templates with progressive enhancement
- **State Management**: Event-driven architecture with SocketIO broadcasts

## Getting Started

### Prerequisites

- Python 3.9+
- pip or poetry for dependency management
- Virtual environment (recommended)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd taskforge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python app.py
```

### Initial Setup

### Configuration

Edit `config.py` to customize:

```python
SECRET_KEY          # Session encryption key (use secrets.token_hex(32))
SQLALCHEMY_DATABASE_URI  # Database connection string
UPLOAD_FOLDER       # File attachment storage path
MAX_CONTENT_LENGTH  # Upload size limit
```

For production, use environment variables:

```bash
export FLASK_ENV=production
export SECRET_KEY=<your-secret-key>
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

## Features

### Access Control

Four-tier role-based permission system:

| Role      | Permissions |
|-----------|-------------|
| **Admin** | Full system access, user management, all task operations |
| **Manager** | Create/edit/delete all tasks, view all reports, assign tasks |
| **Developer** | Create/edit own tasks, update assigned tasks, comment, upload files |
| **Viewer** | Read-only access to tasks and reports |

### Task Management

- **CRUD Operations**: Full lifecycle management with audit trails
- **Assignment System**: Multi-user task delegation with notification
- **Status Workflow**: Not Started → In Progress → Blocked → Completed
- **Priority Levels**: Low, Medium, High, Critical
- **Tagging System**: Flexible categorization with comma-separated tags
- **File Attachments**: Secure upload with type validation
- **Comments**: Threaded discussion per task
- **Activity Logging**: Complete audit trail of all changes

### Visualization Modes

1. **List View**: Filterable table with advanced search and sorting
2. **Kanban Board**: Drag-and-drop interface with real-time sync
3. **Calendar View**: FullCalendar integration with date-based filtering
4. **Timeline View**: Gantt-style visualization for project planning

### Real-time Collaboration

WebSocket-based event system ensures instant updates across all connected clients:

- Task creation/updates broadcast to all users
- Status changes reflected immediately on Kanban boards
- Comment notifications in real-time
- Connection status indicator

### Reporting

PDF report generation with ReportLab:

- Daily task summaries per user
- Status distribution analytics
- Priority breakdown
- Overdue task alerts
- Role-based report access control

## Project Structure

```
taskforge/
├── app.py                      # Application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── taskforge.db               # SQLite database (auto-generated)
│
└── app/
    ├── __init__.py            # Application factory, DB initialization
    │
    ├── models/
    │   ├── user.py            # User model, authentication
    │   └── task.py            # Task, Comment, Attachment, ActivityLog models
    │
    ├── routes/
    │   ├── auth.py            # Authentication endpoints
    │   ├── tasks.py           # Task CRUD + REST API
    │   ├── users.py           # User management (admin only)
    │   ├── reports.py         # PDF generation
    │   └── api.py             # SocketIO event handlers
    │
    ├── templates/
    │   ├── base.html          # Base layout with navigation
    │   ├── auth/
    │   │   └── login.html     # Login page
    │   ├── dashboard/
    │   │   └── index.html     # Analytics dashboard
    │   ├── tasks/
    │   │   ├── index.html     # List view
    │   │   ├── board.html     # Kanban board
    │   │   ├── calendar.html  # Calendar view
    │   │   ├── timeline.html  # Timeline/Gantt view
    │   │   └── detail.html    # Task detail page
    │   ├── users/
    │   │   └── index.html     # User management
    │   └── reports/
    │       └── index.html     # Report generation
    │
    ├── static/
    │   ├── css/
    │   │   └── style.css      # Application styles
    │   └── js/
    │       └── pages.js       # Client-side logic
    │
    └── uploads/               # File attachment storage
```

## Technology Stack

### Backend

- **Flask 3.x**: Lightweight WSGI web framework
- **SQLAlchemy 2.x**: ORM with migration support via Alembic
- **Flask-Login**: Session management and authentication
- **Flask-SocketIO**: WebSocket implementation
- **Flask-Migrate**: Database schema versioning
- **ReportLab**: PDF generation engine

### Frontend

- **Bootstrap 5**: Responsive UI framework
- **Chart.js 4**: Data visualization
- **FullCalendar 6**: Calendar component
- **SortableJS**: Drag-and-drop functionality
- **Socket.IO Client**: Real-time communication

### Database

- **SQLite**: Development and small deployments
- **PostgreSQL**: Recommended for production (connection string compatible)

## API Endpoints

### REST API

```
GET    /api/tasks                    # List all tasks (with filters)
POST   /api/tasks                    # Create new task
GET    /api/tasks/<id>               # Get task details
PUT    /api/tasks/<id>               # Update task
DELETE /api/tasks/<id>               # Delete task
PATCH  /api/tasks/<id>/status        # Update task status

GET    /api/tasks/<id>/comments      # Get task comments
POST   /api/tasks/<id>/comments      # Add comment
POST   /api/tasks/<id>/upload        # Upload attachment

GET    /api/dashboard/stats          # Dashboard analytics
GET    /api/calendar/tasks           # Calendar events
GET    /api/timeline/tasks           # Timeline data

GET    /api/users                    # List users (admin)
POST   /api/users                    # Create user (admin)
PUT    /api/users/<id>               # Update user (admin)
DELETE /api/users/<id>               # Delete user (admin)
```

### WebSocket Events

```javascript
// Client → Server
socket.emit('join_task', {task_id: 123})

// Server → Client
socket.on('task_created', (data) => {...})
socket.on('task_updated', (data) => {...})
socket.on('task_deleted', (data) => {...})
socket.on('task_status_changed', (data) => {...})
socket.on('comment_added', (data) => {...})
```

## Security Considerations

### Authentication

- Session-based authentication with secure cookies
- Password hashing using Werkzeug's PBKDF2-SHA256
- CSRF protection on all forms
- Login rate limiting recommended for production

### Authorization

- Decorator-based route protection (`@login_required`)
- Function-level permission checks (`can_edit()`)
- Role-based access control enforced at API level

### File Uploads

- Whitelist-based file type validation
- Secure filename sanitization
- Configurable size limits
- Isolated storage directory

### Production Hardening

```python
# config.py - Production settings
SECRET_KEY = os.environ.get('SECRET_KEY')  # Never commit secrets
SESSION_COOKIE_SECURE = True               # HTTPS only
SESSION_COOKIE_HTTPONLY = True             # No JS access
SESSION_COOKIE_SAMESITE = 'Lax'            # CSRF protection
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
```

## Deployment

### Production Server

Use a production WSGI server (not Flask's development server):

```bash
# Using Gunicorn
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 app:app

# Using uWSGI
pip install uwsgi
uwsgi --http :8000 --gevent 1000 --http-websockets --master --wsgi-file app.py --callable app
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name taskforge.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Migration

For production, migrate to PostgreSQL:

```python
# config.py
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'postgresql://user:password@localhost:5432/taskforge'
```

Run migrations:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Environment Variables

```bash
# .env (never commit this file)
FLASK_ENV=production
SECRET_KEY=<generate-with-secrets.token_hex(32)>
DATABASE_URL=postgresql://user:pass@host:5432/taskforge
UPLOAD_FOLDER=/var/www/taskforge/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:8000", "app:app"]
```

## Performance Optimization

### Database

- Add indexes on frequently queried columns (status, assignee_id, due_date)
- Use connection pooling for PostgreSQL
- Implement query result caching for dashboard stats
- Consider read replicas for high-traffic deployments

### Caching

```python
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'redis'})
cache.init_app(app)

@cache.cached(timeout=300)
def get_dashboard_stats():
    # Expensive query
    pass
```

### Static Assets

- Enable gzip compression in Nginx
- Use CDN for Bootstrap/Chart.js
- Implement asset versioning for cache busting
- Minify CSS/JS in production

## Monitoring & Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('taskforge.log', maxBytes=10000000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
```

### Health Check Endpoint

```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'db': db.session.execute('SELECT 1').scalar() == 1}
```

## Testing

```bash
# Run tests
pytest tests/

# Coverage report
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Specify your license here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@taskforge.local
