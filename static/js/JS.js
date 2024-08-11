// pagination.js

const songsPerPage = 6;
let currentPage = 1;
let songs = []; // This should be populated with your actual song data

function renderSongs() {
    const songsContainer = document.getElementById('songs-container');
    songsContainer.innerHTML = '';

    const startIndex = (currentPage - 1) * songsPerPage;
    const endIndex = startIndex + songsPerPage;

    const currentSongs = songs.slice(startIndex, endIndex);

    currentSongs.forEach(song => {
        const songCard = document.createElement('div');
        songCard.classList.add('song-card');

        songCard.innerHTML = `
            <img src="${song.track.album.images[0].url}" alt="${song.track.name} cover" class="song-cover">
            <div class="song-details">
                <strong class="song-title">${song.track.name}</strong>
                <span class="song-artist">${song.track.artists[0].name}</span>
            </div>
        `;

        songsContainer.appendChild(songCard);
    });

    document.getElementById('page-info').textContent = `Page ${currentPage} of ${Math.ceil(songs.length / songsPerPage)}`;
}

function setupPagination() {
    document.getElementById('prev-button').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderSongs();
        }
    });

    document.getElementById('next-button').addEventListener('click', () => {
        if (currentPage < Math.ceil(songs.length / songsPerPage)) {
            currentPage++;
            renderSongs();
        }
    });
}

// Fetch your songs data and then initialize
// This is where you'd load songs, e.g., from a server
// For this example, assume songs are loaded directly into the songs array
songs = [...] // Populate this array with your songs
renderSongs();
setupPagination();
