# Spotify Music Companion — Plan d'Implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire un agent n8n qui analyse chaque morceau Spotify en temps réel, envoie l'analyse sur Telegram et la lit à voix haute sur le PC, génère des playlists selon l'humeur, et produit un résumé quotidien — 100% gratuit.

**Architecture:** Un serveur Python Flask local gère la pause/TTS/reprise Spotify sur le PC. Quatre workflows n8n orchestrent la détection de morceaux (polling 5s), la génération de playlists via Telegram bot, le résumé quotidien à 18h, et l'analyse manuelle à la demande. Le LLM utilisé est Groq (Llama 3.3 70B, gratuit).

**Tech Stack:** Python 3.10+, Flask, spotipy, gTTS, pygame, n8n self-hosted, Groq API, Spotify Web API, Telegram Bot API

---

## Structure des fichiers

```
agents/
├── pc-server/
│   ├── spotify_control.py     # Pause/reprise/infos Spotify via spotipy
│   ├── tts_engine.py          # Génération et lecture audio TTS
│   ├── server.py              # API Flask exposée à n8n
│   ├── requirements.txt       # Dépendances Python
│   ├── .env                   # Credentials (gitignore)
│   └── tests/
│       ├── test_spotify_control.py
│       ├── test_tts_engine.py
│       └── test_server.py
└── n8n-workflows/
    ├── 01-spotify-watcher.json     # Import dans n8n
    ├── 02-playlist-generator.json
    ├── 03-daily-summary.json
    └── 04-manual-analyze.json
```

---

## Task 1 : Scaffolding du projet

**Files:**
- Create: `pc-server/requirements.txt`
- Create: `pc-server/.env`
- Create: `pc-server/tests/__init__.py`

- [ ] **Étape 1 : Créer les dossiers**

```powershell
New-Item -ItemType Directory -Force -Path "pc-server/tests"
New-Item -ItemType Directory -Force -Path "n8n-workflows"
New-Item -ItemType File -Path "pc-server/tests/__init__.py"
```

- [ ] **Étape 2 : Créer requirements.txt**

Contenu de `pc-server/requirements.txt` :
```
flask==3.0.3
spotipy==2.23.0
gTTS==2.5.1
pygame==2.5.2
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
requests==2.31.0
```

- [ ] **Étape 3 : Créer .env**

Contenu de `pc-server/.env` :
```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
TELEGRAM_CHAT_ID=your_chat_id_here
```

- [ ] **Étape 4 : Installer les dépendances**

```powershell
cd pc-server
pip install -r requirements.txt
```

Résultat attendu : `Successfully installed flask-3.0.3 spotipy-2.23.0 ...`

- [ ] **Étape 5 : Commit**

```powershell
git init
git add pc-server/requirements.txt pc-server/.env
git commit -m "chore: scaffolding projet spotify-music-companion"
```

---

## Task 2 : spotify_control.py

**Files:**
- Create: `pc-server/spotify_control.py`
- Create: `pc-server/tests/test_spotify_control.py`

- [ ] **Étape 1 : Écrire les tests**

Contenu de `pc-server/tests/test_spotify_control.py` :
```python
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


@pytest.fixture
def controller():
    with patch('spotify_control.spotipy.Spotify'), \
         patch('spotify_control.SpotifyOAuth'):
        from spotify_control import SpotifyController
        ctrl = SpotifyController.__new__(SpotifyController)
        ctrl.sp = MagicMock()
        return ctrl


def test_get_current_track_returns_none_when_nothing_playing(controller):
    controller.sp.currently_playing.return_value = None
    from spotify_control import SpotifyController
    result = controller.get_current_track()
    assert result is None


def test_get_current_track_returns_none_when_not_playing(controller):
    controller.sp.currently_playing.return_value = {'is_playing': False}
    result = controller.get_current_track()
    assert result is None


def test_get_current_track_returns_track_dict(controller):
    controller.sp.currently_playing.return_value = {
        'is_playing': True,
        'item': {
            'id': 'abc123',
            'name': 'Power',
            'artists': [{'name': 'Kanye West'}],
            'album': {'name': 'My Beautiful Dark Twisted Fantasy'},
            'duration_ms': 292000,
        },
        'progress_ms': 5000,
    }
    result = controller.get_current_track()
    assert result == {
        'id': 'abc123',
        'title': 'Power',
        'artist': 'Kanye West',
        'album': 'My Beautiful Dark Twisted Fantasy',
        'duration_ms': 292000,
        'progress_ms': 5000,
    }


def test_pause_calls_spotify_api(controller):
    controller.pause()
    controller.sp.pause_playback.assert_called_once()


def test_resume_calls_spotify_api(controller):
    controller.resume()
    controller.sp.start_playback.assert_called_once()
```

- [ ] **Étape 2 : Lancer les tests (vérifier qu'ils échouent)**

```powershell
cd pc-server
pytest tests/test_spotify_control.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'spotify_control'`

- [ ] **Étape 3 : Implémenter spotify_control.py**

Contenu de `pc-server/spotify_control.py` :
```python
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()


class SpotifyController:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope='user-read-currently-playing user-modify-playback-state user-read-playback-state user-read-recently-played',
            open_browser=False,
        ))

    def get_current_track(self):
        result = self.sp.currently_playing()
        if not result or not result.get('is_playing'):
            return None
        item = result['item']
        return {
            'id': item['id'],
            'title': item['name'],
            'artist': item['artists'][0]['name'],
            'album': item['album']['name'],
            'duration_ms': item['duration_ms'],
            'progress_ms': result['progress_ms'],
        }

    def pause(self):
        self.sp.pause_playback()

    def resume(self):
        self.sp.start_playback()
```

- [ ] **Étape 4 : Lancer les tests (vérifier qu'ils passent)**

```powershell
pytest tests/test_spotify_control.py -v
```

Résultat attendu : `5 passed`

- [ ] **Étape 5 : Commit**

```powershell
git add pc-server/spotify_control.py pc-server/tests/test_spotify_control.py
git commit -m "feat: spotify_control - pause/resume/now-playing"
```

---

## Task 3 : tts_engine.py

**Files:**
- Create: `pc-server/tts_engine.py`
- Create: `pc-server/tests/test_tts_engine.py`

- [ ] **Étape 1 : Écrire les tests**

Contenu de `pc-server/tests/test_tts_engine.py` :
```python
import pytest
from unittest.mock import MagicMock, patch, call


def test_speak_generates_mp3_and_plays(tmp_path):
    with patch('tts_engine.gTTS') as mock_gtts, \
         patch('tts_engine.pygame.mixer') as mock_mixer, \
         patch('tts_engine.tempfile.mktemp', return_value=str(tmp_path / 'test.mp3')), \
         patch('tts_engine.os.unlink') as mock_unlink:

        mock_tts_instance = MagicMock()
        mock_gtts.return_value = mock_tts_instance
        mock_mixer.music.get_busy.return_value = False

        from tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine.lang = 'fr'
        engine.speak("Bonjour")

        mock_gtts.assert_called_once_with(text="Bonjour", lang='fr')
        mock_tts_instance.save.assert_called_once()
        mock_mixer.music.load.assert_called_once()
        mock_mixer.music.play.assert_called_once()
        mock_unlink.assert_called_once()


def test_speak_uses_french_by_default():
    with patch('tts_engine.gTTS') as mock_gtts, \
         patch('tts_engine.pygame.mixer'), \
         patch('tts_engine.tempfile.mktemp', return_value='/tmp/test.mp3'), \
         patch('tts_engine.os.unlink'):
        mock_gtts.return_value = MagicMock()
        from tts_engine import TTSEngine
        engine = TTSEngine.__new__(TTSEngine)
        engine.lang = 'fr'
        engine.speak("test")
        _, kwargs = mock_gtts.call_args
        assert kwargs['lang'] == 'fr'
```

- [ ] **Étape 2 : Lancer les tests (vérifier qu'ils échouent)**

```powershell
pytest tests/test_tts_engine.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'tts_engine'`

- [ ] **Étape 3 : Implémenter tts_engine.py**

Contenu de `pc-server/tts_engine.py` :
```python
import os
import tempfile
import pygame
from gtts import gTTS


class TTSEngine:
    def __init__(self, lang: str = 'fr'):
        self.lang = lang
        pygame.mixer.init()

    def speak(self, text: str):
        tts = gTTS(text=text, lang=self.lang)
        tmp_path = tempfile.mktemp(suffix='.mp3')
        tts.save(tmp_path)
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        os.unlink(tmp_path)
```

- [ ] **Étape 4 : Lancer les tests (vérifier qu'ils passent)**

```powershell
pytest tests/test_tts_engine.py -v
```

Résultat attendu : `2 passed`

- [ ] **Étape 5 : Commit**

```powershell
git add pc-server/tts_engine.py pc-server/tests/test_tts_engine.py
git commit -m "feat: tts_engine - text-to-speech francais via gTTS"
```

---

## Task 4 : server.py

**Files:**
- Create: `pc-server/server.py`
- Create: `pc-server/tests/test_server.py`

- [ ] **Étape 1 : Écrire les tests**

Contenu de `pc-server/tests/test_server.py` :
```python
import pytest
import json
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    with patch('server.SpotifyController'), \
         patch('server.TTSEngine'):
        from server import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client


def test_health_returns_ok(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'running'


def test_speak_returns_ok(client):
    response = client.post('/speak',
        data=json.dumps({'text': 'Bonjour', 'type': 'intro'}),
        content_type='application/json'
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_speak_requires_text(client):
    response = client.post('/speak',
        data=json.dumps({}),
        content_type='application/json'
    )
    assert response.status_code == 400
```

- [ ] **Étape 2 : Lancer les tests (vérifier qu'ils échouent)**

```powershell
pytest tests/test_server.py -v
```

Résultat attendu : `ModuleNotFoundError: No module named 'server'`

- [ ] **Étape 3 : Implémenter server.py**

Contenu de `pc-server/server.py` :
```python
import threading
from flask import Flask, request, jsonify
from spotify_control import SpotifyController
from tts_engine import TTSEngine

app = Flask(__name__)
spotify = SpotifyController()
tts = TTSEngine()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'running'})


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


if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=False)
```

- [ ] **Étape 4 : Lancer les tests (vérifier qu'ils passent)**

```powershell
pytest tests/test_server.py -v
```

Résultat attendu : `3 passed`

- [ ] **Étape 5 : Lancer tous les tests**

```powershell
pytest tests/ -v
```

Résultat attendu : `10 passed`

- [ ] **Étape 6 : Commit**

```powershell
git add pc-server/server.py pc-server/tests/test_server.py
git commit -m "feat: flask server - endpoint /speak avec pause/TTS/reprise"
```

---

## Task 5 : Credentials Spotify + lancement serveur

**Files:** aucun (configuration externe)

- [ ] **Étape 1 : Créer l'app Spotify**

1. Aller sur https://developer.spotify.com/dashboard
2. Cliquer **Create App**
3. Nom : `Music Companion`, Redirect URI : `http://localhost:8888/callback`
4. Cocher **Web API**
5. Copier **Client ID** et **Client Secret** dans `pc-server/.env`

- [ ] **Étape 2 : Autoriser Spotify (première connexion)**

```powershell
cd pc-server
python -c "from spotify_control import SpotifyController; SpotifyController()"
```

Un navigateur s'ouvre → accepter les permissions → copier l'URL de redirection dans le terminal si demandé.
Un fichier `.cache` se crée automatiquement (token sauvegardé).

- [ ] **Étape 3 : Vérifier la connexion**

```powershell
python -c "
from spotify_control import SpotifyController
ctrl = SpotifyController()
track = ctrl.get_current_track()
print('Track actuel:', track)
"
```

Résultat attendu (si Spotify joue) : `Track actuel: {'id': '...', 'title': '...', ...}`
Résultat attendu (si rien ne joue) : `Track actuel: None`

- [ ] **Étape 4 : Lancer le serveur PC**

```powershell
python server.py
```

Résultat attendu : `* Running on http://localhost:5001`

- [ ] **Étape 5 : Tester le endpoint /speak**

Dans un autre terminal :
```powershell
Invoke-RestMethod -Uri "http://localhost:5001/health" -Method Get
```

Résultat attendu : `status: running`

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/speak" -Method Post `
  -ContentType "application/json" `
  -Body '{"text": "Test de la voix française.", "type": "intro"}'
```

Résultat attendu : voix française parle sur les enceintes + `status: ok`

---

## Task 6 : Installation n8n + credentials

**Files:** aucun (configuration n8n)

- [ ] **Étape 1 : Installer n8n**

```powershell
npm install -g n8n
```

- [ ] **Étape 2 : Lancer n8n**

```powershell
n8n start
```

Résultat attendu : `Editor is now accessible via: http://localhost:5678`

- [ ] **Étape 3 : Créer le bot Telegram**

1. Ouvrir Telegram → chercher `@BotFather`
2. Envoyer `/newbot` → donner un nom → copier le **token**
3. Envoyer `/start` à ton bot pour l'activer
4. Récupérer ton **Chat ID** : aller sur `https://api.telegram.org/bot{TOKEN}/getUpdates` après avoir envoyé un message au bot

- [ ] **Étape 4 : Créer le compte Groq**

1. Aller sur https://console.groq.com
2. Créer un compte gratuit
3. Dans **API Keys** → créer une clé → copier

- [ ] **Étape 5 : Configurer les credentials dans n8n**

Dans n8n → **Settings > Credentials** :

**Credential Spotify OAuth2 :**
- Type : `Spotify OAuth2 API`
- Client ID : (depuis developer.spotify.com)
- Client Secret : (depuis developer.spotify.com)
- Scopes : `user-read-currently-playing user-modify-playback-state user-read-playback-state user-read-recently-played playlist-modify-public`
- Cliquer **Connect** → autoriser dans le navigateur

**Credential Telegram :**
- Type : `Telegram API`
- Access Token : (depuis @BotFather)

**Variable d'environnement Groq :**
Dans **Settings > Environment Variables** :
- `GROQ_API_KEY` = ta clé Groq

---

## Task 7 : Workflow 1 — Spotify Watcher (détection + analyse)

**Files:**
- Create: `n8n-workflows/01-spotify-watcher.json`

Ce workflow poll Spotify toutes les 5s, détecte les changements de titre, et appelle Groq pour l'analyse.

- [ ] **Étape 1 : Créer le workflow dans n8n**

Dans n8n → **New Workflow** → nommer `01-spotify-watcher`

- [ ] **Étape 2 : Ajouter le Schedule Trigger**

- Node : `Schedule Trigger`
- Mode : `Interval`
- Interval : `5` secondes

- [ ] **Étape 3 : Ajouter le node HTTP Request Spotify**

- Node : `HTTP Request`
- Nom : `Spotify Now Playing`
- Method : `GET`
- URL : `https://api.spotify.com/v1/me/player/currently-playing`
- Authentication : `Predefined Credential Type` → `Spotify OAuth2 API`
- Options → **Ignore Response Code** : activé (retourne 204 si rien ne joue)

- [ ] **Étape 4 : Ajouter le node Code — Détecteur de changement**

- Node : `Code`
- Nom : `Detect Track Change`
- Language : JavaScript
- Code :

```javascript
const workflowStaticData = $getWorkflowStaticData('global');
const response = $input.first().json;

// Rien en lecture
if (!response || !response.item || !response.is_playing) {
  return [{ json: { changed: false } }];
}

const currentTrack = {
  id: response.item.id,
  title: response.item.name,
  artist: response.item.artists[0].name,
  album: response.item.album.name,
  duration_ms: response.item.duration_ms,
};

const previousId = workflowStaticData.currentTrackId;
const previousTrack = workflowStaticData.currentTrack || null;

// Même morceau, pas de changement
if (previousId === currentTrack.id) {
  return [{ json: { changed: false } }];
}

// Nouveau morceau détecté
workflowStaticData.currentTrackId = currentTrack.id;
workflowStaticData.currentTrack = currentTrack;

return [{
  json: {
    changed: true,
    currentTrack,
    previousTrack,
  }
}];
```

- [ ] **Étape 5 : Ajouter le node IF — Nouveau morceau ?**

- Node : `IF`
- Nom : `New Track?`
- Condition : `{{ $json.changed }}` **equals** `true`

- [ ] **Étape 6 : Branche True — Appel Groq pour analyse intro**

- Node : `HTTP Request`
- Nom : `Groq Intro Analysis`
- Method : `POST`
- URL : `https://api.groq.com/openai/v1/chat/completions`
- Headers :
  - `Authorization` : `Bearer {{ $env.GROQ_API_KEY }}`
  - `Content-Type` : `application/json`
- Body (JSON) :

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "Tu es un expert musical et culturel. Réponds toujours en français. Sois concis, profond, et inspirant."
    },
    {
      "role": "user",
      "content": "Analyse ce morceau en 2 parties distinctes séparées par '|||'.\nPARTIE 1 (2-3 phrases): De quoi parle ce morceau concrètement ?\nPARTIE 2 (1-2 phrases): Quel est le message profond ou l'intention artistique ?\n\nMorceau: {{ $json.currentTrack.title }} de {{ $json.currentTrack.artist }}, album: {{ $json.currentTrack.album }}"
    }
  ],
  "max_tokens": 300,
  "temperature": 0.7
}
```

- [ ] **Étape 7 : Appel Groq pour analyse outro (titre précédent)**

- Node : `HTTP Request`
- Nom : `Groq Outro Analysis`
- Connecter en parallèle depuis le node IF (branche True) — uniquement si `previousTrack` existe
- Ajouter un IF avant : `{{ $json.previousTrack !== null }}` equals `true`
- Method : `POST`
- URL : `https://api.groq.com/openai/v1/chat/completions`
- Headers : même qu'au-dessus
- Body (JSON) :

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "Tu es un expert musical. Réponds en français. Sois bref et percutant."
    },
    {
      "role": "user",
      "content": "En une seule phrase impactante, dis ce qu'il faut retenir de ce morceau qu'on vient de finir d'écouter.\n\nMorceau: {{ $json.previousTrack.title }} de {{ $json.previousTrack.artist }}"
    }
  ],
  "max_tokens": 100,
  "temperature": 0.7
}
```

- [ ] **Étape 8 : Commit du workflow exporté**

Dans n8n → menu du workflow → **Download** → sauvegarder dans `n8n-workflows/01-spotify-watcher.json`

```powershell
git add n8n-workflows/01-spotify-watcher.json
git commit -m "feat: workflow spotify-watcher - detection + analyse Groq"
```

---

## Task 8 : Workflow 1 — Sorties Telegram + PC Audio

**Files:**
- Modify: `n8n-workflows/01-spotify-watcher.json`

- [ ] **Étape 1 : Node Code — Formater le message intro Telegram**

- Node : `Code`
- Nom : `Format Intro Message`
- Connecter après `Groq Intro Analysis`
- Code :

```javascript
const track = $('Detect Track Change').first().json.currentTrack;
const groqResponse = $input.first().json.choices[0].message.content;
const parts = groqResponse.split('|||');
const description = parts[0] ? parts[0].trim() : groqResponse.trim();
const deepMessage = parts[1] ? parts[1].trim() : '';

let message = `🎵 *${track.title}* — ${track.artist}\n📀 ${track.album}\n\n`;
message += `📖 *De quoi ça parle :*\n${description}\n`;
if (deepMessage) {
  message += `\n💭 *Message profond :*\n${deepMessage}`;
}

return [{ json: { message, track } }];
```

- [ ] **Étape 2 : Node Telegram — Envoyer l'intro**

- Node : `Telegram`
- Nom : `Telegram Intro`
- Credential : ta credential Telegram
- Operation : `Send Message`
- Chat ID : ton Chat ID (ex : `123456789`)
- Text : `{{ $json.message }}`
- Additional Fields → **Parse Mode** : `Markdown`

- [ ] **Étape 3 : Node HTTP Request — PC Audio Intro**

- Node : `HTTP Request`
- Nom : `PC Audio Intro`
- Method : `POST`
- URL : `http://localhost:5001/speak`
- Body (JSON) :

```json
{
  "text": "{{ $('Format Intro Message').first().json.message.replace(/[*_]/g, '') }}",
  "type": "intro"
}
```

- Options → **Continue On Fail** : activé (si le serveur PC est éteint, le workflow continue)

- [ ] **Étape 4 : Node Code — Formater le message outro Telegram**

- Node : `Code`
- Nom : `Format Outro Message`
- Connecter après `Groq Outro Analysis`
- Code :

```javascript
const track = $('Detect Track Change').first().json.previousTrack;
const groqResponse = $input.first().json.choices[0].message.content;

return [{
  json: {
    message: `✅ *À retenir :*\n${groqResponse.trim()}`,
    track
  }
}];
```

- [ ] **Étape 5 : Node Telegram — Envoyer l'outro**

- Node : `Telegram`
- Nom : `Telegram Outro`
- Chat ID : ton Chat ID
- Text : `{{ $json.message }}`
- Parse Mode : `Markdown`

- [ ] **Étape 6 : Node HTTP Request — PC Audio Outro**

- Node : `HTTP Request`
- Nom : `PC Audio Outro`
- Method : `POST`
- URL : `http://localhost:5001/speak`
- Body (JSON) : `{ "text": "{{ $json.message.replace(/[*_]/g, '') }}", "type": "outro" }`
- **Continue On Fail** : activé

- [ ] **Étape 7 : Activer le workflow et tester**

1. Dans n8n → cliquer **Activate** (toggle en haut à droite)
2. Lancer Spotify sur ton PC avec un morceau
3. Passer au morceau suivant
4. Vérifier dans n8n → **Executions** : doit montrer une exécution avec `changed: true`
5. Vérifier Telegram : message intro reçu
6. Vérifier PC : voix qui parle

- [ ] **Étape 8 : Commit**

```powershell
# Exporter le workflow depuis n8n et sauvegarder
git add n8n-workflows/01-spotify-watcher.json
git commit -m "feat: workflow spotify-watcher complet - telegram + pc audio"
```

---

## Task 9 : Workflow 2 — Playlist Generator (bot Telegram)

**Files:**
- Create: `n8n-workflows/02-playlist-generator.json`

- [ ] **Étape 1 : Créer le workflow**

Dans n8n → **New Workflow** → nommer `02-playlist-generator`

- [ ] **Étape 2 : Node Telegram Trigger**

- Node : `Telegram Trigger`
- Nom : `Telegram Bot`
- Credential : ta credential Telegram
- Updates : `message`

- [ ] **Étape 3 : Node Code — Parser l'intention**

- Node : `Code`
- Nom : `Parse User Intent`
- Code :

```javascript
const text = $input.first().json.message?.text || '';
const chatId = $input.first().json.message?.chat?.id;
const hour = new Date().getHours();

let timeContext = 'matin';
if (hour >= 12 && hour < 18) timeContext = 'après-midi';
else if (hour >= 18 && hour < 22) timeContext = 'soirée';
else if (hour >= 22 || hour < 6) timeContext = 'nuit';

const presets = {
  'concentration 🧠': 'deep focus, concentration intense, travail',
  'soirée 🌙': 'ambiance soirée détendue, bonne humeur',
  'sport ⚡': 'énergie, motivation, sport, intensité',
  'détente 🌿': 'relaxation, calme, repos',
  'sad mood 🌧️': 'mélancolie, introspection, émotions profondes',
};

const lowerText = text.toLowerCase();
let mood = presets[lowerText] || text;

return [{ json: { mood, timeContext, chatId, originalText: text } }];
```

- [ ] **Étape 4 : Node HTTP Request — Historique Spotify**

- Node : `HTTP Request`
- Nom : `Spotify Recent Tracks`
- Method : `GET`
- URL : `https://api.spotify.com/v1/me/player/recently-played?limit=50`
- Authentication : `Predefined Credential Type` → `Spotify OAuth2 API`

- [ ] **Étape 5 : Node Code — Extraire les artistes/titres récents**

- Node : `Code`
- Nom : `Extract Recent Tracks`
- Code :

```javascript
const items = $input.first().json.items || [];
const tracks = items.map(item => ({
  title: item.track.name,
  artist: item.track.artists[0].name,
  id: item.track.id,
}));
const mood = $('Parse User Intent').first().json.mood;
const timeContext = $('Parse User Intent').first().json.timeContext;
const chatId = $('Parse User Intent').first().json.chatId;

return [{ json: { tracks, mood, timeContext, chatId } }];
```

- [ ] **Étape 6 : Node HTTP Request — Groq sélectionne les titres**

- Node : `HTTP Request`
- Nom : `Groq Playlist Selection`
- Method : `POST`
- URL : `https://api.groq.com/openai/v1/chat/completions`
- Headers : `Authorization: Bearer {{ $env.GROQ_API_KEY }}`
- Body (JSON) :

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "Tu es un DJ expert. Réponds UNIQUEMENT avec un JSON valide, rien d'autre."
    },
    {
      "role": "user",
      "content": "Contexte: {{ $json.timeContext }}, humeur/activité: {{ $json.mood }}.\n\nHistorique récent (50 titres): {{ JSON.stringify($json.tracks) }}\n\nSélectionne 7 titres de cet historique qui correspondent parfaitement au contexte et à l'humeur. Génère aussi un nom de playlist créatif.\n\nRéponds avec ce JSON exact:\n{\"playlist_name\": \"...\", \"tracks\": [{\"id\": \"...\", \"title\": \"...\", \"artist\": \"...\"}]}"
    }
  ],
  "max_tokens": 800,
  "temperature": 0.8
}
```

- [ ] **Étape 7 : Node Code — Parser la réponse Groq**

- Node : `Code`
- Nom : `Parse Groq Playlist`
- Code :

```javascript
const content = $input.first().json.choices[0].message.content;
const chatId = $('Extract Recent Tracks').first().json.chatId;

let parsed;
try {
  parsed = JSON.parse(content);
} catch(e) {
  const match = content.match(/\{[\s\S]*\}/);
  parsed = JSON.parse(match[0]);
}

return [{ json: { ...parsed, chatId } }];
```

- [ ] **Étape 8 : Node HTTP Request — Créer la playlist Spotify**

- Node : `HTTP Request`
- Nom : `Create Spotify Playlist`
- Method : `POST`
- URL : `https://api.spotify.com/v1/me/playlists`
- Authentication : Spotify OAuth2 API
- Body (JSON) :

```json
{
  "name": "{{ $json.playlist_name }}",
  "description": "Créée par Music Companion",
  "public": true
}
```

- [ ] **Étape 9a : Node Code — Préparer les URIs Spotify**

- Node : `Code`
- Nom : `Prepare Track URIs`
- Code :

```javascript
const playlist = $('Create Spotify Playlist').first().json;
const tracks = $('Parse Groq Playlist').first().json.tracks;
const uris = tracks.map(t => `spotify:track:${t.id}`);
const chatId = $('Parse Groq Playlist').first().json.chatId;
const playlistName = $('Parse Groq Playlist').first().json.playlist_name;

return [{ json: { playlistId: playlist.id, uris, tracks, chatId, playlistName } }];
```

- [ ] **Étape 9b : Node HTTP Request — Ajouter les titres à la playlist**

- Node : `HTTP Request`
- Nom : `Add Tracks to Playlist`
- Method : `POST`
- URL : `https://api.spotify.com/v1/playlists/{{ $json.playlistId }}/tracks`
- Authentication : Spotify OAuth2 API
- Body (JSON) :

```json
{
  "uris": {{ $json.uris }}
}
```

- [ ] **Étape 10 : Node HTTP Request — Lancer la playlist**

- Node : `HTTP Request`
- Nom : `Play Playlist`
- Method : `PUT`
- URL : `https://api.spotify.com/v1/me/player/play`
- Authentication : Spotify OAuth2 API
- Body (JSON) :

```json
{
  "context_uri": "spotify:playlist:{{ $json.playlistId }}"
}
```

- [ ] **Étape 11 : Node Code — Formater le message de confirmation**

- Node : `Code`
- Nom : `Format Confirmation`
- Code :

```javascript
const tracks = $('Parse Groq Playlist').first().json.tracks;
const playlistName = $('Parse Groq Playlist').first().json.playlist_name;
const chatId = $('Parse Groq Playlist').first().json.chatId;

const trackList = tracks.map(t => `• ${t.title} – ${t.artist}`).join('\n');
const message = `🎧 *Playlist créée :* "${playlistName}"\n${tracks.length} titres sélectionnés :\n${trackList}\n\n▶️ Lancée sur Spotify !`;

return [{ json: { message, chatId } }];
```

- [ ] **Étape 12 : Node Telegram — Envoyer la confirmation**

- Node : `Telegram`
- Chat ID : `{{ $json.chatId }}`
- Text : `{{ $json.message }}`
- Parse Mode : `Markdown`

- [ ] **Étape 13 : Envoyer les boutons de mood au démarrage**

Ajouter un second trigger — Node `Telegram Trigger` sur commande `/mood` :
- Node : `Telegram`
- Operation : `Send Message`
- Text : `Quel est ton humeur du moment ?`
- Additional Fields → **Reply Markup** (JSON) :

```json
{
  "inline_keyboard": [[
    {"text": "Concentration 🧠", "callback_data": "Concentration 🧠"},
    {"text": "Soirée 🌙", "callback_data": "Soirée 🌙"}
  ],[
    {"text": "Sport ⚡", "callback_data": "Sport ⚡"},
    {"text": "Détente 🌿", "callback_data": "Détente 🌿"}
  ],[
    {"text": "Sad mood 🌧️", "callback_data": "Sad mood 🌧️"}
  ]]
}
```

- [ ] **Étape 14 : Tester le workflow**

1. Envoyer `/mood` au bot Telegram → vérifier les boutons
2. Appuyer sur `Concentration 🧠`
3. Vérifier dans n8n Executions : workflow déclenché
4. Vérifier Spotify : nouvelle playlist créée et en lecture
5. Vérifier Telegram : message de confirmation reçu

- [ ] **Étape 15 : Commit**

```powershell
git add n8n-workflows/02-playlist-generator.json
git commit -m "feat: workflow playlist-generator - mood → Groq → Spotify playlist"
```

---

## Task 10 : Workflow 3 — Daily Summary (18h)

**Files:**
- Create: `n8n-workflows/03-daily-summary.json`

- [ ] **Étape 1 : Créer le workflow**

Dans n8n → **New Workflow** → nommer `03-daily-summary`

- [ ] **Étape 2 : Schedule Trigger à 18h**

- Node : `Schedule Trigger`
- Mode : `Every Day`
- Heure : `18:00`

- [ ] **Étape 3 : HTTP Request — Historique du jour**

- Node : `HTTP Request`
- Nom : `Spotify History`
- Method : `GET`
- URL : `https://api.spotify.com/v1/me/player/recently-played?limit=50`
- Authentication : Spotify OAuth2 API

- [ ] **Étape 4 : Node Code — Préparer les données pour Groq**

- Node : `Code`
- Nom : `Prepare Summary Data`
- Code :

```javascript
const items = $input.first().json.items || [];
const today = new Date().toLocaleDateString('fr-FR');

const tracks = items.map(item => ({
  title: item.track.name,
  artist: item.track.artists[0].name,
  playedAt: item.played_at,
}));

// Compter les artistes
const artistCount = {};
tracks.forEach(t => {
  artistCount[t.artist] = (artistCount[t.artist] || 0) + 1;
});
const topArtists = Object.entries(artistCount)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 3)
  .map(([name]) => name);

return [{ json: { tracks, topArtists, today, totalTracks: tracks.length } }];
```

- [ ] **Étape 5 : HTTP Request — Groq synthèse**

- Node : `HTTP Request`
- Nom : `Groq Daily Summary`
- Method : `POST`
- URL : `https://api.groq.com/openai/v1/chat/completions`
- Headers : `Authorization: Bearer {{ $env.GROQ_API_KEY }}`
- Body (JSON) :

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "Tu es un analyste musical et psychologue culturel. Réponds en français, de manière chaleureuse et personnelle."
    },
    {
      "role": "user",
      "content": "Voici les {{ $json.totalTracks }} morceaux écoutés aujourd'hui ({{ $json.today }}):\n{{ JSON.stringify($json.tracks) }}\n\nArtistes dominants: {{ $json.topArtists.join(', ') }}\n\nDonne-moi:\n1. Une synthèse des thèmes musicaux et émotionnels de la journée (3-4 phrases)\n2. 2-3 artistes à découvrir qui correspondraient à ces goûts\n\nFormat: THEMES|||ARTISTE1,ARTISTE2,ARTISTE3"
    }
  ],
  "max_tokens": 400,
  "temperature": 0.7
}
```

- [ ] **Étape 6 : Node Code — Formater le résumé**

- Node : `Code`
- Nom : `Format Daily Summary`
- Code :

```javascript
const content = $input.first().json.choices[0].message.content;
const data = $('Prepare Summary Data').first().json;
const parts = content.split('|||');
const themes = parts[0] ? parts[0].trim() : content;
const suggestions = parts[1] ? parts[1].trim().split(',').map(a => `• ${a.trim()}`) : [];

let message = `📊 *Ton journal musical du ${data.today}*\n\n`;
message += `🎵 ${data.totalTracks} titres écoutés\n`;
message += `🎨 Artistes dominants : ${data.topArtists.join(', ')}\n\n`;
message += `💭 *Thèmes du jour :*\n${themes}\n`;
if (suggestions.length > 0) {
  message += `\n🔭 *À découvrir :*\n${suggestions.join('\n')}`;
}

return [{ json: { message } }];
```

- [ ] **Étape 7 : Node Telegram — Envoyer le résumé**

- Node : `Telegram`
- Chat ID : ton Chat ID
- Text : `{{ $json.message }}`
- Parse Mode : `Markdown`

- [ ] **Étape 8 : Tester manuellement**

Dans n8n → cliquer **Execute Workflow** (sans attendre 18h)
Vérifier Telegram : résumé reçu avec thèmes + suggestions.

- [ ] **Étape 9 : Activer + Commit**

```powershell
git add n8n-workflows/03-daily-summary.json
git commit -m "feat: workflow daily-summary - resume 18h via Groq"
```

---

## Task 11 : Workflow 4 — Manual Analyze

**Files:**
- Create: `n8n-workflows/04-manual-analyze.json`

- [ ] **Étape 1 : Créer le workflow**

Dans n8n → **New Workflow** → nommer `04-manual-analyze`

- [ ] **Étape 2 : Telegram Trigger sur mot "analyse"**

- Node : `Telegram Trigger`
- Updates : `message`

- [ ] **Étape 3 : Node IF — Contient "analyse" ?**

- Node : `IF`
- Condition : `{{ $json.message.text.toLowerCase().includes('analyse') }}` equals `true`

- [ ] **Étape 4 : HTTP Request — Spotify Now Playing**

- Identique au node `Spotify Now Playing` du Workflow 1
- Authentication : Spotify OAuth2 API

- [ ] **Étape 5 : Node IF — Quelque chose joue ?**

- Condition : `{{ $json.item !== undefined }}` equals `true`

- [ ] **Étape 6 : Node Code — Extraire les infos**

- Code :

```javascript
const item = $input.first().json.item;
return [{
  json: {
    id: item.id,
    title: item.name,
    artist: item.artists[0].name,
    album: item.album.name,
    chatId: $('Telegram Trigger').first().json.message.chat.id,
  }
}];
```

- [ ] **Étape 7 : HTTP Request — Groq analyse complète**

- Identique au node `Groq Intro Analysis` du Workflow 1
- Adapter le contenu du message user pour inclure `$json.title`, `$json.artist`, `$json.album`

- [ ] **Étape 8 : Node Code — Formater + envoyer**

- Code : identique à `Format Intro Message` du Workflow 1
- Chat ID : `{{ $('Extraire les infos').first().json.chatId }}`

- [ ] **Étape 9 : Nodes Telegram + PC Audio**

- Identiques aux nodes Telegram Intro et PC Audio Intro du Workflow 1
- Chat ID dynamique depuis le node d'extraction

- [ ] **Étape 10 : Tester**

1. Lancer Spotify sur un morceau
2. Envoyer "analyse" au bot Telegram
3. Vérifier : message reçu sur Telegram + voix sur PC

- [ ] **Étape 11 : Commit**

```powershell
git add n8n-workflows/04-manual-analyze.json
git commit -m "feat: workflow manual-analyze - analyse a la demande via Telegram"
```

---

## Task 12 : Test d'intégration end-to-end

- [ ] **Étape 1 : Vérifier que le serveur PC tourne**

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/health"
```
Résultat attendu : `status: running`

- [ ] **Étape 2 : Vérifier que les 4 workflows sont actifs**

Dans n8n → chaque workflow doit afficher le toggle **Actif** en vert.

- [ ] **Étape 3 : Test scénario complet**

1. Lancer Spotify → jouer **Power – Kanye West**
2. Attendre 5-10s → vérifier Telegram : message intro reçu + voix sur PC
3. Passer au morceau suivant → vérifier : outro pour Power + intro pour le nouveau titre
4. Envoyer "analyse" au bot → vérifier : analyse immédiate
5. Envoyer `/mood` → appuyer sur `Détente 🌿` → vérifier : playlist créée sur Spotify + confirmation Telegram
6. Attendre 18h (ou tester manuellement) → vérifier le résumé quotidien

- [ ] **Étape 4 : Commit final**

```powershell
git add .
git commit -m "feat: spotify music companion - integration complete"
```
