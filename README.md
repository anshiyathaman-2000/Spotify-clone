# Spotify Clone with Intelligent Recommendation Engine

A full-stack Spotify Web Player clone featuring a FastAPI machine-learning recommendation engine and a premium dark-themed static frontend. The recommendation engine evaluates user history, likes, and skips to deliver content-based, collaborative, and trending song recommendations in real time.

---

## Features
- **Premium Web Player Interface**: Responsive, high-fidelity UI with real-time audio playback controls, volume controls, progress seeking, and song list navigation.
- **Intelligent ML Recommendations**:
  - **Collaborative Filtering**: Reconstructs listening preferences using Matrix Factorization (`TruncatedSVD`).
  - **Content-Based Filtering**: Calculates track profile similarities using Cosine Similarity of audio features (tempo, energy, valence, danceability, acousticness).
  - **Hybrid Blend**: Interleaves collaborative, content-based, and trending tracks.
- **Search Autocomplete**: Low-latency instant database search for artists, albums, and tracks.
- **Listening Statistics**: Calculates personalized mood categories (e.g. Chill, Energetic, Sad, Happy), skip rates, and favorite genre distributions.

---

## 🚀 Deployment & Local Running Guide

### Method 1: Using Docker & Docker Compose (Recommended)

Docker is the easiest way to launch the frontend, backend, database, and recommendation model without manually installing dependencies.

#### Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### Run Locally
1. In your terminal, navigate to the repository root directory:
   ```bash
   cd "/Users/apple/Library/Mobile Documents/com~apple~CloudDocs/spotify_clone/Spotify-clone"
   ```
2. Build and start the container:
   ```bash
   docker compose up --build
   ```
3. Open your browser and go to:
   **[http://localhost:8000](http://localhost:8000)**

*Note: The SQLite database file will be stored and persisted in a Docker volume named `spotify_data` (mapped inside `/app/backend/db` in the container) so your interactions, likes, and playlists will be saved across restarts.*

---

### Method 2: Manual Local Setup (Python Environment)

If you prefer to run the application directly in your Python environment without containers:

#### Prerequisites
- Install Python 3.10 or 3.11
- Install Node.js (optional, only if you run local serving utilities)

#### Setup Steps
1. Navigate to the backend directory and create a virtual environment:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Serve the frontend (FastAPI will serve the frontend automatically at `http://localhost:8000` because we updated `FRONTEND_DIR` in `main.py`!). 
   Simply open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## ☁️ Deploying to the Cloud (e.g. Render)

You can easily host this application on [Render](https://render.com) for free using the Dockerfile configurations we set up.

### Step-by-Step Render Deployment
1. **Push to GitHub**: Create a repository on GitHub and push this codebase to it.
2. **Create a Render Web Service**:
   - Log in to [Render Dashboard](https://dashboard.render.com).
   - Click **New +** and select **Web Service**.
   - Connect your GitHub repository.
3. **Configure Web Service Properties**:
   - **Name**: `spotify-recommendation-clone` (or any name you prefer)
   - **Environment/Runtime**: Select **Docker** (Render will automatically detect the `Dockerfile` at the root).
   - **Region**: Choose the closest location to you.
   - **Instance Type**: Select **Free** (or Starter).
4. **Environment Variables** (Optional):
   - You do not need to configure `DATABASE_URL` unless you want to connect to a PostgreSQL database. By default, it will fall back to SQLite inside the container.
   - If you want SQLite database persistence across redeploys on Render's paid tiers, add a **Persistent Disk** mount (Mount Path: `/app/backend/db`) and set the environment variable:
     `DATABASE_URL=sqlite:////app/backend/db/spotify.db`
5. **Deploy**: Click **Deploy Web Service**. Render will build the Docker image, run the FastAPI application, mount the static frontend, and host it on a public `https://...onrender.com` URL!