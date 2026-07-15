import os
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime

from app.models import (
    Track, User, Playlist, PlaylistTrack, 
    ListenHistory, LikeHistory, SkipHistory
)
from app.database import engine, create_db_and_tables, get_session
from app.seed import seed_database
from app.recommender import (
    get_hybrid_recommendations,
    get_content_based_recommendations,
    get_collaborative_recommendations,
    get_trending_tracks
)

app = FastAPI(title="Spotify Intelligent Recommendation API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend") # Serve static frontend

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def on_startup():
    # Create DB and seed initial mock values
    create_db_and_tables()
    seed_database()

# User Routes
@app.get("/api/users", response_model=List[User])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()

@app.get("/api/users/{user_id}", response_model=User)
def get_user(user_id: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Track Routes
@app.get("/api/tracks", response_model=List[Track])
def get_tracks(session: Session = Depends(get_session)):
    return session.exec(select(Track)).all()

@app.get("/api/tracks/{track_id}", response_model=Track)
def get_track(track_id: str, session: Session = Depends(get_session)):
    track = session.exec(select(Track).where(Track.id == track_id)).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

# Playlist Routes
@app.get("/api/playlists", response_model=List[Playlist])
def get_playlists(session: Session = Depends(get_session)):
    return session.exec(select(Playlist)).all()

@app.get("/api/playlists/{playlist_id}")
def get_playlist(playlist_id: str, session: Session = Depends(get_session)):
    playlist = session.exec(select(Playlist).where(Playlist.id == playlist_id)).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Get tracks inside playlist
    stmt = (
        select(Track)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
    )
    playlist_tracks = session.exec(stmt).all()
    
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "coverUrl": playlist.cover_url,
        "tracks": playlist_tracks
    }

# Interactions logging
@app.post("/api/interactions/play")
def log_play(user_id: str, track_id: str, session: Session = Depends(get_session)):
    history = ListenHistory(user_id=user_id, track_id=track_id)
    session.add(history)
    session.commit()
    return {"status": "success", "message": "Listen history logged."}

@app.post("/api/interactions/like")
def toggle_like(user_id: str, track_id: str, session: Session = Depends(get_session)):
    existing = session.exec(
        select(LikeHistory).where(LikeHistory.user_id == user_id, LikeHistory.track_id == track_id)
    ).first()
    
    if existing:
        session.delete(existing)
        session.commit()
        return {"status": "success", "liked": False, "message": "Like removed."}
    else:
        like = LikeHistory(user_id=user_id, track_id=track_id)
        session.add(like)
        session.commit()
        return {"status": "success", "liked": True, "message": "Like added."}

@app.get("/api/interactions/like-status")
def get_like_status(user_id: str, track_id: str, session: Session = Depends(get_session)):
    existing = session.exec(
        select(LikeHistory).where(LikeHistory.user_id == user_id, LikeHistory.track_id == track_id)
    ).first()
    return {"liked": existing is not None}

@app.post("/api/interactions/skip")
def log_skip(user_id: str, track_id: str, session: Session = Depends(get_session)):
    skip = SkipHistory(user_id=user_id, track_id=track_id)
    session.add(skip)
    session.commit()
    return {"status": "success", "message": "Track skip logged."}

# Recommendation Routes
@app.get("/api/recommendations/hybrid", response_model=List[Track])
def hybrid_recs(user_id: str, limit: int = 10, session: Session = Depends(get_session)):
    return get_hybrid_recommendations(session, user_id, limit=limit)

@app.get("/api/recommendations/content", response_model=List[Track])
def content_recs(user_id: str, limit: int = 10, session: Session = Depends(get_session)):
    return get_content_based_recommendations(session, user_id, limit=limit)

@app.get("/api/recommendations/collaborative", response_model=List[Track])
def collab_recs(user_id: str, limit: int = 10, session: Session = Depends(get_session)):
    return get_collaborative_recommendations(session, user_id, limit=limit)

@app.get("/api/recommendations/trending", response_model=List[Track])
def trending_recs(limit: int = 10, session: Session = Depends(get_session)):
    return get_trending_tracks(session, limit=limit)

# Search Autocomplete
@app.get("/api/search/autocomplete")
def search_autocomplete(q: str = "", session: Session = Depends(get_session)):
    if not q:
        return []
    query = q.lower()
    stmt = (
        select(Track)
        .where(
            (func.lower(Track.title).contains(query)) |
            (func.lower(Track.artist).contains(query)) |
            (func.lower(Track.album).contains(query))
        )
        .limit(8)
    )
    return session.exec(stmt).all()

# Stats calculation
@app.get("/api/stats")
def get_user_stats(user_id: str, session: Session = Depends(get_session)):
    # 1. Favorite genres (based on listened history tracks)
    listens = session.exec(
        select(Track.genre, func.count(ListenHistory.id))
        .join(ListenHistory, ListenHistory.track_id == Track.id)
        .where(ListenHistory.user_id == user_id)
        .group_by(Track.genre)
    ).all()
    
    genre_stats = [{"genre": genre, "count": count} for genre, count in listens]
    
    # 2. Skip Rate
    total_listens = session.exec(
        select(func.count(ListenHistory.id)).where(ListenHistory.user_id == user_id)
    ).one() or 0
    
    total_skips = session.exec(
        select(func.count(SkipHistory.id)).where(SkipHistory.user_id == user_id)
    ).one() or 0
    
    total_interactions = total_listens + total_skips
    skip_rate = (total_skips / total_interactions) * 100 if total_interactions > 0 else 0
    
    # 3. Listening Mood (valence & energy averages)
    avg_mood = session.exec(
        select(func.avg(Track.valence), func.avg(Track.energy))
        .join(ListenHistory, ListenHistory.track_id == Track.id)
        .where(ListenHistory.user_id == user_id)
    ).first()
    
    avg_valence = avg_mood[0] if avg_mood and avg_mood[0] is not None else 0.5
    avg_energy = avg_mood[1] if avg_mood and avg_mood[1] is not None else 0.5
    
    # Categorize mood: Happy (high valence, high energy), Sad (low valence, low energy), Chill (high valence, low energy), Energetic (low valence, high energy)
    mood_category = "Chill"
    if avg_valence > 0.55:
        mood_category = "Happy" if avg_energy > 0.5 else "Chill"
    else:
        mood_category = "Energetic" if avg_energy > 0.5 else "Sad / Moody"

    return {
        "genreStats": genre_stats,
        "skipRate": round(skip_rate, 1),
        "totalPlays": total_listens,
        "totalSkips": total_skips,
        "averageValence": round(avg_valence, 2),
        "averageEnergy": round(avg_energy, 2),
        "moodCategory": mood_category
    }

# Serve compiled frontend build if it exists
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "message": "Spotify API running. Frontend folder is not compiled yet.",
            "api_endpoints": "/docs"
        }