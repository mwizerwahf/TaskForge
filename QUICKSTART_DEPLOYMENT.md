# TaskForge → Supabase + Vercel: Quick Start

## 🎯 What You'll Achieve

- Move database from SQLite/local PostgreSQL to Supabase (cloud PostgreSQL)
- Deploy Flask app on Vercel (serverless platform)
- Free hosting for both database and application

## ⏱️ Time Required: ~30 minutes

---

## 📋 Step-by-Step Guide

### PART 1: Supabase Database (10 min)

1. **Create Supabase Project**
   - Go to https://supabase.com → Sign up/Login
   - Click "New Project"
   - Name: `taskforge`
   - Generate strong password → **SAVE IT!**
   - Choose region → Create

2. **Setup Database**
   - Wait for project to initialize (~2 min)
   - Go to SQL Editor (left sidebar)
   - Click "New query"
   - Open your `schema.sql` file
   - Copy entire content → Paste in SQL Editor
   - Click "Run" (bottom right)
   - Verify: Go to "Table Editor" → Should see: user, task, comment, attachment, activity_log

3. **Get Connection Details**
   - Go to Settings (gear icon) → Database
   - Scroll to "Connection string"
   - Select "URI" tab
   - Copy the string (looks like):
     ```
     postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with your actual password
   - **SAVE THIS STRING!**

4. **Get API Keys**
   - Go to Settings → API
   - Copy "Project URL" → **SAVE IT!**
   - Copy "anon public" key → **SAVE IT!**

---

### PART 2: Prepare Your Code (10 min)

1. **Update Files**
   ```bash
   # Run the migration script
   python migrate_to_vercel.py
   ```

2. **Verify New Files Exist**
   - ✅ `vercel.json`
   - ✅ `config_vercel.py`
   - ✅ `requirements_vercel.txt`
   - ✅ `.env.vercel`

3. **Generate Secret Key**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output → **SAVE IT!**

4. **Push to Git**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

---

### PART 3: Deploy on Vercel (10 min)

1. **Create Vercel Account**
   - Go to https://vercel.com
   - Sign up with GitHub/GitLab/Bitbucket

2. **Import Project**
   - Click "Add New..." → "Project"
   - Select your TaskForge repository
   - Click "Import"

3. **Configure Environment Variables**
   Click "Environment Variables" and add:

   | Name | Value |
   |------|-------|
   | `SECRET_KEY` | (from step 2.3) |
   | `DATABASE_URL` | (from step 1.3) |
   | `FLASK_ENV` | `production` |
   | `VERCEL` | `1` |
   | `SUPABASE_URL` | (from step 1.4) |
   | `SUPABASE_KEY` | (from step 1.4) |

4. **Configure Build Settings**
   - Framework Preset: **Other**
   - Build Command: `pip install -r requirements_vercel.txt`
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements_vercel.txt`

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes
   - You'll get a URL: `https://taskforge-xxxxx.vercel.app`

6. **Test Your App**
   - Visit the URL
   - Login: `admin@taskforge.local` / `changeme`
   - Create a test task
   - ✅ Success!

---

## 🎉 You're Done!

Your TaskForge app is now running on:
- **Database**: Supabase (PostgreSQL)
- **Application**: Vercel (Serverless)
- **Cost**: $0 (Free tier)

---

## ⚠️ Important Notes

### What Works
✅ User authentication
✅ Task CRUD operations
✅ Reports generation
✅ Dashboard analytics
✅ User management
✅ Comments

### What's Disabled
❌ Real-time updates (WebSockets not supported on Vercel)
❌ Kanban drag-and-drop sync (still works, but no real-time)
❌ Persistent file uploads (use /tmp or implement Supabase Storage)

### Workarounds
- **Real-time**: Use page refresh or implement polling
- **File uploads**: Implement Supabase Storage (see full guide)
- **Cold starts**: First request after inactivity is slow (~3-5s)

---

## 🔧 Troubleshooting

### "Can't connect to database"
- Check DATABASE_URL in Vercel environment variables
- Ensure it starts with `postgresql://` (not `postgres://`)
- Verify password is correct

### "500 Internal Server Error"
- Go to Vercel → Your Project → Deployments → Click latest → Functions tab
- Check logs for errors
- Verify all environment variables are set

### "Static files not loading"
- Check `vercel.json` exists in root
- Verify routes configuration

### "Tables don't exist"
- Go to Supabase → SQL Editor
- Run your schema.sql again
- Check Table Editor to verify

---

## 📚 Full Documentation

- **Complete Guide**: `VERCEL_SUPABASE_DEPLOYMENT.md`
- **Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **Environment Variables**: `.env.vercel`

---

## 🆘 Need Help?

1. Check Vercel logs: Project → Deployments → Functions
2. Check Supabase logs: Project → Logs → Postgres Logs
3. Review full deployment guide
4. Check Vercel docs: https://vercel.com/docs/frameworks/flask
5. Check Supabase docs: https://supabase.com/docs

---

## 🚀 Next Steps

1. **Change admin password** (important!)
2. **Add custom domain** (Vercel Settings → Domains)
3. **Set up monitoring** (Sentry, LogRocket)
4. **Configure backups** (Supabase automatic backups)
5. **Add more users**

---

## 💰 Cost Breakdown

**Free Tier Limits:**
- Supabase: 500MB database, 1GB storage, 2GB bandwidth
- Vercel: 100GB bandwidth, 100 serverless function executions/day

**When to upgrade:**
- Supabase Pro ($25/mo): 8GB database, 100GB storage
- Vercel Pro ($20/mo): Unlimited bandwidth, better performance

---

## 🔄 Rollback

If something goes wrong:

```bash
# Restore original app/__init__.py
cp app/__init__.py.backup app/__init__.py

# Revert to local database
# Update .env: DATABASE_URL=sqlite:///taskforge.db

# Run locally
python app.py
```

---

**Good luck with your deployment! 🎊**
