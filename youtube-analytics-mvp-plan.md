# YouTube Channel Analytics — Lite MVP Plan

## Overview

Build a Lite MVP web application that lets a YouTube channel owner sign in with Google OAuth 2.0,
authorize access to their private YouTube Analytics data, and view a single Overview Dashboard
showing key performance indicators (KPIs) and their top 5 videos.

**Stack:**
- Backend: Python 3.11+ · FastAPI · SQLite (via SQLAlchemy + aiosqlite)
- Frontend: React 18 · TypeScript · Vite · Tailwind CSS · Recharts
- Auth: Google OAuth 2.0 (authorization code flow) · JWT session tokens
- YouTube APIs: YouTube Data API v3 · YouTube Analytics API v2
- Runtime: localhost (backend on port 8000, frontend on port 5173)

**Scope:**
- Login page with Google OAuth sign-in
- Overview Dashboard with 4 KPI cards and a Top 5 Videos table
- Daily snapshot cron job to persist channel data to SQLite
- No AI/ML, no multi-channel support, no deployment configuration

**Non-Goals:**
- Production deployment / HTTPS / Docker
- Multi-user / team workspaces
- Video-level deep-dive pages
- Export / reporting features
- Alerts / notifications

---

## Architecture

```
[React + TS Frontend :5173]
        |
        | HTTP (fetch / axios)
        v
[FastAPI Backend :8000]
   |           |
   |           v
   |      [SQLite DB]  <-- daily snapshot cron
   |
   v
[Google OAuth 2.0]  -->  [YouTube Data API v3]
                    -->  [YouTube Analytics API v2]
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffolding

**Status:** [ ] pending

**Intent:**
Create the monorepo folder structure, install dependencies, and configure environment
variables so both backend and frontend can start cleanly on localhost.

**Expected Outcomes:**
- `/backend` folder with FastAPI app skeleton running on `http://localhost:8000`
- `/frontend` folder with Vite + React + TypeScript skeleton running on `http://localhost:5173`
- `.env.example` files in both `/backend` and `/frontend` documenting required secrets
- CORS configured on FastAPI to allow requests from `http://localhost:5173`
- Both apps start without errors using a single README instruction

**Todo List:**
1. Create root folders: `backend/`, `frontend/`
2. Backend: initialise Python virtual environment, create `requirements.txt` with:
   `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `aiosqlite`, `python-jose[cryptography]`,
   `httpx`, `google-auth-oauthlib`, `google-api-python-client`, `apscheduler`, `python-dotenv`
3. Backend: create `backend/app/main.py` with a minimal FastAPI app, CORS middleware,
   and a `/health` endpoint returning `{ "status": "ok" }`
4. Backend: create `backend/.env.example` with keys:
   `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`, `FRONTEND_ORIGIN`
5. Frontend: scaffold with `npm create vite@latest frontend -- --template react-ts`
6. Frontend: install `axios`, `recharts`, `react-router-dom`, `tailwindcss`, `@tailwindcss/vite`
7. Frontend: configure Tailwind — add `@tailwindcss/vite` plugin to `vite.config.ts`,
   add `@import "tailwindcss"` to `src/index.css`
8. Frontend: create `frontend/.env.example` with key: `VITE_API_BASE_URL=http://localhost:8000`
8. Root: create `README.md` with setup and run instructions for both apps

**Relevant Context:**
- FastAPI CORS middleware: `fastapi.middleware.cors.CORSMiddleware`
- Vite proxy is NOT needed; frontend will call backend directly via `VITE_API_BASE_URL`

---

### Sub-Task 2 — SQLite Database & Models

**Status:** [ ] pending

**Intent:**
Define the SQLite schema using SQLAlchemy ORM models to store OAuth tokens and daily
channel/video snapshots. This is the persistence layer the cron job and API both depend on.

**Expected Outcomes:**
- `backend/app/database.py` — async SQLAlchemy engine + session factory for SQLite
- `backend/app/models.py` — three ORM models: `User`, `ChannelSnapshot`, `VideoSnapshot`
- Tables are created automatically on app startup via `create_all`

**Todo List:**
1. Create `backend/app/database.py`:
   - Async SQLAlchemy engine pointed at `./youtube_analytics.db`
   - `AsyncSession` factory exported as `get_db` dependency
2. Create `backend/app/models.py` with three tables:

   **User**
   - `id` (PK, UUID)
   - `google_id` (unique string)
   - `email` (string)
   - `name` (string)
   - `access_token` (string) — encrypted at rest is out of scope for MVP
   - `refresh_token` (string)
   - `token_expiry` (datetime)
   - `created_at` (datetime)

   **ChannelSnapshot**
   - `id` (PK, UUID)
   - `user_id` (FK → User)
   - `snapshot_date` (date) — one row per day
   - `subscriber_count` (integer)
   - `total_views` (integer)
   - `total_watch_time_minutes` (integer)
   - `video_count` (integer)

   **VideoSnapshot**
   - `id` (PK, UUID)
   - `user_id` (FK → User)
   - `snapshot_date` (date)
   - `video_id` (string) — YouTube video ID
   - `title` (string)
   - `thumbnail_url` (string)
   - `views` (integer)
   - `likes` (integer)
   - `comments` (integer)
   - `published_at` (datetime)

3. Wire `Base.metadata.create_all` into FastAPI startup event in `main.py`

**Relevant Context:**
- Use `sqlalchemy.ext.asyncio` throughout — no sync sessions
- `snapshot_date` + `user_id` should have a composite unique constraint on both snapshot tables
  to prevent duplicate daily inserts

---

### Sub-Task 3 — Google OAuth 2.0 Authentication

**Status:** [ ] pending

**Intent:**
Implement the Google OAuth 2.0 authorization code flow so a channel owner can log in,
grant YouTube API scopes, and receive a JWT session token the frontend stores locally.

**Expected Outcomes:**
- `GET /auth/google/login` — redirects browser to Google consent screen
- `GET /auth/google/callback` — exchanges code for tokens, upserts User in DB, returns JWT
- `GET /auth/me` — protected endpoint returning the logged-in user's profile
- `POST /auth/logout` — client-side only (frontend clears JWT); endpoint optional
- Frontend Login page has a "Sign in with Google" button that starts the flow

**Todo List:**
1. Register OAuth 2.0 credentials in Google Cloud Console (new project setup):
   - Go to https://console.cloud.google.com → create a new project (e.g. "yt-analytics-mvp")
   - Enable **YouTube Data API v3** and **YouTube Analytics API v2** under "APIs & Services → Library"
   - Go to "APIs & Services → OAuth consent screen" → set as External, fill app name + email
   - Go to "APIs & Services → Credentials" → Create OAuth 2.0 Client ID (type: Web Application)
   - Authorized redirect URI: `http://localhost:8000/auth/google/callback`
   - Required scopes: `openid email profile`,
     `https://www.googleapis.com/auth/youtube.readonly`,
     `https://www.googleapis.com/auth/yt-analytics.readonly`
   - Copy Client ID and Client Secret into `backend/.env`
   - Document ALL above steps in `README.md` (they are a one-time manual setup step)
2. Create `backend/app/routers/auth.py`:
   - `GET /auth/google/login`: build Google OAuth URL using `google-auth-oauthlib`,
     redirect user
   - `GET /auth/google/callback`: exchange `code` for tokens, call Google UserInfo endpoint
     to get `google_id` + `email` + `name`, upsert User row, issue signed JWT,
     redirect to `http://localhost:5173/dashboard?token=<jwt>`
3. Create `backend/app/auth.py` utilities:
   - `create_jwt(user_id)` — signs a JWT with `JWT_SECRET`, 7-day expiry
   - `decode_jwt(token)` — validates and decodes; raises `HTTPException 401` on failure
   - `get_current_user(token)` — FastAPI dependency that returns the User ORM object
4. Frontend: create `src/pages/LoginPage.tsx` with a button that calls
   `window.location.href = VITE_API_BASE_URL + "/auth/google/login"`
5. Frontend: create `src/pages/CallbackPage.tsx` — reads `?token=` from URL,
   stores JWT in `localStorage`, redirects to `/dashboard`
6. Frontend: create `src/hooks/useAuth.ts` — reads JWT from localStorage,
   calls `GET /auth/me` to hydrate user state; exposes `user`, `isLoading`, `logout`

**Relevant Context:**
- Use `python-jose` for JWT signing/verification on the backend
- The JWT payload needs only `sub` (user UUID) and `exp`
- Google's token response includes `access_token`, `refresh_token`, `expires_in`
- Store `refresh_token` — it is only returned on first consent; needed for cron job

---

### Sub-Task 4 — YouTube API Data Fetching Service

**Status:** [ ] pending

**Intent:**
Create a backend service layer that fetches channel statistics and top video data from
YouTube Data API v3 and YouTube Analytics API v2 using the stored OAuth tokens.

**Expected Outcomes:**
- `backend/app/services/youtube.py` — two fetch functions:
  1. `fetch_channel_stats(user)` → returns subscriber count, total views, video count
  2. `fetch_top_videos(user, limit=5)` → returns list of video objects with views, likes,
     comments, title, thumbnail
- `backend/app/services/analytics.py` — one fetch function:
  1. `fetch_watch_time(user)` → returns total watch time in minutes for the last 28 days
- Token refresh logic: if `access_token` is expired, use `refresh_token` to get a new one
  and update the User row in DB

**Todo List:**
1. Create `backend/app/services/youtube.py`:
   - Build an authorized `googleapiclient.discovery` resource using the user's stored tokens
   - `fetch_channel_stats(user, db)`:
     - Call `channels.list(part="statistics", mine=True)`
     - Return `{ subscriber_count, total_views, video_count }`
   - `fetch_top_videos(user, db, limit=5)`:
     - Call `search.list(part="snippet", forMine=True, type="video", order="viewCount", maxResults=limit)`
       then `videos.list(part="statistics,snippet", id=<ids>)` to get stats
     - Return list of `{ video_id, title, thumbnail_url, views, likes, comments, published_at }`
2. Create `backend/app/services/analytics.py`:
   - Build an authorized `googleapiclient.discovery` resource for `youtubeAnalytics` v2
   - `fetch_watch_time(user, db)`:
     - Call `reports.query(ids="channel==MINE", metrics="estimatedMinutesWatched",
       startDate=28-days-ago, endDate=today)`
     - Return total minutes as integer
3. Create `backend/app/services/token_refresh.py`:
   - `ensure_valid_token(user, db)` — checks `token_expiry`, refreshes via Google token
     endpoint if expired, saves new tokens to DB, returns updated user

**Relevant Context:**
- YouTube Data API v3 quota cost: `channels.list` = 1 unit, `search.list` = 100 units,
  `videos.list` = 1 unit per video — keep `search.list` calls minimal
- YouTube Analytics API has a separate quota (separate project quota bucket)
- `google-api-python-client` handles discovery; pass `credentials` object built from
  stored `access_token` + `refresh_token`

---

### Sub-Task 5 — Analytics REST API Endpoints

**Status:** [ ] pending

**Intent:**
Expose FastAPI endpoints that the React frontend calls to retrieve dashboard data.
These endpoints read from SQLite snapshots (fast) and fall back to live API fetch if
today's snapshot is missing.

**Expected Outcomes:**
- `GET /api/dashboard/overview` — returns all KPI data for the Overview Dashboard
- `GET /api/dashboard/top-videos` — returns top 5 videos list
- Both endpoints require a valid JWT (use `get_current_user` dependency)
- Response shapes are clearly typed with Pydantic response models

**Todo List:**
1. Create `backend/app/schemas.py` with Pydantic response models:
   - `ChannelKPIs`: `subscriber_count`, `total_views`, `watch_time_minutes`, `video_count`
   - `VideoItem`: `video_id`, `title`, `thumbnail_url`, `views`, `likes`, `comments`,
     `published_at`, `engagement_rate` (computed: `(likes+comments)/views*100`)
   - `DashboardOverview`: contains `ChannelKPIs` + `snapshot_date` + `data_source`
     (`"cache"` or `"live"`)
2. Create `backend/app/routers/dashboard.py`:
   - `GET /api/dashboard/overview`:
     1. Query DB for today's `ChannelSnapshot` for the current user
     2. If found, return it as `ChannelKPIs` with `data_source="cache"`
     3. If not found, call `fetch_channel_stats` + `fetch_watch_time`, insert snapshot,
        return live data with `data_source="live"`
   - `GET /api/dashboard/top-videos`:
     1. Query DB for today's `VideoSnapshot` rows (up to 5) for the current user
     2. If found, return them
     3. If not found, call `fetch_top_videos`, insert snapshots, return live data
3. Register `dashboard` router in `main.py` with prefix `/api`

**Relevant Context:**
- `engagement_rate` is a computed field — calculate it in the Pydantic model validator
  or in the endpoint before returning, not stored in DB
- Both endpoints should handle the case where the user has no stored tokens gracefully
  (return `402` with a message directing them to re-authenticate)

---

### Sub-Task 6 — Daily Snapshot Cron Job

**Status:** [ ] pending

**Intent:**
Schedule a background job that runs once per day at midnight to fetch and store fresh
snapshots for all users, so dashboard loads are fast (served from DB) without hitting
YouTube API quotas on every page view.

**Expected Outcomes:**
- APScheduler job runs inside the FastAPI process at startup
- Job fires daily at 00:05 local time
- For each User in DB with a valid refresh token, fetches and inserts `ChannelSnapshot`
  and up to 5 `VideoSnapshot` rows for today (skips if row already exists for today)
- Errors for individual users are logged and do not stop the job for other users

**Todo List:**
1. Create `backend/app/scheduler.py`:
   - Initialise `AsyncIOScheduler` from APScheduler
   - Define `async def daily_snapshot_job()`:
     - Open a DB session
     - Query all User rows
     - For each user: call `ensure_valid_token`, then `fetch_channel_stats`,
       `fetch_watch_time`, `fetch_top_videos`
     - Insert `ChannelSnapshot` and `VideoSnapshot` rows if not already present for today
     - Log success/failure per user
   - Register job: `scheduler.add_job(daily_snapshot_job, "cron", hour=0, minute=5)`
2. Wire scheduler start/stop into FastAPI lifespan events in `main.py`

**Relevant Context:**
- Use `AsyncIOScheduler` (not `BackgroundScheduler`) to stay on the same asyncio event loop
- Wrap each user's fetch in `try/except` and log with Python's `logging` module
- APScheduler `misfire_grace_time=3600` prevents duplicate runs after restart

---

### Sub-Task 7 — React Overview Dashboard UI

**Status:** [ ] pending

**Intent:**
Build the Overview Dashboard page in React + TypeScript with 4 KPI cards and a
Top 5 Videos table, wired to the FastAPI endpoints via axios.

**Expected Outcomes:**
- `/dashboard` route renders the Overview Dashboard (protected — redirects to `/` if no JWT)
- 4 KPI cards displayed: Subscribers, Total Views, Watch Time, Video Count
- Top 5 Videos displayed as a styled table with thumbnail, title, views, likes, comments,
  engagement rate
- Loading skeleton shown while data is fetching
- Error state shown if API call fails
- "Sign out" button that clears JWT and redirects to login

**Todo List:**
1. Create `src/api/dashboard.ts` — axios functions:
   - `getOverview()` → calls `GET /api/dashboard/overview`
   - `getTopVideos()` → calls `GET /api/dashboard/top-videos`
   - Axios interceptor: attach `Authorization: Bearer <jwt>` header from localStorage
   - Interceptor: on `401` response, clear JWT and redirect to `/`
2. Create `src/components/KpiCard.tsx`:
   - Props: `label`, `value`, `unit` (optional)
   - Renders a card with a large number and label
3. Create `src/components/TopVideosTable.tsx`:
   - Props: `videos: VideoItem[]`
   - Renders a table with columns: Thumbnail, Title, Views, Likes, Comments, Engagement %
4. Create `src/pages/DashboardPage.tsx`:
   - Uses `useEffect` to call `getOverview()` and `getTopVideos()` on mount
   - Renders 4 `KpiCard` components in a responsive grid
   - Renders `TopVideosTable`
   - Shows a loading spinner / skeleton while `isLoading` is true
   - Shows an error banner if fetch fails
5. Set up React Router in `src/App.tsx`:
   - `/` → `LoginPage`
   - `/callback` → `CallbackPage`
   - `/dashboard` → `DashboardPage` (wrapped in a `PrivateRoute` that checks JWT)
6. Style with Tailwind CSS utility classes:
   - KPI card grid: `grid grid-cols-2 gap-4` (or `grid-cols-4` on wider screens)
   - KPI card: white card with shadow, rounded corners, padded — `bg-white rounded-xl shadow p-6`
   - Top Videos table: full-width, zebra striping via `odd:bg-gray-50`
   - Login page: centered card on a dark/gradient background
   - Loading state: animated pulse skeleton using `animate-pulse bg-gray-200 rounded`

**Relevant Context:**
- Tailwind v4 uses `@tailwindcss/vite` plugin — no `tailwind.config.js` needed
- No charting library needed for MVP — KPI cards are numbers only, table for top videos
- Recharts is already installed (reserved for a future sub-task or iteration)
- `PrivateRoute` simply checks `localStorage.getItem("jwt")` — no server validation needed
  at route level (the API call will 401 if the token is invalid)

---

### Sub-Task 8 — Integration Testing & README

**Status:** [ ] pending

**Intent:**
Do a full end-to-end walkthrough of the localhost app, fix any integration issues found,
and write a clear README so the app can be set up from scratch by following the docs.

**Expected Outcomes:**
- README covers: prerequisites, Google Cloud Console setup, env var configuration,
  backend start command, frontend start command, and expected first-run experience
- Full login → dashboard flow works end-to-end on localhost
- KPI cards and top 5 videos table display real data from the authenticated channel
- Daily snapshot job is confirmed to run (manually trigger it in a test route or log)

**Todo List:**
1. Write `README.md` at the project root with sections:
   - Prerequisites: Python 3.11+, Node 18+, a Google account (to create a Cloud project)
   - Step 1: Create a Google Cloud project from scratch (mirror the detailed steps from Sub-Task 3)
   - Step 2: Enable YouTube Data API v3 and YouTube Analytics API v2
   - Step 3: Create OAuth 2.0 Client ID — set redirect URI to `http://localhost:8000/auth/google/callback`
   - Step 4: Copy `.env.example` → `.env` in both `backend/` and `frontend/`, fill in values
   - Step 5: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
   - Step 6: `cd frontend && npm install && npm run dev`
   - Step 7: Open `http://localhost:5173`, click "Sign in with Google"
2. Manually test the full OAuth flow on localhost
3. Verify KPI cards show real subscriber count, views, and watch time
4. Verify top 5 videos table populates correctly
5. Manually call the snapshot job endpoint (add a `GET /admin/run-snapshot` dev-only route)
   and confirm DB rows are inserted
6. Document any known limitations in README:
   - Watch time requires channel owner OAuth (not public API)
   - First login fetches live data; subsequent same-day loads serve from SQLite cache
   - YouTube Data API quota: 10,000 units/day default

**Relevant Context:**
- The `GET /admin/run-snapshot` endpoint should only exist in development
  (gate it behind an env var `ENV=development`)
