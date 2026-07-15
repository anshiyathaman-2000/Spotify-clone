import numpy as np
import pandas as pd
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sqlmodel import Session, select
from app.models import Track, LikeHistory, ListenHistory, SkipHistory, User

def get_track_features_df(tracks: List[Track]) -> pd.DataFrame:
    """Helper to convert track list into a normalized feature DataFrame."""
    data = []
    for t in tracks:
        data.append({
            "id": t.id,
            "tempo": t.tempo / 200.0,  # Max typical tempo normalization
            "energy": t.energy,
            "danceability": t.danceability,
            "valence": t.valence,
            "acousticness": t.acousticness
        })
    df = pd.DataFrame(data)
    if not df.empty:
        df.set_index("id", inplace=True)
    return df

def get_content_based_recommendations(session: Session, user_id: str, limit: int = 10) -> List[Track]:
    """Generates content-based recommendations based on Cosine Similarity."""
    # 1. Fetch all tracks
    all_tracks = session.exec(select(Track)).all()
    if not all_tracks:
        return []
    
    # 2. Get user likes and skips
    likes = session.exec(select(LikeHistory).where(LikeHistory.user_id == user_id)).all()
    skips = session.exec(select(SkipHistory).where(SkipHistory.user_id == user_id)).all()
    
    # If the user has no history, we can't perform content-based filtering.
    if not likes:
        return []
        
    liked_ids = {l.track_id for l in likes}
    skipped_ids = {s.track_id for s in skips}
    
    # 3. Build features DataFrame
    df_features = get_track_features_df(all_tracks)
    if df_features.empty:
        return []
        
    # 4. Construct User Profile Vector
    liked_vectors = df_features.loc[list(liked_ids & set(df_features.index))]
    skipped_vectors = df_features.loc[list(skipped_ids & set(df_features.index))]
    
    if liked_vectors.empty:
        return []
        
    # User Profile is mean of likes minus half mean of skips (to disfavor skipped qualities)
    user_profile = liked_vectors.mean(axis=0)
    if not skipped_vectors.empty:
        user_profile = user_profile - 0.5 * skipped_vectors.mean(axis=0)
        
    user_profile_arr = user_profile.values.reshape(1, -1)
    
    # 5. Compute similarities
    similarities = cosine_similarity(user_profile_arr, df_features.values)[0]
    df_features["similarity"] = similarities
    
    # Filter out tracks already liked or listened
    listens = session.exec(select(ListenHistory).where(ListenHistory.user_id == user_id)).all()
    listened_ids = {li.track_id for li in listens}
    exclude_ids = liked_ids.union(listened_ids)
    
    df_filtered = df_features.drop(index=list(exclude_ids & set(df_features.index)), errors="ignore")
    df_filtered = df_filtered.sort_values(by="similarity", ascending=False)
    
    recommended_ids = df_filtered.index[:limit].tolist()
    
    # Return track objects in order
    tracks_dict = {t.id: t for t in all_tracks}
    return [tracks_dict[tid] for tid in recommended_ids if tid in tracks_dict]

def get_collaborative_recommendations(session: Session, user_id: str, limit: int = 10) -> List[Track]:
    """Generates collaborative filtering recommendations using Matrix Factorization (SVD)."""
    # 1. Fetch interaction logs
    likes = session.exec(select(LikeHistory)).all()
    listens = session.exec(select(ListenHistory)).all()
    skips = session.exec(select(SkipHistory)).all()
    
    if not listens:
        return []
        
    # Calculate user-track score mapping
    # Formula: Likes = +3.0, Listen = +1.0, Skip = -2.0
    interactions: Dict[str, Dict[str, float]] = {}
    
    def add_interaction(u_id: str, t_id: str, val: float):
        if u_id not in interactions:
            interactions[u_id] = {}
        interactions[u_id][t_id] = interactions[u_id].get(t_id, 0.0) + val

    for l in likes:
        add_interaction(l.user_id, l.track_id, 3.0)
    for li in listens:
        add_interaction(li.user_id, li.track_id, 1.0)
    for s in skips:
        add_interaction(s.user_id, s.track_id, -2.0)
        
    # Check if target user has any interaction history
    if user_id not in interactions:
        return []
        
    # 2. Build User-Item Interaction Matrix DataFrame
    records = []
    for u, tracks_scores in interactions.items():
        for t, score in tracks_scores.items():
            records.append({"user_id": u, "track_id": t, "score": score})
            
    df = pd.DataFrame(records)
    user_item_matrix = df.pivot(index="user_id", columns="track_id", values="score").fillna(0.0)
    
    num_users, num_tracks = user_item_matrix.shape
    
    # Collaborative filtering requires enough data to build components
    if num_users < 3 or num_tracks < 3:
        return []
        
    try:
        # Fit Truncated SVD for matrix factorization
        n_components = min(5, num_users - 1, num_tracks - 1)
        if n_components < 1:
            return []
            
        svd = TruncatedSVD(n_components=n_components, random_state=42)
        latent_matrix = svd.fit_transform(user_item_matrix)
        
        # Reconstruct score predictions
        reconstructed = np.dot(latent_matrix, svd.components_)
        df_predictions = pd.DataFrame(reconstructed, index=user_item_matrix.index, columns=user_item_matrix.columns)
        
        # Get target user's predicted ratings
        user_preds = df_predictions.loc[user_id]
        
        # Exclude tracks already liked or listened
        user_listened = list(interactions[user_id].keys())
        user_preds = user_preds.drop(labels=user_listened, errors="ignore")
        user_preds = user_preds.sort_values(ascending=False)
        
        recommended_ids = user_preds.index[:limit].tolist()
        
        # Fetch tracks
        all_tracks = session.exec(select(Track)).all()
        tracks_dict = {t.id: t for t in all_tracks}
        return [tracks_dict[tid] for tid in recommended_ids if tid in tracks_dict]
        
    except Exception as e:
        print(f"Collaborative filtering SVD error: {e}")
        return []

def get_trending_tracks(session: Session, limit: int = 10) -> List[Track]:
    """Fallback ranking based on listening count and likes."""
    # Score = listen count + 2 * like count
    all_tracks = session.exec(select(Track)).all()
    if not all_tracks:
        return []
        
    listens = session.exec(select(ListenHistory)).all()
    likes = session.exec(select(LikeHistory)).all()
    
    popularity: Dict[str, float] = {}
    for li in listens:
        popularity[li.track_id] = popularity.get(li.track_id, 0.0) + 1.0
    for l in likes:
        popularity[l.track_id] = popularity.get(l.track_id, 0.0) + 2.0
        
    sorted_tracks = sorted(all_tracks, key=lambda t: popularity.get(t.id, 0.0), reverse=True)
    return sorted_tracks[:limit]

def get_hybrid_recommendations(session: Session, user_id: str, limit: int = 10) -> List[Track]:
    """Blends Collaborative, Content-Based and Popularity recommendations."""
    collab = get_collaborative_recommendations(session, user_id, limit=limit)
    content = get_content_based_recommendations(session, user_id, limit=limit)
    trending = get_trending_tracks(session, limit=limit)
    
    # Interleave results: Collaborative first, then Content-Based, then Trending
    seen_ids = set()
    recommended_tracks = []
    
    # Helper to add a list of tracks
    def add_from_pool(pool: List[Track]):
        for track in pool:
            if track.id not in seen_ids:
                seen_ids.add(track.id)
                recommended_tracks.append(track)
                if len(recommended_tracks) >= limit:
                    return True
        return False
        
    # Interleave
    for i in range(max(len(collab), len(content), len(trending))):
        if i < len(collab):
            if add_from_pool([collab[i]]): break
        if i < len(content):
            if add_from_pool([content[i]]): break
        if i < len(trending):
            if add_from_pool([trending[i]]): break
            
    # If we need more, just fill with any trending or remaining tracks
    if len(recommended_tracks) < limit:
        all_tracks = session.exec(select(Track)).all()
        add_from_pool(trending)
        add_from_pool(all_tracks)
        
    return recommended_tracks[:limit]
