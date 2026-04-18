# Web Task Scheduler Backend

Python backend for GreytHR attendance automation, scheduler control, emails, and the dashboard API.

## What Lives Here

- Playwright automation for login and attendance actions
- APScheduler jobs running in `Asia/Kolkata`
- Alert and success emails
- JSON API for dashboard auth, logs, schedule state, manual runs, and blocked dates

This backend no longer serves HTML dashboard pages. The UI lives entirely in the separate React frontend project.



## Backend Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python3 main.py
```

## Important Environment Variables

```env
TIMEZONE=Asia/Kolkata
DASHBOARD_PASSWORD=your-password
FLASK_SECRET_KEY=your-secret
FRONTEND_ORIGIN=http://localhost:5173
SESSION_COOKIE_SECURE=false
```

For production:

- Set `FRONTEND_ORIGIN` to your Netlify domain
- Set `SESSION_COOKIE_SECURE=true`

## API Endpoints

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/dashboard`
- `GET /api/logs`
- `POST /api/run`
- `POST /api/pause`
- `POST /api/blocked-dates`
- `DELETE /api/blocked-dates/<date>`
- `GET /api/health`

## Docker

```bash
docker compose up --build
```

Backend runs on port `5000`.
