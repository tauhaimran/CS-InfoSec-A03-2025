# Free Hosting Guide for #4CK P07470 CTF Lab

This guide covers deploying your Flask CTF lab to free hosting platforms.

## Option 1: Render (Recommended - Easiest)

**Free Tier:** 750 hours/month, persistent disk storage, auto-deploy from Git

### Steps:

1. **Push to GitHub/GitLab:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Create Render Account:**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub/GitLab

3. **Create New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Settings:
     - **Name:** `ctf-lab` (or your choice)
     - **Environment:** `Python 3`
     - **Build Command:** `cd server && pip install -r requirements.txt && python init_db.py --csv data/students_sample.csv`
     - **Start Command:** `cd server && gunicorn app:app --bind 0.0.0.0:$PORT`
     - **Root Directory:** Leave empty (or set to `server` if you prefer)
     - **Python Version:** Render will auto-detect from `server/runtime.txt` (already included in repo)

4. **Environment Variables:**
   - `FLASK_APP=app`
   - `SECRET_KEY=<generate-a-random-string>` (important for sessions)
   - **Note:** Python version is set via `runtime.txt` (see below), not environment variable

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your app will be live at `https://your-app-name.onrender.com`

6. **Update CSRF Attack File:**
   - Edit `server/static/attacks/csrf_trap.html`
   - Change `http://localhost:5000` to your Render URL
   - Commit and push (auto-redeploys)

**Note:** Free tier spins down after 15 min inactivity. First request may take ~30s to wake up.

---

## Option 2: Railway

**Free Tier:** $5 credit/month (enough for small apps), persistent storage

### Steps:

1. **Push to GitHub** (same as Render)

2. **Create Railway Account:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

3. **New Project:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

4. **Configure:**
   - Railway auto-detects Python
   - Add these in "Variables" tab:
     - `FLASK_APP=app`
     - `SECRET_KEY=<random-string>`
   - In "Settings" → "Root Directory": Set to `server`

5. **Build & Deploy:**
   - Railway auto-builds
   - Add a "Run Command" in settings:
     ```
     python init_db.py --csv data/students_sample.csv && gunicorn app:app --bind 0.0.0.0:$PORT
     ```
   - Or use a `Procfile` in `server/`:
     ```
     web: python init_db.py --csv data/students_sample.csv && gunicorn app:app --bind 0.0.0.0:$PORT
     ```

6. **Get URL:**
   - Railway provides a `*.railway.app` URL
   - Update CSRF trap file with this URL

---

## Option 3: PythonAnywhere

**Free Tier:** Limited to `*.pythonanywhere.com` subdomain, 512MB storage

### Steps:

1. **Sign up:** [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files:**
   - Go to "Files" tab
   - Upload your `server/` folder contents to `/home/yourusername/ctf-lab/`

3. **Create Web App:**
   - "Web" tab → "Add a new web app"
   - Choose "Manual configuration" → Python 3.10
   - Set source code to `/home/yourusername/ctf-lab`

4. **Configure WSGI:**
   - Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:
     ```python
     import sys
     sys.path.insert(0, '/home/yourusername/ctf-lab')
     from app import app as application
     ```

5. **Initialize DB:**
   - Open "Consoles" → "Bash"
   - Run:
     ```bash
     cd /home/yourusername/ctf-lab
     python3 init_db.py --csv data/students_sample.csv
     ```

6. **Reload Web App:**
   - "Web" tab → Click "Reload"

---

## Option 4: Fly.io

**Free Tier:** 3 shared VMs, persistent volumes available

### Steps:

1. **Install Fly CLI:**
   ```bash
   # Windows: Use PowerShell
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Initialize:**
   ```bash
   cd server
   fly launch
   ```
   - Choose app name, region
   - Don't deploy yet

4. **Create `fly.toml` in `server/`:**
   ```toml
   app = "your-app-name"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = false
     auto_start_machines = true

   [[services]]
     protocol = "tcp"
     internal_port = 5000
   ```

5. **Create `Dockerfile` in `server/`:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt gunicorn
   COPY . .
   RUN python init_db.py --csv data/students_sample.csv
   CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
   ```

6. **Deploy:**
   ```bash
   fly deploy
   ```

---

## Important Notes for All Platforms

### 1. Install Gunicorn
Add to `server/requirements.txt`:
```
gunicorn==21.2.0
```

### 2. Update CSRF Attack URL
After deployment, edit `server/static/attacks/csrf_trap.html`:
```html
<!-- Change this line: -->
<form ... action="http://localhost:5000/csrf/update-email" ...>
<!-- To your deployed URL: -->
<form ... action="https://your-app.onrender.com/csrf/update-email" ...>
```

### 3. Database Persistence
- **Render/Railway:** SQLite files persist on disk (free tier)
- **PythonAnywhere:** Files persist in your home directory
- **Fly.io:** Use volumes for persistence (see Fly docs)

### 4. Environment Variables
Always set `SECRET_KEY` in production:
```python
# In app.py, change:
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
```

### 5. Admin Credentials
Change default admin password before going live:
- Edit `server/init_db.py` line 38, or
- Update `admins` table directly in SQLite after first deploy

---

## Quick Comparison

| Platform | Free Tier | Ease | Persistence | Best For |
|----------|-----------|------|------------|----------|
| **Render** | 750 hrs/mo | ⭐⭐⭐⭐⭐ | ✅ Yes | Beginners |
| **Railway** | $5 credit | ⭐⭐⭐⭐ | ✅ Yes | Quick deploys |
| **PythonAnywhere** | Limited | ⭐⭐⭐ | ✅ Yes | Python-focused |
| **Fly.io** | 3 VMs | ⭐⭐⭐ | ⚠️ Volumes | Advanced users |

---

## Troubleshooting

**"Database locked" errors:**
- SQLite can have issues with concurrent writes on some platforms
- Consider using PostgreSQL on paid tiers if scaling

**Static files not loading:**
- Ensure `static_folder="static"` in Flask app config
- Check file paths are relative to `server/` directory

**CSRF not working:**
- Verify the attack HTML file has the correct deployed URL
- Check CORS/cookie settings (Flask defaults should work)

**App crashes on startup:**
- Check build logs for missing dependencies
- Ensure `init_db.py` runs successfully during build
- Verify `FLASK_APP=app` environment variable is set

---

## Next Steps After Deployment

1. Test all CTF challenges work
2. Update `instructions.md` with deployed URL for students
3. Share admin credentials securely with instructors only
4. Monitor usage via admin panel (`/admin`)
5. Download DB backups regularly (`/admin/download-db`)

