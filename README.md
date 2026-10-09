# YouTube Channel Analytics — Lite MVP

A single-channel analytics dashboard that lets a YouTube channel owner sign in with Google OAuth 2.0 and view key performance indicators and their top 5 videos.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 or later |
| Node.js | 18 or later |
| Google account | Required to create a Cloud project |

---

## Step 1 — Create a Google Cloud Project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com) and create a **new project** (e.g. `yt-analytics-mvp`).
2. In the sidebar, go to **APIs & Services → Library**.
   - Search for and **enable** `YouTube Data API v3`.
   - Search for and **enable** `YouTube Analytics API v2`.
3. Go to **APIs & Services → OAuth consent screen**.
   - Select **External** and click **Create**.
   - Fill in the App name (e.g. `YT Analytics MVP`) and your email.
   - Add the following scopes:
     - `openid`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
     - `https://www.googleapis.com/auth/youtube.readonly`
     - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - Add your Google account as a **Test user**.
4. Go to **APIs & Services → Credentials** → **Create Credentials → OAuth 2.0 Client ID**.
   - Application type: **Web application**.
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
   - Click **Create** and note your **Client ID** and **Client Secret**.

---

## Step 2 — Configure Environment Variables

### Backend

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
JWT_SECRET=<any-long-random-string>
FRONTEND_ORIGIN=http://localhost:5173
ENV=development
```

### Frontend

```bash
cp frontend/.env.example frontend/.env
```

`frontend/.env` only needs:

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## Step 3 — Start the Backend

```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**.  
Swagger UI is available at **http://localhost:8000/docs**.

---

## Step 4 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is now running at **http://localhost:5173**.

---

## Step 5 — First Run

1. Open **http://localhost:5173** in your browser.
2. Click **Sign in with Google** and complete the OAuth consent screen.
3. You will be redirected to the dashboard where KPI cards and the top 5 videos table will load with live data from the YouTube API.

> **Note:** The first login fetches live data from the YouTube API.  
> Subsequent same-day loads are served from the SQLite cache.

---

## Development Utilities

### Manually trigger the daily snapshot job

While `ENV=development`, a dev-only endpoint is available:

```
GET http://localhost:8000/admin/run-snapshot
```

This queues the snapshot job in the background and returns immediately. Check the backend logs to confirm DB rows were inserted.

---

## Architecture

```
[React + TS Frontend :5173]
        |
        | HTTP (axios)
        v
[FastAPI Backend :8000]
   |           |
   |           v
   |      [SQLite DB]  <-- daily snapshot cron (00:05 local time)
   |
   v
[Google OAuth 2.0]  -->  [YouTube Data API v3]
                    -->  [YouTube Analytics API v2]
```

---

## Known Limitations

- **Watch time data** requires channel owner OAuth — it is not available via the public YouTube Data API.
- **First login** always fetches live data from the YouTube API. The daily cron pre-caches subsequent loads.
- **YouTube Data API quota:** 10,000 units/day by default. Each dashboard load (live) costs ~102 units (`search.list` = 100, `channels.list` = 1, `videos.list` = 1).
- **Refresh token** is only returned by Google on the first consent screen. If you revoke access and reconnect, you must sign in again and grant consent to get a new refresh token.
- Tokens are stored in plaintext in SQLite — encryption at rest is out of scope for this MVP.
- No production deployment, HTTPS, or Docker configuration is included.
