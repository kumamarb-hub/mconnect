# MConnect — Listings Directory App

A listings directory where users add info about **Hotels**, **Cars**, **Taxis** (and any custom category) and search/filter it. Comes with ratings, a Top 5 table, and a daily-joke style banner.

## Features
- **Dynamic categories** — create categories with custom fields (text, number, phone, textarea, dropdown); tabs render automatically
- **Listings CRUD** — add, edit, delete; per-category fields; star ratings (running average + vote count)
- **Search** — case-insensitive across name, category, description, and location; category filter tabs + Clear button
- **Top 5 Listings** — table sorted by rating, expandable rows to view details
- **Confirmation modals** for deletes
- White → light-blue gradient with a semi-transparent "MConnect" watermark

## Tech Stack
- **Backend:** Python Flask + PostgreSQL (psycopg2)
- **Frontend:** Vanilla HTML/CSS/JavaScript (served by Flask)

## Project Structure
```
/backend/
  app.py          # Flask app, API routes, DB init (auto-creates tables + seeds defaults)
  requirements.txt
/frontend/
  index.html      # Single-page app UI
Dockerfile        # Web container image
docker-compose.yml  # web + db docker service stack
```

## 🐳 Deploy with Docker (recommended)

One command runs the whole app (Flask + PostgreSQL) with a persistent database:

```bash
docker compose up -d --build
```

- App → http://localhost:4000
- PostgreSQL runs in a private container (`db`), data persists in the `pgdata` volume (survives restarts/rebuilds)
- The schema auto-creates and seeds default categories (hotel/car/taxi) on first start

Useful commands:
```bash
docker compose logs -f web     # app logs
docker compose down            # stop containers (data kept)
docker compose down -v         # stop AND wipe the database
docker compose up -d --build   # rebuild after code changes
```

To change the DB password, edit `POSTGRES_PASSWORD` in `docker-compose.yml` (both spots) and run `docker compose down -v && docker compose up -d` to re-create the volume.

To deploy on a production server: install Docker on it, copy this folder, and run the same `docker compose up -d --build` command.

## Manual Setup (no Docker)

### 1. Install Python dependencies
```bash
pip3 install --break-system-packages flask psycopg2-binary flask-cors
```

### 2. Ensure a PostgreSQL server is reachable
The DB migrates/initializes itself on startup (creates `listings` + `categories` tables, seeds Hotel/Car/Taxi). Find the postgres container IP:
```bash
docker inspect postgres --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

### 3. Run the backend
```bash
cd backend
DATABASE_URL="postgres://user:password@<PG_IP>:5432/outline" python3 app.py
```

The app serves the API and frontend at `http://localhost:4000`.

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/listings` | List (optional `?category=<name>&search=<query>`) |
| `POST` | `/api/listings` | Create a listing |
| `GET` | `/api/listings/:id` | Get one listing |
| `PUT` | `/api/listings/:id` | Edit a listing |
| `DELETE` | `/api/listings/:id` | Delete a listing |
| `POST` | `/api/listings/:id/rate` | Rate a listing `{"value": 1-5}` |
| `GET` | `/api/listings/top` | Top-N by rating (`?limit=5`) |
| `GET` | `/api/categories` | List categories |
| `POST` | `/api/categories` | Create a category with field definitions |
| `DELETE` | `/api/categories/:name` | Delete a category (cascades its listings) |
| `GET` | `/api/joke` | Daily joke (live API with bundled fallback) |