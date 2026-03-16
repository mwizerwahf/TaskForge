# TaskForge Database Schema

## Overview

TaskForge uses a relational database with 5 main tables implementing a normalized schema for task management, user authentication, and activity tracking.

## Entity Relationship Diagram

```
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │◄─────┐
│ name            │      │
│ email (UNIQUE)  │      │
│ password_hash   │      │
│ role            │      │
│ created_at      │      │
└─────────────────┘      │
         ▲               │
         │               │
         │               │
    ┌────┴────┐          │
    │         │          │
    │         │          │
┌───┴─────────┴───┐      │
│     tasks       │      │
├─────────────────┤      │
│ id (PK)         │      │
│ title           │      │
│ description     │      │
│ assignee_id (FK)├──────┘
│ creator_id (FK) ├──────┐
│ status          │      │
│ priority        │      │
│ start_date      │      │
│ due_date        │      │
│ tags            │      │
│ created_at      │      │
│ updated_at      │      │
└─────────────────┘      │
         ▲               │
         │               │
    ┌────┼────┬──────────┘
    │    │    │
    │    │    │
┌───┴────┴────┴───┐
│ task_comments   │
├─────────────────┤
│ id (PK)         │
│ task_id (FK)    │
│ user_id (FK)    │
│ comment         │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│  attachments    │
├─────────────────┤
│ id (PK)         │
│ task_id (FK)    │
│ file_path       │
│ original_name   │
│ uploaded_by (FK)│
│ created_at      │
└─────────────────┘

┌─────────────────┐
│ activity_logs   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ action          │
│ task_id (FK)    │
│ timestamp       │
└─────────────────┘
```

---

## Table Definitions

### 1. `users`

Stores user accounts with authentication and role-based access control.

| Column         | Type          | Constraints                    | Description                          |
|----------------|---------------|--------------------------------|--------------------------------------|
| `id`           | INTEGER       | PRIMARY KEY, AUTO_INCREMENT    | Unique user identifier               |
| `name`         | VARCHAR(100)  | NOT NULL                       | User's full name                     |
| `email`        | VARCHAR(120)  | UNIQUE, NOT NULL               | User's email (login identifier)      |
| `password_hash`| VARCHAR(255)  | NOT NULL                       | Hashed password (PBKDF2-SHA256)      |
| `role`         | VARCHAR(20)   | NOT NULL, DEFAULT 'developer'  | User role (admin/manager/developer/viewer) |
| `created_at`   | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP      | Account creation timestamp           |

**Indexes:**
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`
- INDEX on `role` (for role-based queries)

**Roles:**
- `admin` - Full system access
- `manager` - Manage all tasks, view reports
- `developer` - Create/edit own tasks, update assigned tasks
- `viewer` - Read-only access

---

### 2. `tasks`

Core table storing all task information.

| Column         | Type          | Constraints                    | Description                          |
|----------------|---------------|--------------------------------|--------------------------------------|
| `id`           | INTEGER       | PRIMARY KEY, AUTO_INCREMENT    | Unique task identifier               |
| `title`        | VARCHAR(200)  | NOT NULL                       | Task title                           |
| `description`  | TEXT          | DEFAULT ''                     | Detailed task description            |
| `assignee_id`  | INTEGER       | FOREIGN KEY → users.id, NULL   | User assigned to task                |
| `creator_id`   | INTEGER       | FOREIGN KEY → users.id, NOT NULL | User who created task              |
| `status`       | VARCHAR(30)   | NOT NULL, DEFAULT 'not_started'| Task status                          |
| `priority`     | VARCHAR(20)   | NOT NULL, DEFAULT 'medium'     | Task priority level                  |
| `start_date`   | DATE          | NULL                           | Task start date                      |
| `due_date`     | DATE          | NULL                           | Task due date                        |
| `tags`         | VARCHAR(200)  | DEFAULT ''                     | Comma-separated tags                 |
| `created_at`   | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP      | Task creation timestamp              |
| `updated_at`   | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP, ON UPDATE | Last modification timestamp   |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `assignee_id` → `users.id`
- FOREIGN KEY on `creator_id` → `users.id`
- INDEX on `status` (for filtering)
- INDEX on `priority` (for filtering)
- INDEX on `assignee_id` (for user task queries)
- INDEX on `due_date` (for overdue queries)

**Status Values:**
- `not_started` - Task not yet begun
- `in_progress` - Task currently being worked on
- `blocked` - Task blocked by dependencies
- `completed` - Task finished

**Priority Values:**
- `low` - Low priority
- `medium` - Medium priority
- `high` - High priority
- `critical` - Critical priority

---

### 3. `task_comments`

Stores comments/discussions on tasks.

| Column         | Type          | Constraints                    | Description                          |
|----------------|---------------|--------------------------------|--------------------------------------|
| `id`           | INTEGER       | PRIMARY KEY, AUTO_INCREMENT    | Unique comment identifier            |
| `task_id`      | INTEGER       | FOREIGN KEY → tasks.id, NOT NULL | Associated task                    |
| `user_id`      | INTEGER       | FOREIGN KEY → users.id, NOT NULL | Comment author                     |
| `comment`      | TEXT          | NOT NULL                       | Comment content                      |
| `created_at`   | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP      | Comment creation timestamp           |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `task_id` → `tasks.id` (CASCADE DELETE)
- FOREIGN KEY on `user_id` → `users.id`
- INDEX on `task_id` (for task comment queries)

**Cascade Rules:**
- ON DELETE CASCADE for `task_id` (delete comments when task deleted)

---

### 4. `attachments`

Stores file attachments associated with tasks.

| Column         | Type          | Constraints                    | Description                          |
|----------------|---------------|--------------------------------|--------------------------------------|
| `id`           | INTEGER       | PRIMARY KEY, AUTO_INCREMENT    | Unique attachment identifier         |
| `task_id`      | INTEGER       | FOREIGN KEY → tasks.id, NOT NULL | Associated task                    |
| `file_path`    | VARCHAR(500)  | NOT NULL                       | Server file path (UUID-based)        |
| `original_name`| VARCHAR(255)  | NOT NULL                       | Original filename                    |
| `uploaded_by`  | INTEGER       | FOREIGN KEY → users.id, NOT NULL | User who uploaded file             |
| `created_at`   | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP      | Upload timestamp                     |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `task_id` → `tasks.id` (CASCADE DELETE)
- FOREIGN KEY on `uploaded_by` → `users.id`
- INDEX on `task_id` (for task attachment queries)

**Cascade Rules:**
- ON DELETE CASCADE for `task_id` (delete attachments when task deleted)

**Allowed File Types:**
- Images: png, jpg, jpeg, gif
- Documents: pdf, doc, docx, txt
- Archives: zip
- Logs: log

---

### 5. `activity_logs`

Audit trail of all system activities.

| Column         | Type          | Constraints                    | Description                          |
|----------------|---------------|--------------------------------|--------------------------------------|
| `id`           | INTEGER       | PRIMARY KEY, AUTO_INCREMENT    | Unique log entry identifier          |
| `user_id`      | INTEGER       | FOREIGN KEY → users.id, NOT NULL | User who performed action          |
| `action`       | VARCHAR(200)  | NOT NULL                       | Description of action                |
| `task_id`      | INTEGER       | FOREIGN KEY → tasks.id, NULL   | Related task (if applicable)         |
| `timestamp`    | TIMESTAMP     | DEFAULT CURRENT_TIMESTAMP      | Action timestamp                     |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY on `user_id` → `users.id`
- FOREIGN KEY on `task_id` → `tasks.id` (CASCADE DELETE)
- INDEX on `timestamp` (for chronological queries)
- INDEX on `task_id` (for task activity queries)

**Cascade Rules:**
- ON DELETE CASCADE for `task_id` (delete logs when task deleted)

---

## Relationships

### One-to-Many Relationships

1. **User → Tasks (as Creator)**
   - One user can create many tasks
   - `users.id` ← `tasks.creator_id`

2. **User → Tasks (as Assignee)**
   - One user can be assigned many tasks
   - `users.id` ← `tasks.assignee_id`

3. **Task → Comments**
   - One task can have many comments
   - `tasks.id` ← `task_comments.task_id`

4. **Task → Attachments**
   - One task can have many attachments
   - `tasks.id` ← `attachments.task_id`

5. **Task → Activity Logs**
   - One task can have many activity log entries
   - `tasks.id` ← `activity_logs.task_id`

6. **User → Comments**
   - One user can write many comments
   - `users.id` ← `task_comments.user_id`

7. **User → Activity Logs**
   - One user can have many activity log entries
   - `users.id` ← `activity_logs.user_id`

8. **User → Attachments**
   - One user can upload many attachments
   - `users.id` ← `attachments.uploaded_by`

---

## SQL Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'developer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    assignee_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    creator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'not_started',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    start_date DATE,
    due_date DATE,
    tags VARCHAR(200) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_creator ON tasks(creator_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Task comments table
CREATE TABLE task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_task ON task_comments(task_id);
CREATE INDEX idx_comments_user ON task_comments(user_id);

-- Attachments table
CREATE TABLE attachments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_task ON attachments(task_id);
CREATE INDEX idx_attachments_uploader ON attachments(uploaded_by);

-- Activity logs table
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(200) NOT NULL,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_user ON activity_logs(user_id);
CREATE INDEX idx_activity_task ON activity_logs(task_id);
CREATE INDEX idx_activity_timestamp ON activity_logs(timestamp);
```

---

## Common Queries

### Get all tasks assigned to a user
```sql
SELECT t.*, u.name as assignee_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
WHERE t.assignee_id = ?;
```

### Get overdue tasks
```sql
SELECT t.*, u.name as assignee_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
WHERE t.due_date < CURRENT_DATE
  AND t.status != 'completed';
```

### Get task with all comments
```sql
SELECT t.*, 
       json_agg(json_build_object(
           'id', c.id,
           'comment', c.comment,
           'author', u.name,
           'created_at', c.created_at
       )) as comments
FROM tasks t
LEFT JOIN task_comments c ON t.id = c.task_id
LEFT JOIN users u ON c.user_id = u.id
WHERE t.id = ?
GROUP BY t.id;
```

### Get user activity log
```sql
SELECT a.*, t.title as task_title
FROM activity_logs a
LEFT JOIN tasks t ON a.task_id = t.id
WHERE a.user_id = ?
ORDER BY a.timestamp DESC
LIMIT 50;
```

---

## Data Integrity Rules

1. **Referential Integrity**
   - All foreign keys enforced with constraints
   - Cascade deletes for dependent records

2. **Data Validation**
   - Email uniqueness enforced at database level
   - NOT NULL constraints on required fields
   - Default values for optional fields

3. **Audit Trail**
   - All activities logged in `activity_logs`
   - Timestamps on all records
   - User attribution for all actions

4. **Soft Deletes**
   - Tasks: Hard delete (cascade to comments, attachments, logs)
   - Users: Cannot delete if they have created tasks

---

## Performance Considerations

1. **Indexes**
   - All foreign keys indexed
   - Frequently queried columns indexed (status, priority, due_date)
   - Composite indexes for common query patterns

2. **Query Optimization**
   - Use of lazy loading for relationships
   - Pagination for large result sets
   - Connection pooling configured

3. **Maintenance**
   - Regular VACUUM ANALYZE on PostgreSQL
   - Index maintenance
   - Log rotation for activity_logs table

---

## Migration Notes

When migrating from SQLite to PostgreSQL:

1. **Auto-increment**: `SERIAL` instead of `AUTOINCREMENT`
2. **Boolean**: Use `BOOLEAN` type instead of `INTEGER`
3. **Timestamps**: Use `TIMESTAMP` with timezone support
4. **Text**: `TEXT` type has no length limit in PostgreSQL
5. **Indexes**: Create indexes after data migration for better performance

---

## Backup Strategy

1. **Full Backup**: Daily at 2 AM
2. **Incremental**: WAL archiving enabled
3. **Retention**: 7 days of daily backups
4. **Testing**: Monthly restore test

```bash
# Backup command
pg_dump -U taskforge_user taskforge_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore command
gunzip < backup_20240101.sql.gz | psql -U taskforge_user taskforge_db
```
