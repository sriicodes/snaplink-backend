from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import random
import string
import redis

from database import get_db, URL
from hashing import ConsistentHashRing

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    raise Exception("REDIS_URL not set")

cache = redis.from_url(
    redis_url,
    decode_responses=True
)

# Simulate distributed nodes
hash_ring = ConsistentHashRing()
hash_ring.add_node("node-1")
hash_ring.add_node("node-2")
hash_ring.add_node("node-3")


class ShortenRequest(BaseModel):
    url: str


def generate_short_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


@app.post("/shorten")
def shorten_url(request: ShortenRequest, db: Session = Depends(get_db)):
    short_code = generate_short_code()

    while db.query(URL).filter(URL.short_code == short_code).first():
        short_code = generate_short_code()

    new_url = URL(
        original_url=request.url,
        short_code=short_code
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    # Store in Redis (fault tolerant)
    try:
        cache.setex(short_code, 3600, request.url)
    except Exception as e:
        print("Redis cache failed:", e)

    # Assign node
    assigned_node = hash_ring.get_node(short_code)
    print(f"Short code '{short_code}' assigned to {assigned_node}")

    return {
        "original_url": request.url,
        "short_url": f"https://snaplink-xn19.onrender.com/{short_code}",
        "short_code": short_code,
        "assigned_node": assigned_node
    }


@app.get("/analytics/top")
def top_urls(db: Session = Depends(get_db)):
    urls = db.query(URL).order_by(URL.click_count.desc()).limit(5).all()

    return [
        {
            "short_code": u.short_code,
            "original_url": u.original_url,
            "click_count": u.click_count
        }
        for u in urls
    ]


@app.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):

    # Try Redis first
    try:
        cached_url = cache.get(short_code)
    except Exception as e:
        print("Redis read failed:", e)
        cached_url = None

    if cached_url:
        db.query(URL).filter(URL.short_code == short_code).update(
            {"click_count": URL.click_count + 1}
        )
        db.commit()

        print(f"CACHE HIT for {short_code}")
        return RedirectResponse(url=cached_url)

    # Fallback to PostgreSQL
    print(f"CACHE MISS for {short_code}")
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    # Store back in Redis
    try:
        cache.setex(short_code, 3600, url.original_url)
    except Exception as e:
        print("Redis cache failed:", e)

    url.click_count += 1
    db.commit()

    return RedirectResponse(url=url.original_url)