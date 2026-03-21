# 🔧 Fix for Vercel Import Error

## Problem
```
ImportError: cannot import name 'create_app' from 'app' (/var/task/app.py)
```

## Root Cause
Python is confusing `app.py` (entry point file) with `app/` (package directory) causing a circular import.

## Solution

### Files Changed
1. ✅ Created `wsgi.py` - New entry point for Vercel
2. ✅ Updated `vercel.json` - Points to `wsgi.py` instead of `app.py`

### What to Do

**Step 1: Commit the changes**
```bash
git add wsgi.py vercel.json
git commit -m "Fix: Use wsgi.py as Vercel entry point to avoid circular import"
git push origin main
```

**Step 2: Redeploy on Vercel**
Vercel will automatically redeploy when you push. Or manually:
1. Go to Vercel dashboard
2. Click your project
3. Click "Redeploy" on the latest deployment

**Step 3: Verify**
Visit your Vercel URL - it should now work!

---

## Environment Variables for Supabase

Make sure these are set in Vercel:

### Required
- `SECRET_KEY` - Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
- `DATABASE_URL` - From Supabase Settings → Database → Connection String
- `FLASK_ENV` - Set to: `production`
- `VERCEL` - Set to: `1`

### For File Storage (Optional)
- `SUPABASE_URL` - From Supabase Settings → API → Project URL
- `SUPABASE_ANON_KEY` - From Supabase Settings → API → anon public key
- `SUPABASE_SERVICE_KEY` - From Supabase Settings → API → service_role key

**Important:** 
- `SUPABASE_ANON_KEY` - For client-side operations (respects Row Level Security)
- `SUPABASE_SERVICE_KEY` - For server-side admin operations (bypasses RLS) - **KEEP SECRET!**

---

## How to Get Supabase Keys

1. Go to your Supabase project dashboard
2. Click **Settings** (gear icon in sidebar)
3. Click **API**
4. You'll see:
   - **Project URL** → Use as `SUPABASE_URL`
   - **Project API keys** section:
     - **anon public** → Use as `SUPABASE_ANON_KEY` (safe to expose)
     - **service_role** → Use as `SUPABASE_SERVICE_KEY` (NEVER expose to client!)

---

## Why Two Keys?

### SUPABASE_ANON_KEY (Public)
- Used for client-side operations
- Respects Row Level Security (RLS) policies
- Safe to expose in frontend code
- Limited permissions

### SUPABASE_SERVICE_KEY (Secret)
- Used for server-side admin operations
- **Bypasses all Row Level Security**
- Full database access
- **NEVER expose to client or commit to git**
- Use only in backend/serverless functions

---

## File Structure After Fix

```
taskforge/
├── app.py              # Original entry point (for local dev)
├── wsgi.py             # New entry point (for Vercel) ✅
├── vercel.json         # Updated to use wsgi.py ✅
├── config_vercel.py    # Updated with both Supabase keys ✅
└── app/
    ├── __init__.py
    └── ...
```

---

## Testing Locally

You can still use `app.py` for local development:

```bash
# Local development (with SocketIO)
python app.py

# Or test Vercel setup locally
python wsgi.py
```

---

## Next Steps After Deployment

1. ✅ Verify app loads at Vercel URL
2. ✅ Test login functionality
3. ✅ Test database operations
4. ✅ Check Vercel function logs for any errors
5. ✅ Test file uploads (if using Supabase Storage)

---

## Still Having Issues?

### Check Vercel Logs
1. Go to Vercel dashboard
2. Click your project
3. Click "Deployments"
4. Click latest deployment
5. Click "Functions" tab
6. Look for error messages

### Common Issues

**Database connection failed:**
- Verify `DATABASE_URL` is correct
- Check it starts with `postgresql://` (not `postgres://`)
- Verify Supabase project is active

**Module not found:**
- Check all dependencies are in `requirements_vercel.txt`
- Redeploy to reinstall dependencies

**Static files not loading:**
- Check `vercel.json` routes configuration
- Verify static files are in `app/static/`

---

## Summary

✅ **Fixed:** Circular import by using `wsgi.py` as entry point
✅ **Added:** Support for both Supabase keys (anon + service_role)
✅ **Updated:** Configuration files

**Action Required:** Commit and push changes, then Vercel will auto-deploy!
