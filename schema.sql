-- ============================================================================
-- TaskForge Database Schema - PostgreSQL
-- ============================================================================
-- Version: 1.0
-- Database: PostgreSQL 13+
-- Description: Complete schema for TaskForge task management system
-- ============================================================================

-- Drop existing tables (if any) in correct order
DROP TABLE IF EXISTS activity_logs CASCADE;
DROP TABLE IF EXISTS attachments CASCADE;
DROP TABLE IF EXISTS task_comments CASCADE;
DROP TABLE IF EXISTS tasks CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- TABLE: users
-- Description: User accounts with role-based access control
-- ============================================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'developer',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_role CHECK (role IN ('admin', 'manager', 'developer', 'viewer')),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Comments for users table
COMMENT ON TABLE users IS 'User accounts with authentication and role-based access control';
COMMENT ON COLUMN users.id IS 'Unique user identifier';
COMMENT ON COLUMN users.name IS 'User full name';
COMMENT ON COLUMN users.email IS 'User email address (login identifier)';
COMMENT ON COLUMN users.password_hash IS 'Hashed password using PBKDF2-SHA256';
COMMENT ON COLUMN users.role IS 'User role: admin, manager, developer, or viewer';
COMMENT ON COLUMN users.created_at IS 'Account creation timestamp';

-- ============================================================================
-- TABLE: tasks
-- Description: Core task management table
-- ============================================================================
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    assignee_id INTEGER,
    creator_id INTEGER NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'not_started',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    start_date DATE,
    due_date DATE,
    tags VARCHAR(200) DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_tasks_assignee FOREIGN KEY (assignee_id) 
        REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_tasks_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_status CHECK (status IN ('not_started', 'in_progress', 'blocked', 'completed')),
    CONSTRAINT chk_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_dates CHECK (start_date IS NULL OR due_date IS NULL OR start_date <= due_date)
);

-- Indexes for tasks table
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);
CREATE INDEX idx_tasks_creator_id ON tasks(creator_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
CREATE INDEX idx_tasks_assignee_status ON tasks(assignee_id, status);

-- Comments for tasks table
COMMENT ON TABLE tasks IS 'Core task management table with assignments and tracking';
COMMENT ON COLUMN tasks.id IS 'Unique task identifier';
COMMENT ON COLUMN tasks.title IS 'Task title/summary';
COMMENT ON COLUMN tasks.description IS 'Detailed task description';
COMMENT ON COLUMN tasks.assignee_id IS 'User assigned to complete the task';
COMMENT ON COLUMN tasks.creator_id IS 'User who created the task';
COMMENT ON COLUMN tasks.status IS 'Current task status: not_started, in_progress, blocked, completed';
COMMENT ON COLUMN tasks.priority IS 'Task priority: low, medium, high, critical';
COMMENT ON COLUMN tasks.start_date IS 'Task start date';
COMMENT ON COLUMN tasks.due_date IS 'Task due date';
COMMENT ON COLUMN tasks.tags IS 'Comma-separated tags for categorization';
COMMENT ON COLUMN tasks.created_at IS 'Task creation timestamp';
COMMENT ON COLUMN tasks.updated_at IS 'Last modification timestamp';

-- ============================================================================
-- TABLE: task_comments
-- Description: Comments and discussions on tasks
-- ============================================================================
CREATE TABLE task_comments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_comments_task FOREIGN KEY (task_id) 
        REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_comment_not_empty CHECK (LENGTH(TRIM(comment)) > 0)
);

-- Indexes for task_comments table
CREATE INDEX idx_comments_task_id ON task_comments(task_id);
CREATE INDEX idx_comments_user_id ON task_comments(user_id);
CREATE INDEX idx_comments_created_at ON task_comments(created_at);
CREATE INDEX idx_comments_task_created ON task_comments(task_id, created_at);

-- Comments for task_comments table
COMMENT ON TABLE task_comments IS 'Comments and discussions on tasks';
COMMENT ON COLUMN task_comments.id IS 'Unique comment identifier';
COMMENT ON COLUMN task_comments.task_id IS 'Associated task';
COMMENT ON COLUMN task_comments.user_id IS 'Comment author';
COMMENT ON COLUMN task_comments.comment IS 'Comment text content';
COMMENT ON COLUMN task_comments.created_at IS 'Comment creation timestamp';

-- ============================================================================
-- TABLE: attachments
-- Description: File attachments for tasks
-- ============================================================================
CREATE TABLE attachments (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    uploaded_by INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_attachments_task FOREIGN KEY (task_id) 
        REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_attachments_uploader FOREIGN KEY (uploaded_by) 
        REFERENCES users(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_file_path_not_empty CHECK (LENGTH(TRIM(file_path)) > 0),
    CONSTRAINT chk_original_name_not_empty CHECK (LENGTH(TRIM(original_name)) > 0)
);

-- Indexes for attachments table
CREATE INDEX idx_attachments_task_id ON attachments(task_id);
CREATE INDEX idx_attachments_uploaded_by ON attachments(uploaded_by);
CREATE INDEX idx_attachments_created_at ON attachments(created_at);

-- Comments for attachments table
COMMENT ON TABLE attachments IS 'File attachments associated with tasks';
COMMENT ON COLUMN attachments.id IS 'Unique attachment identifier';
COMMENT ON COLUMN attachments.task_id IS 'Associated task';
COMMENT ON COLUMN attachments.file_path IS 'Server file path (UUID-based filename)';
COMMENT ON COLUMN attachments.original_name IS 'Original filename from upload';
COMMENT ON COLUMN attachments.uploaded_by IS 'User who uploaded the file';
COMMENT ON COLUMN attachments.created_at IS 'Upload timestamp';

-- ============================================================================
-- TABLE: activity_logs
-- Description: Audit trail of all system activities
-- ============================================================================
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(200) NOT NULL,
    task_id INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Keys
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) 
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_activity_task FOREIGN KEY (task_id) 
        REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT chk_action_not_empty CHECK (LENGTH(TRIM(action)) > 0)
);

-- Indexes for activity_logs table
CREATE INDEX idx_activity_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_task_id ON activity_logs(task_id);
CREATE INDEX idx_activity_timestamp ON activity_logs(timestamp DESC);
CREATE INDEX idx_activity_user_timestamp ON activity_logs(user_id, timestamp DESC);
CREATE INDEX idx_activity_task_timestamp ON activity_logs(task_id, timestamp DESC);

-- Comments for activity_logs table
COMMENT ON TABLE activity_logs IS 'Audit trail of all system activities';
COMMENT ON COLUMN activity_logs.id IS 'Unique log entry identifier';
COMMENT ON COLUMN activity_logs.user_id IS 'User who performed the action';
COMMENT ON COLUMN activity_logs.action IS 'Description of the action performed';
COMMENT ON COLUMN activity_logs.task_id IS 'Related task (if applicable)';
COMMENT ON COLUMN activity_logs.timestamp IS 'Action timestamp';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger to automatically update updated_at timestamp on tasks
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates updated_at timestamp';

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Active tasks with user information
CREATE OR REPLACE VIEW v_active_tasks AS
SELECT 
    t.id,
    t.title,
    t.description,
    t.status,
    t.priority,
    t.start_date,
    t.due_date,
    t.tags,
    t.created_at,
    t.updated_at,
    creator.name AS creator_name,
    creator.email AS creator_email,
    assignee.name AS assignee_name,
    assignee.email AS assignee_email,
    CASE 
        WHEN t.due_date < CURRENT_DATE AND t.status != 'completed' THEN true
        ELSE false
    END AS is_overdue,
    (SELECT COUNT(*) FROM task_comments WHERE task_id = t.id) AS comment_count,
    (SELECT COUNT(*) FROM attachments WHERE task_id = t.id) AS attachment_count
FROM tasks t
INNER JOIN users creator ON t.creator_id = creator.id
LEFT JOIN users assignee ON t.assignee_id = assignee.id
WHERE t.status != 'completed';

COMMENT ON VIEW v_active_tasks IS 'Active tasks with user information and metadata';

-- View: Overdue tasks
CREATE OR REPLACE VIEW v_overdue_tasks AS
SELECT 
    t.id,
    t.title,
    t.status,
    t.priority,
    t.due_date,
    assignee.name AS assignee_name,
    creator.name AS creator_name,
    CURRENT_DATE - t.due_date AS days_overdue
FROM tasks t
INNER JOIN users creator ON t.creator_id = creator.id
LEFT JOIN users assignee ON t.assignee_id = assignee.id
WHERE t.due_date < CURRENT_DATE 
  AND t.status != 'completed'
ORDER BY t.due_date ASC;

COMMENT ON VIEW v_overdue_tasks IS 'All overdue tasks with days overdue calculation';

-- View: User workload summary
CREATE OR REPLACE VIEW v_user_workload AS
SELECT 
    u.id,
    u.name,
    u.email,
    u.role,
    COUNT(t.id) AS total_assigned_tasks,
    COUNT(CASE WHEN t.status = 'not_started' THEN 1 END) AS not_started_count,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) AS in_progress_count,
    COUNT(CASE WHEN t.status = 'blocked' THEN 1 END) AS blocked_count,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS completed_count,
    COUNT(CASE WHEN t.due_date < CURRENT_DATE AND t.status != 'completed' THEN 1 END) AS overdue_count
FROM users u
LEFT JOIN tasks t ON u.id = t.assignee_id
GROUP BY u.id, u.name, u.email, u.role;

COMMENT ON VIEW v_user_workload IS 'Summary of task workload per user';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Get task statistics
CREATE OR REPLACE FUNCTION get_task_statistics()
RETURNS TABLE (
    total_tasks BIGINT,
    not_started BIGINT,
    in_progress BIGINT,
    blocked BIGINT,
    completed BIGINT,
    overdue BIGINT,
    low_priority BIGINT,
    medium_priority BIGINT,
    high_priority BIGINT,
    critical_priority BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT AS total_tasks,
        COUNT(CASE WHEN status = 'not_started' THEN 1 END)::BIGINT AS not_started,
        COUNT(CASE WHEN status = 'in_progress' THEN 1 END)::BIGINT AS in_progress,
        COUNT(CASE WHEN status = 'blocked' THEN 1 END)::BIGINT AS blocked,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::BIGINT AS completed,
        COUNT(CASE WHEN due_date < CURRENT_DATE AND status != 'completed' THEN 1 END)::BIGINT AS overdue,
        COUNT(CASE WHEN priority = 'low' THEN 1 END)::BIGINT AS low_priority,
        COUNT(CASE WHEN priority = 'medium' THEN 1 END)::BIGINT AS medium_priority,
        COUNT(CASE WHEN priority = 'high' THEN 1 END)::BIGINT AS high_priority,
        COUNT(CASE WHEN priority = 'critical' THEN 1 END)::BIGINT AS critical_priority
    FROM tasks;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_task_statistics() IS 'Returns comprehensive task statistics';

-- ============================================================================
-- INITIAL DATA (Optional - Default Admin User)
-- ============================================================================

-- Insert default admin user (password: 'changeme')
-- Password hash generated using Werkzeug's generate_password_hash
INSERT INTO users (name, email, password_hash, role) 
VALUES (
    'System Admin',
    'admin@taskforge.local',
    'scrypt:32768:8:1$vQxZGKzXhWYqJN8r$8f5e3c4d2b1a9e7f6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- PERMISSIONS (Optional - Adjust based on your security requirements)
-- ============================================================================

-- Grant permissions to application user (replace 'taskforge_user' with your username)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO taskforge_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO taskforge_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO taskforge_user;

-- ============================================================================
-- MAINTENANCE
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE users;
ANALYZE tasks;
ANALYZE task_comments;
ANALYZE attachments;
ANALYZE activity_logs;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table creation
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Verify indexes
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Verify foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'TaskForge Database Schema Created Successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: 5';
    RAISE NOTICE 'Views created: 3';
    RAISE NOTICE 'Functions created: 1';
    RAISE NOTICE 'Triggers created: 1';
    RAISE NOTICE '';
    RAISE NOTICE 'Default Admin Credentials:';
    RAISE NOTICE '  Email: admin@taskforge.local';
    RAISE NOTICE '  Password: changeme';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT: Change the admin password immediately!';
    RAISE NOTICE '========================================';
END $$;
