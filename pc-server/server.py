import threading
import requests as req
import spotipy
from flask import Flask, request, jsonify
from spotify_control import SpotifyController
from tts_engine import TTSEngine

app = Flask(__name__)
spotify = SpotifyController()
tts = TTSEngine()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'})


@app.route('/token', methods=['GET'])
def token():
    # Retourne le token Spotify actuel pour que n8n puisse faire ses appels API
    access_token = spotify.sp.auth_manager.get_access_token(as_dict=False)
    return jsonify({'access_token': access_token})


@app.route('/currently-playing', methods=['GET'])
def currently_playing():
    try:
        track = spotify.get_current_track()
        return jsonify(track or {})
    except Exception as e:
        return jsonify({'error': str(e), 'id': None}), 200


@app.route('/speak', methods=['POST'])
def speak():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'error': 'text requis'}), 400

    def speak_with_control():
        spotify.pause()
        tts.speak(text)
        spotify.resume()

    threading.Thread(target=speak_with_control, daemon=True).start()
    return jsonify({'status': 'ok'})


@app.route('/recently-played', methods=['GET'])
def recently_played():
    try:
        results = spotify.sp.current_user_recently_played(limit=50)
        tracks = [{
            'title': item['track']['name'],
            'artist': item['track']['artists'][0]['name'],
            'played_at': item['played_at'],
        } for item in results.get('items', [])]
        return jsonify({'tracks': tracks})
    except Exception as e:
        return jsonify({'tracks': [], 'error': str(e)})


@app.route('/create-playlist', methods=['POST'])
def create_playlist():
    try:
        data = request.get_json()
        playlist_name = data.get('playlist_name', 'TuneZine Playlist')
        tracks = data.get('tracks', [])  # [{"title": "...", "artist": "..."}]

        # Rechercher chaque track sur Spotify
        uris = []
        for track in tracks:
            query = f"track:{track['title']} artist:{track['artist']}"
            results = spotify.sp.search(q=query, type='track', limit=1)
            items = results.get('tracks', {}).get('items', [])
            if items:
                uris.append(items[0]['uri'])

        if not uris:
            return jsonify({'error': 'Aucun titre trouvé sur Spotify'}), 400

        # Créer la playlist via /me/playlists
        token = spotify.sp.auth_manager.get_access_token(as_dict=False)
        resp = req.post(
            'https://api.spotify.com/v1/me/playlists',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'name': playlist_name, 'public': True, 'description': 'Créée par TuneZine AI'}
        )
        playlist = resp.json()

        # Lancer la lecture immédiatement avec les URIs
        play_resp = req.put(
            'https://api.spotify.com/v1/me/player/play',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            json={'uris': uris}
        )
        print(f"Play response: {play_resp.status_code} - {play_resp.text}")

        return jsonify({
            'playlist_id': playlist['id'],
            'playlist_url': playlist['external_urls']['spotify'],
            'tracks_added': len(uris),
            'playlist_name': playlist_name,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=False)
