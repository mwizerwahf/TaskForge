# PostgreSQL Schema Import Guide

## Quick Import

### Method 1: Using psql command line

```bash
# Import schema into existing database
psql -U taskforge_user -d taskforge_db -f schema.sql

# Or with password prompt
psql -U taskforge_user -d taskforge_db -W -f schema.sql

# Or specify host
psql -h localhost -U taskforge_user -d taskforge_db -f schema.sql
```

### Method 2: Using psql interactive mode

```bash
# Connect to database
psql -U taskforge_user -d taskforge_db

# Import schema
\i schema.sql

# Or with full path
\i /path/to/schema.sql

# Exit
\q
```

### Method 3: Using sudo (if postgres user)

```bash
sudo -u postgres psql -d taskforge_db -f schema.sql
```

---

## Complete Setup from Scratch

### Step 1: Create Database and User

```bash
# Connect as postgres superuser
sudo -u postgres psql

# Create database
CREATE DATABASE taskforge_db;

# Create user with password
CREATE USER taskforge_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE taskforge_db TO taskforge_user;

# Exit
\q
```

### Step 2: Import Schema

```bash
# Import schema
psql -U taskforge_user -d taskforge_db -f schema.sql
```

### Step 3: Verify Import

```bash
# Connect to database
psql -U taskforge_user -d taskforge_db

# List tables
\dt

# List views
\dv

# List functions
\df

# Describe a table
\d tasks

# Count records
SELECT COUNT(*) FROM users;

# Exit
\q
```

---

## Docker Import

### If using Docker Compose

```bash
# Copy schema to container
docker cp schema.sql taskforge_db:/tmp/schema.sql

# Import schema
docker-compose exec db psql -U taskforge_user -d taskforge_db -f /tmp/schema.sql
```

### Alternative: Mount volume

```yaml
# In docker-compose.yml
services:
  db:
    volumes:
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql
```

---

## Remote Server Import

```bash
# Import to remote PostgreSQL server
psql -h remote-host.com -p 5432 -U taskforge_user -d taskforge_db -f schema.sql

# With SSL
psql "host=remote-host.com port=5432 dbname=taskforge_db user=taskforge_user sslmode=require" -f schema.sql
```

---

## Troubleshooting

### Permission Denied

```bash
# Grant permissions to user
sudo -u postgres psql -d taskforge_db

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO taskforge_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO taskforge_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO taskforge_user;
\q
```

### Database Already Exists

```bash
# Drop and recreate (WARNING: This deletes all data!)
sudo -u postgres psql

DROP DATABASE IF EXISTS taskforge_db;
CREATE DATABASE taskforge_db;
GRANT ALL PRIVILEGES ON DATABASE taskforge_db TO taskforge_user;
\q

# Then import
psql -U taskforge_user -d taskforge_db -f schema.sql
```

### Tables Already Exist

The schema.sql file includes `DROP TABLE IF EXISTS` statements, so it will:
1. Drop existing tables (if any)
2. Recreate them with fresh schema
3. **WARNING**: This will delete all existing data!

To preserve data, backup first:

```bash
# Backup existing database
pg_dump -U taskforge_user taskforge_db > backup_before_import.sql

# Then import new schema
psql -U taskforge_user -d taskforge_db -f schema.sql
```

---

## Verification Queries

After import, verify everything is working:

```sql
-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE';

-- Check views
SELECT table_name 
FROM information_schema.views 
WHERE table_schema = 'public';

-- Check functions
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'public';

-- Check default admin user
SELECT id, name, email, role, created_at 
FROM users 
WHERE email = 'admin@taskforge.local';

-- Get task statistics
SELECT * FROM get_task_statistics();

-- Check active tasks view
SELECT * FROM v_active_tasks LIMIT 5;
```

---

## What Gets Created

### Tables (5)
- `users` - User accounts
- `tasks` - Task management
- `task_comments` - Task comments
- `attachments` - File attachments
- `activity_logs` - Audit trail

### Views (3)
- `v_active_tasks` - Active tasks with metadata
- `v_overdue_tasks` - Overdue tasks
- `v_user_workload` - User workload summary

### Functions (1)
- `get_task_statistics()` - Task statistics

### Triggers (1)
- `trigger_tasks_updated_at` - Auto-update timestamp

### Indexes
- 25+ indexes for optimal query performance

### Default Data
- 1 admin user (admin@taskforge.local / changeme)

---

## Post-Import Steps

1. **Change Admin Password**
   ```sql
   -- Connect to database
   psql -U taskforge_user -d taskforge_db
   
   -- Update password (use your application to hash it properly)
   -- Or login to application and change via UI
   ```

2. **Create Additional Users**
   ```sql
   -- Via application UI (recommended)
   -- Or manually (not recommended - use application)
   ```

3. **Configure Application**
   ```bash
   # Update .env file
   DATABASE_URL=postgresql://taskforge_user:your_password@localhost:5432/taskforge_db
   ```

4. **Test Connection**
   ```bash
   # From application directory
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('Connected!' if db.session.execute('SELECT 1').scalar() == 1 else 'Failed')"
   ```

---

## Backup and Restore

### Backup

```bash
# Full backup
pg_dump -U taskforge_user taskforge_db > taskforge_backup.sql

# Compressed backup
pg_dump -U taskforge_user taskforge_db | gzip > taskforge_backup.sql.gz

# Schema only
pg_dump -U taskforge_user -s taskforge_db > taskforge_schema_only.sql

# Data only
pg_dump -U taskforge_user -a taskforge_db > taskforge_data_only.sql
```

### Restore

```bash
# Restore from backup
psql -U taskforge_user -d taskforge_db < taskforge_backup.sql

# Restore from compressed
gunzip < taskforge_backup.sql.gz | psql -U taskforge_user -d taskforge_db
```

---

## Performance Tuning

After import, optimize for your workload:

```sql
-- Analyze tables for query planner
ANALYZE;

-- Vacuum to reclaim space
VACUUM;

-- Full vacuum (requires more time)
VACUUM FULL;

-- Reindex if needed
REINDEX DATABASE taskforge_db;
```

---

## Security Recommendations

1. **Change default admin password immediately**
2. **Use strong database password**
3. **Restrict database access by IP**
4. **Enable SSL for remote connections**
5. **Regular backups**
6. **Monitor activity logs**

---

## Support

If you encounter issues:
1. Check PostgreSQL logs: `/var/log/postgresql/`
2. Verify user permissions
3. Ensure PostgreSQL version is 13+
4. Check database connection settings

For application-specific issues, see DEPLOYMENT.md
