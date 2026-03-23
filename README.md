# TaskForge

Task management platform with real-time collaboration, role-based access control, and reporting.

## Tech Stack

- **Backend**: Flask 3.x + SQLAlchemy
- **Database**: SQLite / PostgreSQL
- **Real-time**: Flask-SocketIO
- **Auth**: Flask-Login
- **Frontend**: Bootstrap 5, Chart.js, FullCalendar

## Quick Start

### Docker (Recommended)

```bash
docker-compose up -d
# Import database schema (contact admin for schema.sql)
docker exec -i taskforge-db psql -U taskforge -d taskforge < schema.sql
```

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for details.

### Local Development

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py
```

Access at `http://localhost:5000`

Default login: `admin@taskforge.local` / `changeme`

## Configuration

Create `.env` file:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///taskforge.db
FLASK_ENV=development
```

## Features

**Roles**: Admin, Manager, Developer, Viewer

**Task Management**:
- CRUD operations with audit trails
- Status workflow: Not Started → In Progress → Blocked → Completed
- Priority levels: Low, Medium, High, Critical
- File attachments and comments
- Multi-user assignment

**Views**:
- List view with filters
- Kanban board (drag-and-drop)
- Calendar view
- Timeline/Gantt view

**Real-time**: WebSocket updates for tasks, status changes, and comments

**Reports**: PDF generation with task summaries and analytics

## Structure

```
taskforge/
├── wsgi.py              # Entry point
├── config.py            # Configuration
├── requirements.txt     # Dependencies
└── app/
    ├── __init__.py      # App factory
    ├── models/          # User, Task models
    ├── routes/          # Auth, Tasks, Users, Reports, API
    ├── templates/       # HTML templates
    ├── static/          # CSS, JS
    └── uploads/         # File storage
```



## API

**REST**: `/api/tasks`, `/api/users`, `/api/dashboard/stats`, `/api/calendar/tasks`

**WebSocket**: `task_created`, `task_updated`, `task_deleted`, `task_status_changed`, `comment_added`

## Security

- Session-based auth with password hashing
- CSRF protection
- Role-based access control
- Secure file uploads with validation

## Production

```bash
# Using Gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8000 wsgi:app
```

For PostgreSQL:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/taskforge
```

## License

MIT
