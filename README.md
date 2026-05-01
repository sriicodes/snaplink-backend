# ⚡ SnapLink — Distributed URL Shortener with Analytics

A full-stack distributed URL shortening service built with FastAPI, PostgreSQL, Redis, and React.js. Designed with production-grade systems principles including consistent hashing, TTL-based caching, and fault-tolerant architecture.

---

## 🏗️ Architecture

```
User → React UI → FastAPI Backend → Redis Cache (hit?)
                                  → PostgreSQL (miss → update cache)
                                  → Consistent Hash Ring (node assignment)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL, SQLAlchemy |
| Cache | Redis (TTL-based eviction) |
| Frontend | React.js |
| Load Distribution | Consistent Hashing (MD5 ring) |
| Load Testing | Locust |

---

## ✨ Features

- **URL Shortening** — generates unique 6-character alphanumeric codes
- **Instant Redirects** — 307 temporary redirects preserve click tracking
- **Redis Caching** — TTL-based cache reduces repeated PostgreSQL lookups
- **Consistent Hashing** — distributes requests across simulated nodes; adding/removing a node only affects neighbouring nodes
- **Click Analytics** — tracks click counts per URL, exposes top URLs endpoint
- **React Dashboard** — real-time analytics UI with URL input and top URLs table
- **Fault Tolerance** — system remains available during simulated node failures

---

## 📁 Project Structure

```
snaplink/
├── main.py          # FastAPI app, all endpoints
├── database.py      # PostgreSQL models, SQLAlchemy setup
├── hashing.py       # Consistent hash ring implementation
├── locustfile.py    # Load testing configuration
└── snaplink-frontend/
    └── src/
        └── App.js   # React dashboard
```

---

## 🚀 Running Locally

### Backend

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux

# 2. Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis locust

# 3. Set up PostgreSQL — create a database named 'snaplink'

# 4. Start Redis server

# 5. Run the backend
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend

```bash
cd snaplink-frontend
npm install
npm start
```

Frontend runs at: `http://localhost:3000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/shorten` | Shorten a URL |
| GET | `/{short_code}` | Redirect to original URL |
| GET | `/analytics/top` | Get top 5 most clicked URLs |

### Example

```bash
# Shorten a URL
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'

# Response
{
  "original_url": "https://github.com",
  "short_url": "http://localhost:8000/aB3kPx",
  "short_code": "aB3kPx",
  "assigned_node": "node-2"
}
```

---

## 🧠 Key Design Decisions

**Why Redis over just PostgreSQL?**
Redis is an in-memory store with microsecond read times vs millisecond DB reads. Under high traffic, serving redirects from cache dramatically reduces database load.

**Why Consistent Hashing over modulo?**
With modulo (`hash % n`), adding or removing a node remaps almost all keys. Consistent hashing places nodes on a virtual ring — only the affected node's neighbours need remapping, preserving cache locality.

**Why 307 and not 301?**
301 is a permanent redirect — browsers cache it and never ask the server again, breaking click tracking. 307 is temporary — every redirect goes through the server, keeping analytics accurate.

---

## 📊 Load Testing

```bash
locust -f locustfile.py --host=http://localhost:8000
# Open http://localhost:8089
# Simulate concurrent users hitting /shorten and /{short_code}
```
