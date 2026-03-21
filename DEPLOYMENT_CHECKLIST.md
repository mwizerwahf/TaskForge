# Quick Deployment Checklist

## Supabase Setup (5 minutes)

- [ ] Create Supabase account at https://supabase.com
- [ ] Create new project (name: taskforge)
- [ ] Save database password
- [ ] Copy connection string from Settings → Database
- [ ] Go to SQL Editor
- [ ] Run schema from `schema.sql` file
- [ ] Verify tables created in Table Editor
- [ ] Get API keys from Settings → API (URL + anon key)

## Code Preparation (10 minutes)

- [ ] Copy `app/__init___vercel.py` to `app/__init__.py` (backup original first)
- [ ] Ensure `vercel.json` exists in root
- [ ] Ensure `config_vercel.py` exists in root
- [ ] Ensure `requirements_vercel.txt` exists in root
- [ ] Commit and push to Git repository

## Vercel Deployment (5 minutes)

- [ ] Create Vercel account at https://vercel.com
- [ ] Click "Add New Project"
- [ ] Import your Git repository
- [ ] Add environment variables:
  ```
  SECRET_KEY=<generate-new-secret>
  DATABASE_URL=<supabase-connection-string>
  FLASK_ENV=production
  VERCEL=1
  SUPABASE_URL=<from-supabase-api-settings>
  SUPABASE_KEY=<from-supabase-api-settings>
  ```
- [ ] Set build command: `pip install -r requirements_vercel.txt`
- [ ] Click Deploy
- [ ] Wait for deployment to complete
- [ ] Visit provided URL
- [ ] Test login with admin@taskforge.local / changeme

## Post-Deployment

- [ ] Change admin password
- [ ] Test creating tasks
- [ ] Test reports generation
- [ ] Monitor Vercel function logs
- [ ] Monitor Supabase database logs

## Generate SECRET_KEY

Run locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Connection String Format

```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

Replace:
- `[PASSWORD]` with your database password
- `[PROJECT-REF]` with your Supabase project reference

## Troubleshooting

**Can't connect to database:**
- Check DATABASE_URL format (must start with `postgresql://`)
- Verify password is correct
- Check Supabase project is active

**500 errors:**
- Check Vercel function logs
- Verify all environment variables are set
- Check database tables exist

**Static files not loading:**
- Verify `vercel.json` routes configuration
- Check file paths in templates

## Important Notes

⚠️ **WebSocket features (real-time updates) are disabled on Vercel**
- Kanban board won't sync in real-time
- Comments won't appear instantly
- Use page refresh to see updates

⚠️ **File uploads use /tmp (temporary storage)**
- Files are deleted after function execution
- Implement Supabase Storage for persistent uploads

⚠️ **Cold starts**
- First request after inactivity may be slow (3-5 seconds)
- Subsequent requests are fast
