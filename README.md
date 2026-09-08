# Listings Directory App

A simple CRUD application for managing listings across three categories: **Hotels**, **Cars**, and **Taxis**. Features a search bar and category filtering.

## Tech Stack
- **Backend:** Python Flask + PostgreSQL (psycopg2)
- **Frontend:** Vanilla HTML/CSS/JavaScript (served by Flask)
- **Database:** PostgreSQL (running in Docker)

## Project Structure
```
/backend/
  app.py          # Flask app, API routes, DB init
  schema.sql      # SQL schema (optional, DB auto-inits in app.py)
  requirements.txt
/frontend/
  index.html      # Single-page app UI
```

## Setup

### 1. Install Python dependencies
```bash
pip3 install --break-system-packages flask psycopg2-binary flask-cors
```

### 2. Start PostgreSQL (Docker)
Ensure the postgres container is running and reachable. Find its IP:
```bash
docker inspect postgres --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

### 3. Run the backend
```bash
cd backend
DATABASE_URL="postgres://user:password@<PG_IP>:5432/outline" python3 app.py
```

The app serves both the API and frontend at `http://localhost:4000`.

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/listings` | List all (optional `?category=hotel\|car\|taxi&search=query`) |
| `POST` | `/api/listings` | Create a listing |
| `GET` | `/api/listings/:id` | Get one listing |
| `DELETE` | `/api/listings/:id` | Delete a listing |

## Category-specific fields
- **Hotel:** `stars` (1-5), `amenities` (list)
- **Car:** `model`, `seats`, `year`
- **Taxi:** `rate_per_km`, `area`, `phone`
