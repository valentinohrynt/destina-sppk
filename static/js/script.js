// static/js/script.js

document.addEventListener('DOMContentLoaded', function () {
    const animatedElements = document.querySelectorAll('.card');
    animatedElements.forEach(element => {
        element.classList.add('fade-in-on-load');
        setTimeout(() => {
            element.classList.add('is-visible');
        }, 10);
    });

    // Form submission loading spinner
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const button = e.submitter;
            if (button && button.tagName === 'BUTTON') {
                button.innerHTML = '<span class="loading"></span> Memproses...';
            }
        });
    });

    const music = document.getElementById('backgroundMusic');
    const muteButton = document.getElementById('muteButton');
    const songNameDisplay = document.getElementById('songName');

    const playlist = [
        { name: 'Sound of Java Orchestra', src: '/static/audio/sound_of_java_orchestra.ogg' },
        { name: 'Sabilulungan', src: '/static/audio/sabilulungan.ogg' },
    ];

    let currentSongIndex = localStorage.getItem('music_songIndex') ? parseInt(localStorage.getItem('music_songIndex')) : 0;
    if (playlist.length > 0) {
        currentSongIndex = localStorage.getItem('music_songIndex') ? parseInt(localStorage.getItem('music_songIndex')) : Math.floor(Math.random() * playlist.length);
    }


    function loadSong(songIndex) {
        if (playlist.length === 0) {
            if (songNameDisplay) songNameDisplay.textContent = "Tidak ada lagu";
            return;
        }
        songIndex = songIndex % playlist.length;
        const song = playlist[songIndex];
        music.src = song.src;
        if (songNameDisplay) songNameDisplay.textContent = song.name;

        music.currentTime = parseFloat(localStorage.getItem('music_currentTime')) || 0;

        // Atur status mute berdasarkan localStorage, defaultnya tidak mute jika belum ada setting
        music.muted = localStorage.getItem('music_isMuted') === 'true';
        updateMuteButton();

        // Coba putar. Jika gagal karena autoplay, akan ditangkap.
        // Jika berhasil tapi muted, akan berputar tanpa suara.
        music.play().catch(error => {
            console.log("Autoplay dicegah. Pengguna harus berinteraksi dulu. Error:", error);
            // Anda bisa menambahkan UI feedback di sini jika mau, misal ikon play/pause di tombol mute
        });
    }

    function updateMuteButton() {
        if (muteButton) { // Pastikan tombol ada
            muteButton.innerHTML = music.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
        }
    }

    if (muteButton && music) {
        muteButton.addEventListener('click', function () {
            music.muted = !music.muted;
            localStorage.setItem('music_isMuted', music.muted);
            updateMuteButton();

            // Jika musik di-unmute dan sedang di-pause (mungkin karena autoplay gagal), coba putar lagi.
            if (!music.muted && music.paused) {
                music.play().catch(e => console.log("Gagal play setelah interaksi unmute:", e));
            }
        });
    }

    if (music) {
        music.addEventListener('timeupdate', function () {
            localStorage.setItem('music_currentTime', music.currentTime);
        });

        music.addEventListener('ended', function () {
            if (playlist.length > 0) {
                currentSongIndex = (currentSongIndex + 1) % playlist.length;
                localStorage.setItem('music_songIndex', currentSongIndex);
                localStorage.setItem('music_currentTime', 0);
                loadSong(currentSongIndex);
            }
        });
    }

    if (playlist.length > 0 && music) {
        loadSong(currentSongIndex);
    } else if (songNameDisplay) {
        songNameDisplay.textContent = "Tidak ada lagu dalam playlist.";
    }


    const resultsCard = document.getElementById('results-card');
    const scrollButtonsContainer = document.querySelector('.scroll-buttons');

    if (resultsCard) {
        if (scrollButtonsContainer) scrollButtonsContainer.style.display = 'flex';

        const scrollTopBtn = document.getElementById('scrollTopBtn');
        const scrollEndBtn = document.getElementById('scrollEndBtn');
        const endMarker = document.getElementById('end-of-page-marker');

        if (scrollTopBtn) {
            scrollTopBtn.addEventListener('click', function (e) {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        if (scrollEndBtn && endMarker) {
            scrollEndBtn.addEventListener('click', function (e) {
                e.preventDefault();
                endMarker.scrollIntoView({ behavior: 'smooth' });
            });
        }
    } else {
        if (scrollButtonsContainer) scrollButtonsContainer.style.display = 'none';
    }
});

const styleSheet = document.createElement("style");
styleSheet.innerText = `
    .fade-in-on-load {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.6s ease-out, transform 0.6s ease-out;
    }
    .fade-in-on-load.is-visible {
        opacity: 1;
        transform: translateY(0);
    }
    .song-info {
        font-size: 0.8rem;
        color: var(--dark-slate);
        max-width: 150px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
`;
document.head.appendChild(styleSheet);
