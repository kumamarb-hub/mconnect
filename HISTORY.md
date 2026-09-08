# MConnect — Project History & Session Log

This document records everything built in this project and the decisions made along the way, as a permanent record of the development conversation.

## The Idea

A simple listings directory where users add info about **Hotels**, **Cars**, **Taxis** (and any custom category) and search/filter it. Evolved into **MConnect** — a clean branded app with search, dynamic categories, ratings, and a Top 5 table.

## Tech Stack (why)

- **Python Flask + PostgreSQL (psycopg2) + vanilla HTML/CSS/JS** — since the machine had **no Node.js/npm** (only Python 3.13.7), we pivoted from a Node plan to Flask serving both the API and the single-page frontend.
- **PostgreSQL in Docker** at `172.18.0.3:5432` (not exposed to host; container IP used directly).
- The app runs on port `4000`, waited on by nothing — fully self-contained.

## How the session unfolded (chronological log)

### 1. Core CRUD app
- Listings CRUD with hardcoded categories (hotel/car/taxi). Realised a **listings table** + form UI.
- DB schema auto-creates on startup and **seeds** default categories only when the `categories` table is empty.

### 2. MConnect branding
- Logo with a slowly spinning icon (6s `slowSpin`).
- Purple→indigo gradient header, yellow accent, white→light-blue gradient page background, giant "MConnect" watermark.

### 3. Search & filter
- Search bar searching name/description/location (later extended to **category** too, case-insensitive via `ILIKE`).
- **Learnings about caching:** the app now sends `Cache-Control: no-store` on every response (`@app.after_request`) to stop stale-page bugs ("Clear doesn't work" was actually the browser caching an old JS file).

### 4. Dynamic categories
- `categories` table: `name` + `fields` (JSON) defining custom fields per category.
- UI: tabs per category, **"+ Add Category"** modal with a field builder (name/label/type incl. dropdown).
- Deleting a category **cascades** — its listings are deleted first.
- Dropped the old `listings_category_check` constraint so any category name works.
- Clear button = resets the **category filter** (back to All). Later also clears the search text.

### 5. Daily joke (added then removed)
- `/api/joke` with live joke API + bundled fallback. Removed from the frontend (took too much space). Backend endpoints still exist unused.

### 6. Ratings & real Top 5
- `rating NUMERIC(3,2)` + `rating_count INTEGER` columns on listings.
- `POST /api/listings/:id/rate` computes a running average.
- Stars on each card (★), click to rate.
- Top 5 table now sorts by `rating DESC, rating_count DESC, created_at DESC`, 7 columns with expandable detail rows.

### 7. Edit listings
- `PUT /api/listings/:id` + Edit button per card that **pre-fills the form** (including dynamic custom fields), modal title flips to "Edit Listing".

### 8. UX polish
- Hovering a category tab makes it **blink**.
- Deletes (category + listing) ask **"Are you sure?"** in a styled confirmation modal.

### 9. Saving & git / GitHub
- Project was living in `/tmp/opencode` (ephemeral!) — moved to permanent **`/home/marbella/mconnect`** and version-controlled.
- Created GitHub repo **`kumamarb-hub/mconnect`** (SSH key auth), pushed all code. Repo later made **public** for easy testing.

### 10. Docker packaging
- `Dockerfile` + `docker-compose.yml`: `web` (Flask) + `db` (postgres:16-alpine), persistent `pgdata` volume, health-gated startup.
- Production deploy via **`deploy.sh`** (one command: ensures Docker, pulls latest code from GitHub, `docker compose up -d --build`). Hardened against broken apt repos, missing Compose plugin (binary fallback), and old curl flag conflicts.

### 11. Production deploy (10.14.0.42)
- Deployed to the prod server `10.14.0.42` (static IP, separate VLAN from dev machine `10.10.24.59` — no direct route between them, so all server work is done via commands run by the user).

### 12. HTTPS experiments (all rolled back)
- **Self-signed HTTPS** via an nginx container (ports 80/443, cert for the IP, cert downloadable at `/mconnect-ca.crt`).
- **Plain-HTTP nginx** on port 80 when self-signed proved fiddly.
- **Both removed** — user wanted the simple public app on `http://10.14.0.42:4000`, which always "worked great".

### 13. Login screen (added then removed)
- Added a **"Welcome to MConnect"** login screen (username/password, session cookies), protected all API routes with `@login_required`, env-configured credentials.
- On the prod server it proved troublesome to keep running, so the user asked to **remove the login screen** and restore the simple open app. Done, committed, pushed. (Login code exists in git history commits `2493eba` if ever needed again.)

### 14. Server-side troubleshooting
- `pypi.org` build-time DNS failures on the server → fixed by setting Docker daemon DNS (`/etc/docker/daemon.json` → `"dns": ["8.8.8.8","1.1.1.1"]` + `systemctl restart docker`).

## Current state (final)

- **Live app:** Flask + Postgres in Docker on port `4000`, open access, **no login**.
- **URLs:** http://10.14.0.42:4000 (prod), http://10.10.24.59:4000 (dev).
- **Schema:** `listings` (incl. rating/rating_count/fields) + `categories` (fields JSON), auto-seed of hotel/car/taxi.

## Gotchas & lessons (worth remembering)

| Issue | Fix |
|---|---|
| Port 4000 conflicts between dev server & Docker | Stop the dev Flask, let Docker bind it |
| Docker DNS can't resolve pypi.org at build | `daemon.json` DNS `8.8.8.8`, `systemctl restart docker` |
| Browsers caching old JS/CSS | `no-store` headers on every response |
| `curl -fsSL` fails on server ("badly used here") | Server's curl config conflicts `-f` with user's `curlrc`; use `curl -sSL -o` or git clone |
| `docker-compose-plugin` not in distro repos | Download the binary from GitHub releases (x86_64 vs aarch64) |
| Unsigned apt repo (anydesk) breaks `apt-get update` | Remove the source file; `apt-get update || true` in deploy script |
| Compose override merges `ports` (doesn't replace) | Test services with `docker run` one-off instead |

## Updating this record

When big things change, keep this log current:

```bash
cd /home/marbella/mconnect
# ...edit HISTORY.md...
git add -A && git commit -m "Update history" && git push
```