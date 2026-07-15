from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)
    username: str

class Track(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    artist: str
    album: str
    genre: str
    cover_url: str
    audio_url: str
    tempo: float  # BPM (e.g. 70-160)
    energy: float  # 0.0 to 1.0
    danceability: float  # 0.0 to 1.0
    valence: float  # 0.0 to 1.0 (happiness/mood)
    acousticness: float  # 0.0 to 1.0

class PlaylistTrack(SQLModel, table=True):
    playlist_id: str = Field(foreign_key="playlist.id", primary_key=True)
    track_id: str = Field(foreign_key="track.id", primary_key=True)

class Playlist(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    description: str
    cover_url: str
    user_id: str = Field(foreign_key="user.id")

class ListenHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    track_id: str = Field(foreign_key="track.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LikeHistory(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    track_id: str = Field(foreign_key="track.id", primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SkipHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    track_id: str = Field(foreign_key="track.id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
