from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Track, User, Playlist, PlaylistTrack, LikeHistory, ListenHistory, SkipHistory
from datetime import datetime, timedelta

def seed_database():
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if database is already seeded
        if session.exec(select(User)).first():
            print("Database already seeded.")
            return
            
        print("Seeding database...")
        
        # 1. Create Tracks
        tracks = [
            Track(
                id="1",
                title="Late Night Reverie",
                artist="Lofi Beats Collective",
                album="Cozy Nights",
                genre="Lofi",
                cover_url="/static/images/album_lofi.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                tempo=80.0,
                energy=0.3,
                danceability=0.5,
                valence=0.7,
                acousticness=0.8
            ),
            Track(
                id="2",
                title="Grid Horizon",
                artist="Synthwave Retro Project",
                album="Neon Sunset",
                genre="Synthwave",
                cover_url="/static/images/album_retro.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                tempo=120.0,
                energy=0.8,
                danceability=0.7,
                valence=0.6,
                acousticness=0.1
            ),
            Track(
                id="3",
                title="Blue Saxophone Club",
                artist="The Jazz Quartet",
                album="Expressive Moods",
                genre="Jazz",
                cover_url="/static/images/album_jazz.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
                tempo=90.0,
                energy=0.4,
                danceability=0.6,
                valence=0.5,
                acousticness=0.7
            ),
            Track(
                id="4",
                title="Bonfire Waves",
                artist="Acoustic Beachside",
                album="Calm Oceans",
                genre="Acoustic",
                cover_url="/static/images/album_acoustic.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
                tempo=75.0,
                energy=0.25,
                danceability=0.4,
                valence=0.6,
                acousticness=0.95
            ),
            Track(
                id="5",
                title="Rainy Cyberpunk Drive",
                artist="Neon Rain",
                album="Synth City",
                genre="Electro",
                cover_url="/static/images/album_electro.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
                tempo=140.0,
                energy=0.9,
                danceability=0.6,
                valence=0.4,
                acousticness=0.05
            ),
            Track(
                id="6",
                title="Tokyo Cafe Chill",
                artist="Lofi Beats Collective",
                album="Cozy Nights",
                genre="Lofi",
                cover_url="/static/images/album_lofi.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
                tempo=82.0,
                energy=0.35,
                danceability=0.55,
                valence=0.65,
                acousticness=0.75
            ),
            Track(
                id="7",
                title="Outrun Sunset",
                artist="Synthwave Retro Project",
                album="Neon Sunset",
                genre="Synthwave",
                cover_url="/static/images/album_retro.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
                tempo=118.0,
                energy=0.75,
                danceability=0.68,
                valence=0.58,
                acousticness=0.15
            ),
            Track(
                id="8",
                title="Autumn in New York",
                artist="The Jazz Quartet",
                album="Expressive Moods",
                genre="Jazz",
                cover_url="/static/images/album_jazz.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
                tempo=88.0,
                energy=0.38,
                danceability=0.58,
                valence=0.48,
                acousticness=0.72
            ),
            Track(
                id="9",
                title="Campfire Stories",
                artist="Acoustic Beachside",
                album="Calm Oceans",
                genre="Acoustic",
                cover_url="/static/images/album_acoustic.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
                tempo=78.0,
                energy=0.28,
                danceability=0.42,
                valence=0.62,
                acousticness=0.92
            ),
            Track(
                id="10",
                title="Neon City Run",
                artist="Neon Rain",
                album="Synth City",
                genre="Electro",
                cover_url="/static/images/album_electro.png",
                audio_url="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
                tempo=135.0,
                energy=0.85,
                danceability=0.62,
                valence=0.45,
                acousticness=0.08
            )
        ]
        
        for t in tracks:
            session.add(t)
            
        # 2. Create Users
        users = [
            User(id="dev", username="Developer (Active User)"),
            User(id="alice", username="Alice (Lofi & Acoustic Fan)"),
            User(id="bob", username="Bob (Synthwave & Electro Fan)"),
            User(id="charlie", username="Charlie (Jazz & Acoustic Fan)"),
            User(id="david", username="David (Lofi & Jazz Fan)")
        ]
        
        for u in users:
            session.add(u)
            
        session.commit()
        
        # 3. Create Playlists
        playlists = [
            Playlist(id="p1", name="Chill Beats for Coding", description="Relaxing tracks to keep you focused.", cover_url="/static/images/album_lofi.png", user_id="dev"),
            Playlist(id="p2", name="Synthwave Horizon", description="Drive into the futuristic neon sunset.", cover_url="/static/images/album_retro.png", user_id="dev"),
            Playlist(id="p3", name="Moods and Jazz", description="Smooth and expressive saxophone melodies.", cover_url="/static/images/album_jazz.png", user_id="dev")
        ]
        for p in playlists:
            session.add(p)
        session.commit()
        
        # Playlist track relationships
        playlist_tracks = [
            PlaylistTrack(playlist_id="p1", track_id="1"),
            PlaylistTrack(playlist_id="p1", track_id="6"),
            PlaylistTrack(playlist_id="p1", track_id="4"),
            PlaylistTrack(playlist_id="p2", track_id="2"),
            PlaylistTrack(playlist_id="p2", track_id="7"),
            PlaylistTrack(playlist_id="p2", track_id="5"),
            PlaylistTrack(playlist_id="p2", track_id="10"),
            PlaylistTrack(playlist_id="p3", track_id="3"),
            PlaylistTrack(playlist_id="p3", track_id="8")
        ]
        for pt in playlist_tracks:
            session.add(pt)
            
        # 4. Create User Listening History & Feedback (to seed recommender)
        # Alice (likes Lofi/Acoustic, hates Synthwave/Electro)
        alice_likes = ["1", "6", "4", "9"]
        alice_skips = ["2", "7", "5", "10"]
        for tid in alice_likes:
            session.add(LikeHistory(user_id="alice", track_id=tid))
            session.add(ListenHistory(user_id="alice", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=2)))
            session.add(ListenHistory(user_id="alice", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=1)))
        for tid in alice_skips:
            session.add(SkipHistory(user_id="alice", track_id=tid))
            session.add(ListenHistory(user_id="alice", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=4)))

        # Bob (likes Synthwave/Electro, hates Lofi/Acoustic)
        bob_likes = ["2", "7", "5", "10"]
        bob_skips = ["1", "6", "4", "9"]
        for tid in bob_likes:
            session.add(LikeHistory(user_id="bob", track_id=tid))
            session.add(ListenHistory(user_id="bob", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=2)))
            session.add(ListenHistory(user_id="bob", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=1)))
        for tid in bob_skips:
            session.add(SkipHistory(user_id="bob", track_id=tid))
            session.add(ListenHistory(user_id="bob", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=4)))

        # Charlie (likes Jazz/Acoustic, skips Electro)
        charlie_likes = ["3", "8", "4", "9"]
        charlie_skips = ["5", "10"]
        for tid in charlie_likes:
            session.add(LikeHistory(user_id="charlie", track_id=tid))
            session.add(ListenHistory(user_id="charlie", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=3)))
        for tid in charlie_skips:
            session.add(SkipHistory(user_id="charlie", track_id=tid))

        # David (likes Lofi/Jazz, skips Acoustic)
        david_likes = ["1", "6", "3", "8"]
        david_skips = ["4", "9"]
        for tid in david_likes:
            session.add(LikeHistory(user_id="david", track_id=tid))
            session.add(ListenHistory(user_id="david", track_id=tid, timestamp=datetime.utcnow() - timedelta(hours=3)))
        for tid in david_skips:
            session.add(SkipHistory(user_id="david", track_id=tid))

        # Seed Active user with a tiny history (likes Late Night Reverie and Lofi cafe, skips Tokyo Outrun Synth)
        # So content-based should suggest more Lofi/Acoustic, and collaborative should match Alice/David.
        session.add(LikeHistory(user_id="dev", track_id="1"))
        session.add(ListenHistory(user_id="dev", track_id="1"))
        session.add(SkipHistory(user_id="dev", track_id="2"))

        session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
