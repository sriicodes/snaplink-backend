from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import random, string, redis
from database import get_db, URL
from hashing import ConsistentHashRing

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
cache = redis.from_url(
    os.getenv("REDIS_URL"),
    decode_responses=True
)
# Simulate 3 server nodes
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

    new_url = URL(original_url=request.url, short_code=short_code)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    # Store in Redis with 1 hour TTL
    cache.setex(short_code, 3600, request.url)

    # Assign to a node via consistent hashing
    assigned_node = hash_ring.get_node(short_code)
    print(f"Short code '{short_code}' assigned to {assigned_node}")

    return {
        "original_url": request.url,
        "short_url": f"http://localhost:8000/{short_code}",
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

    # Step 1: Check Redis first
    cached_url = cache.get(short_code)

    if cached_url:
        db.query(URL).filter(URL.short_code == short_code).update(
            {"click_count": URL.click_count + 1}
        )
        db.commit()
        print(f"CACHE HIT for {short_code}")
        return RedirectResponse(url=cached_url)

    # Step 2: Cache miss — query PostgreSQL
    print(f"CACHE MISS for {short_code}")
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    # Step 3: Store in Redis for next time
    cache.setex(short_code, 3600, url.original_url)
    url.click_count += 1
    db.commit()

    return RedirectResponse(url=url.original_url)