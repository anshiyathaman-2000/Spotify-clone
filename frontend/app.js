// Spotify Clone client side application logic
document.addEventListener('DOMContentLoaded', () => {
    // API URL Discovery
    const getApiUrl = () => {
        if (window.location.protocol.startsWith('http')) {
            // If running frontend on a different port than 8000 (e.g. Live Server on 5500)
            if (window.location.port && window.location.port !== '8000' && window.location.port !== '80') {
                return 'http://localhost:8000';
            }
            return window.location.origin;
        }
        return 'http://localhost:8000';
    };

    const API_BASE = getApiUrl();

    // DOM Elements
    const audio = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('btn-play-pause');
    const playAllBtn = document.getElementById('play-all-btn');
    const prevBtn = document.getElementById('btn-prev');
    const nextBtn = document.getElementById('btn-next');
    const shuffleBtn = document.getElementById('btn-shuffle');
    const repeatBtn = document.getElementById('btn-repeat');
    const volumeBtn = document.getElementById('btn-volume');
    
    const searchInput = document.getElementById('search-input');
    const homeBtn = document.getElementById('btn-home');
    
    const playlistsContainer = document.getElementById('playlists-list');
    const songsContainer = document.getElementById('songs-list');
    
    // Hero banner elements
    const heroCover = document.getElementById('hero-cover');
    const heroTitle = document.getElementById('hero-title');
    const heroDescription = document.getElementById('hero-description');
    const heroTrackCount = document.getElementById('hero-track-count');
    
    // Player bar elements
    const playerCover = document.getElementById('player-cover');
    const playerCoverFallback = document.getElementById('player-cover-fallback');
    const playerTitle = document.getElementById('player-title');
    const playerArtist = document.getElementById('player-artist');
    const likeTrackBtn = document.getElementById('like-track-btn');
    
    // Sliders
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressHandle = document.getElementById('progress-handle');
    const currentTimeEl = document.getElementById('current-time');
    const totalDurationEl = document.getElementById('total-duration');
    
    const volumeBarContainer = document.getElementById('volume-bar-container');
    const volumeBarFill = document.getElementById('volume-bar-fill');
    
    const appContainer = document.querySelector('.app-container');

    // App State
    let currentTracks = []; // currently active track list (from loaded playlist or search)
    let currentTrackIndex = -1;
    let isPlaying = false;
    let isShuffle = false;
    let isRepeat = false;
    let originalTracks = []; // backup for shuffle restoring
    let currentPlaylistId = null;
    let playlists = [];

    // Initialize Application
    init();

    async function init() {
        // Setup Event Listeners
        setupEventListeners();
        
        // Load Initial Playlists and default home page
        await loadPlaylists();
        
        // Load default first playlist
        if (playlists.length > 0) {
            loadPlaylist(playlists[0].id);
        } else {
            // If playlists fail to load, fetch all tracks
            loadAllTracks();
        }
        
        // Default Volume
        audio.volume = 0.8;
        updateVolumeUI(0.8);
    }

    function setupEventListeners() {
        // Player Control Bar Event Listeners
        playPauseBtn.addEventListener('click', togglePlay);
        playAllBtn.addEventListener('click', () => {
            if (currentTracks.length > 0) {
                if (currentTrackIndex === -1) {
                    playTrack(0);
                } else {
                    togglePlay();
                }
            }
        });
        
        prevBtn.addEventListener('click', playPrevious);
        nextBtn.addEventListener('click', playNext);
        
        shuffleBtn.addEventListener('click', () => {
            isShuffle = !isShuffle;
            shuffleBtn.classList.toggle('active', isShuffle);
            if (isShuffle) {
                // Shuffle currentTracks array but keep current playing song index
                originalTracks = [...currentTracks];
                let currentTrack = currentTracks[currentTrackIndex];
                
                // Fisher-Yates shuffle
                for (let i = currentTracks.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [currentTracks[i], currentTracks[j]] = [currentTracks[j], currentTracks[i]];
                }
                
                // Relocate current track index to maintain correct state
                currentTrackIndex = currentTracks.indexOf(currentTrack);
            } else {
                // Restore original tracks order
                let currentTrack = currentTracks[currentTrackIndex];
                currentTracks = [...originalTracks];
                currentTrackIndex = currentTracks.indexOf(currentTrack);
            }
        });
        
        repeatBtn.addEventListener('click', () => {
            isRepeat = !isRepeat;
            repeatBtn.classList.toggle('active', isRepeat);
        });

        // Audio HTML5 element listeners
        audio.addEventListener('timeupdate', updateProgressBar);
        audio.addEventListener('loadedmetadata', () => {
            totalDurationEl.textContent = formatTime(audio.duration);
        });
        audio.addEventListener('ended', () => {
            if (isRepeat) {
                audio.currentTime = 0;
                audio.play();
            } else {
                playNext();
            }
        });

        // Click-to-seek progress bar
        progressBarContainer.addEventListener('click', (e) => {
            const rect = progressBarContainer.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const width = rect.width;
            const percentage = Math.max(0, Math.min(1, clickX / width));
            
            if (audio.duration) {
                audio.currentTime = percentage * audio.duration;
                updateProgressBar();
            }
        });

        // Volume adjustment
        volumeBarContainer.addEventListener('click', (e) => {
            const rect = volumeBarContainer.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const width = rect.width;
            const volume = Math.max(0, Math.min(1, clickX / width));
            
            audio.volume = volume;
            updateVolumeUI(volume);
        });

        volumeBtn.addEventListener('click', () => {
            if (audio.muted) {
                audio.muted = false;
                volumeBtn.querySelector('i').className = audio.volume > 0.5 ? 'fa-solid fa-volume-high' : 'fa-solid fa-volume-low';
            } else {
                audio.muted = true;
                volumeBtn.querySelector('i').className = 'fa-solid fa-volume-xmark';
            }
        });

        // Search inputs
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            searchTimeout = setTimeout(() => {
                if (query.length > 0) {
                    performSearch(query);
                } else {
                    // Reset to active playlist
                    if (currentPlaylistId) {
                        loadPlaylist(currentPlaylistId);
                    } else {
                        loadAllTracks();
                    }
                }
            }, 300);
        });

        // Home button resetting to all tracks
        homeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.playlist-item').forEach(el => el.classList.remove('active'));
            currentPlaylistId = null;
            loadAllTracks();
        });

        // Track liking mock animation
        likeTrackBtn.addEventListener('click', () => {
            likeTrackBtn.classList.toggle('active');
            const heart = likeTrackBtn.querySelector('i');
            if (likeTrackBtn.classList.contains('active')) {
                heart.className = 'fa-solid fa-heart';
                heart.style.color = 'var(--primary-color)';
            } else {
                heart.className = 'fa-regular fa-heart';
                heart.style.color = '';
            }
        });
    }

    // Load and render playlists in Sidebar
    async function loadPlaylists() {
        try {
            const res = await fetch(`${API_BASE}/api/playlists`);
            if (!res.ok) throw new Error('Failed to fetch playlists');
            playlists = await res.json();
            
            playlistsContainer.innerHTML = '';
            playlists.forEach(pl => {
                const div = document.createElement('div');
                div.className = 'playlist-item';
                div.setAttribute('data-id', pl.id);
                div.innerHTML = `
                    <img src="${API_BASE}${pl.coverUrl}" class="playlist-img-small" alt="${pl.name}">
                    <div class="playlist-info-small">
                        <div class="playlist-name-small">${pl.name}</div>
                        <div class="playlist-tracks-small">${pl.tracks.length} songs</div>
                    </div>
                `;
                
                div.addEventListener('click', () => {
                    document.querySelectorAll('.playlist-item').forEach(el => el.classList.remove('active'));
                    div.classList.add('active');
                    loadPlaylist(pl.id);
                });
                
                playlistsContainer.appendChild(div);
            });
        } catch (err) {
            console.error('Playlists API Error:', err);
            playlistsContainer.innerHTML = '<div class="loading-placeholder">Failed to load playlists.</div>';
        }
    }

    // Load tracks from playlist
    async function loadPlaylist(id) {
        currentPlaylistId = id;
        try {
            const res = await fetch(`${API_BASE}/api/playlists/${id}`);
            if (!res.ok) throw new Error('Failed to load playlist tracks');
            const playlist = await res.json();
            
            // Set Hero details
            heroCover.src = `${API_BASE}${playlist.coverUrl}`;
            heroTitle.textContent = playlist.name;
            heroDescription.textContent = playlist.description;
            heroTrackCount.innerHTML = `&bull; ${playlist.tracks.length} songs`;
            
            currentTracks = playlist.tracks;
            originalTracks = [...currentTracks];
            
            renderSongsList();
        } catch (err) {
            console.error('Playlist load error:', err);
        }
    }

    // Load all tracks as a fallback / home
    async function loadAllTracks() {
        try {
            const res = await fetch(`${API_BASE}/api/tracks`);
            if (!res.ok) throw new Error('Failed to load tracks');
            const tracksList = await res.json();
            
            // Set Hero details to All Tracks
            heroCover.src = '/static/images/album_lofi.png';
            heroTitle.textContent = "All Songs Collection";
            heroDescription.textContent = "Everything playing inside Spotify Clone API.";
            heroTrackCount.innerHTML = `&bull; ${tracksList.length} songs`;
            
            currentTracks = tracksList;
            originalTracks = [...currentTracks];
            
            renderSongsList();
        } catch (err) {
            console.error('All tracks load error:', err);
        }
    }

    // Perform track search
    async function performSearch(query) {
        try {
            const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
            if (!res.ok) throw new Error('Search failed');
            const searchResults = await res.json();
            
            // Update Hero details for Search
            heroCover.src = '/static/images/album_electro.png';
            heroTitle.textContent = `Search: "${query}"`;
            heroDescription.textContent = `Displaying search results matching your search terms.`;
            heroTrackCount.innerHTML = `&bull; ${searchResults.length} results found`;
            
            currentTracks = searchResults;
            originalTracks = [...currentTracks];
            
            renderSongsList();
        } catch (err) {
            console.error('Search error:', err);
        }
    }

    // Render Songs in main panel list
    function renderSongsList() {
        songsContainer.innerHTML = '';
        
        if (currentTracks.length === 0) {
            songsContainer.innerHTML = '<div class="loading-placeholder">No songs found in this view.</div>';
            return;
        }

        currentTracks.forEach((track, index) => {
            const row = document.createElement('div');
            // active class check
            const isActive = currentTrackIndex !== -1 && currentTracks[currentTrackIndex] && currentTracks[currentTrackIndex].id === track.id;
            
            row.className = `song-row ${isActive ? 'active' : ''} ${isActive && !isPlaying ? 'paused' : ''}`;
            row.innerHTML = `
                <div class="song-index">
                    <span class="index-number">${index + 1}</span>
                    <span class="hover-play-icon"><i class="fa-solid fa-play"></i></span>
                    <div class="playing-waveform">
                        <div class="bar"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                    </div>
                </div>
                <div class="song-title-col">
                    <img src="${API_BASE}${track.coverUrl}" class="song-cover" alt="">
                    <div class="song-meta-text">
                        <div class="song-title-text">${track.title}</div>
                        <div class="song-artist-text">${track.artist}</div>
                    </div>
                </div>
                <div class="song-album-text">${track.album}</div>
                <div class="song-duration-text">${formatTime(track.duration)}</div>
            `;
            
            // Play song on click
            row.addEventListener('click', () => {
                if (isActive) {
                    togglePlay();
                } else {
                    // Find actual index in currentTracks
                    playTrack(index);
                }
            });
            
            songsContainer.appendChild(row);
        });
    }

    // Play specific track by index in currentTracks list
    function playTrack(index) {
        if (index < 0 || index >= currentTracks.length) return;
        
        currentTrackIndex = index;
        const track = currentTracks[currentTrackIndex];
        
        // Load audio source
        audio.src = track.audioUrl;
        audio.play().then(() => {
            isPlaying = true;
            updatePlaybackUI(track);
        }).catch(err => {
            console.error('Audio playback failed:', err);
            isPlaying = false;
            playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
            playAllBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        });
    }

    // Play/Pause toggler
    function togglePlay() {
        if (currentTrackIndex === -1) {
            if (currentTracks.length > 0) {
                playTrack(0);
            }
            return;
        }
        
        const track = currentTracks[currentTrackIndex];
        
        if (isPlaying) {
            audio.pause();
            isPlaying = false;
            playPauseBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
            playAllBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
            appContainer.classList.add('paused');
            document.querySelectorAll('.song-row').forEach(row => {
                if (row.classList.contains('active')) {
                    row.classList.add('paused');
                }
            });
        } else {
            audio.play().then(() => {
                isPlaying = true;
                playPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
                playAllBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
                appContainer.classList.remove('paused');
                document.querySelectorAll('.song-row').forEach(row => {
                    if (row.classList.contains('active')) {
                        row.classList.remove('paused');
                    }
                });
            }).catch(err => console.error('Play failed:', err));
        }
    }

    // Skip to next track
    function playNext() {
        if (currentTracks.length === 0) return;
        let nextIndex = currentTrackIndex + 1;
        if (nextIndex >= currentTracks.length) {
            nextIndex = 0; // loop back to first
        }
        playTrack(nextIndex);
    }

    // Skip to previous track
    function playPrevious() {
        if (currentTracks.length === 0) return;
        
        // If track is already playing for > 3s, restart track
        if (audio.currentTime > 3) {
            audio.currentTime = 0;
            return;
        }
        
        let prevIndex = currentTrackIndex - 1;
        if (prevIndex < 0) {
            prevIndex = currentTracks.length - 1; // loop to last
        }
        playTrack(prevIndex);
    }

    // Sync UI with current playing track details
    function updatePlaybackUI(track) {
        playerCover.src = `${API_BASE}${track.coverUrl}`;
        playerCover.classList.remove('hidden');
        playerCoverFallback.classList.add('hidden');
        
        playerTitle.textContent = track.title;
        playerArtist.textContent = track.artist;
        
        playPauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
        playAllBtn.innerHTML = '<i class="fa-solid fa-pause"></i>';
        
        appContainer.classList.add('playing-active');
        appContainer.classList.remove('paused');
        
        // Redraw lists to highlight active row
        renderSongsList();
    }

    // Synchronize progress bar
    function updateProgressBar() {
        if (!audio.duration) return;
        
        const current = audio.currentTime;
        const duration = audio.duration;
        const percentage = (current / duration) * 100;
        
        progressBarFill.style.width = `${percentage}%`;
        progressHandle.style.left = `${percentage}%`;
        
        currentTimeEl.textContent = formatTime(current);
    }

    // Adjust Volume Control UI
    function updateVolumeUI(volume) {
        volumeBarFill.style.width = `${volume * 100}%`;
        
        let iconClass = 'fa-solid fa-volume-high';
        if (volume === 0) {
            iconClass = 'fa-solid fa-volume-xmark';
        } else if (volume < 0.3) {
            iconClass = 'fa-solid fa-volume-off';
        } else if (volume < 0.6) {
            iconClass = 'fa-solid fa-volume-low';
        }
        
        volumeBtn.querySelector('i').className = iconClass;
    }

    // Utilities - format seconds to MM:SS
    function formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
});
