import os
import ctypes
import subprocess
import hashlib
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()


def _get_spotify_window_title():
    """Lit le titre de la fenêtre Spotify Desktop (fonctionne sans Premium)."""
    try:
        result = subprocess.run(
            ['powershell', '-Command',
             'Get-Process -Name Spotify -ErrorAction SilentlyContinue | '
             'Where-Object {$_.MainWindowTitle -ne ""} | '
             'Select-Object -ExpandProperty MainWindowTitle -First 1'],
            capture_output=True, text=True, timeout=3
        )
        title = result.stdout.strip()
        # Spotify affiche "Artiste - Titre" quand un morceau joue
        if title and ' - ' in title and title != 'Spotify':
            return title
    except Exception:
        pass
    return None


class SpotifyController:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope='user-read-currently-playing user-modify-playback-state user-read-playback-state user-read-recently-played playlist-modify-public playlist-modify-private',
            open_browser=False,
        ))

    def get_current_track(self):
        # Essai via API Spotify (requiert Premium)
        try:
            result = self.sp.currently_playing()
            if result and result.get('is_playing'):
                item = result.get('item')
                if item:
                    return {
                        'id': item['id'],
                        'title': item['name'],
                        'artist': item['artists'][0]['name'],
                        'album': item['album']['name'],
                        'duration_ms': item['duration_ms'],
                        'progress_ms': result['progress_ms'],
                    }
        except Exception:
            pass

        # Fallback : lecture du titre de la fenêtre Windows (gratuit)
        title = _get_spotify_window_title()
        if title:
            parts = title.split(' - ', 1)
            artist = parts[0].strip()
            song = parts[1].strip() if len(parts) > 1 else title
            # ID synthétique basé sur le titre pour détecter les changements
            fake_id = hashlib.md5(title.encode()).hexdigest()
            return {
                'id': fake_id,
                'title': song,
                'artist': artist,
                'album': 'Album inconnu',
                'duration_ms': 0,
                'progress_ms': 0,
            }
        return None

    def pause(self):
        # Essai via API, fallback touche média Windows
        try:
            self.sp.pause_playback()
        except Exception:
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)

    def resume(self):
        # Essai via API, fallback touche média Windows
        try:
            self.sp.start_playback()
        except Exception:
            ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
