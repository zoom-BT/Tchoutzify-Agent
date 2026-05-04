# Tchoutzify Agent — TuneZine AI

> Un agent musical intelligent qui analyse chaque morceau que tu écoutes sur Spotify, te raconte son histoire en français, et génère des playlists adaptées à ton humeur — 100% gratuit.

---

## L'idée

Tout est parti d'une écoute matinale de Kanye West (*My Beautiful Dark Twisted Fantasy*). J'aimais le flow mais je ne comprenais pas les paroles. La limite était la langue. De là est né l'idée : un agent qui, à chaque nouveau morceau, me raconte son histoire — peu importe la langue.

---

## Ce que fait TuneZine AI

| Fonctionnalité | Description |
|----------------|-------------|
| **Analyse en temps réel** | Détecte chaque changement de morceau (toutes les 5s) et génère une narration |
| **Narration vocale** | Henri (voix masculine Microsoft Edge) lit l'analyse à voix haute sur le PC |
| **Notification Telegram** | L'analyse complète est envoyée sur ton bot Telegram |
| **Playlist par humeur** | Envoie "soirée", "concentration", "sport"... → playlist lancée sur Spotify |
| **Résumé quotidien** | Chaque soir à 18h, résumé des thèmes musicaux du jour |
| **Analyse à la demande** | Envoie "analyse" au bot → analyse immédiate du morceau en cours |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  n8n (4 workflows)           │
│                                             │
│  spotify-watcher    → détection 5s          │
│  playlist-generator → bot Telegram          │
│  daily-summary      → résumé 18h            │
│  manual-analyze     → commande "analyse"    │
└─────────────────┬───────────────────────────┘
                  │
     ┌────────────▼────────────┐
     │   Serveur Python local   │
     │   (Flask · port 5001)    │
     │                          │
     │  /currently-playing      │
     │  /speak (TTS + pause)    │
     │  /create-playlist        │
     │  /recently-played        │
     └──────────────────────────┘
```

**4 workflows n8n :**
- `spotify-watcher` — poll toutes les 5s, analyse Gemini, Telegram + voix PC
- `playlist-generator` — bot Telegram avec humeurs prédéfinies ou texte libre
- `daily-summary` — résumé à 18h via Gemini
- `manual-analyze` — analyse à la demande via message "analyse"

---

## Stack technique — 100% gratuit

| Composant | Technologie |
|-----------|-------------|
| Orchestration | n8n self-hosted |
| Analyse musicale | Google Gemini 2.5 Flash (gratuit) |
| Voix | Microsoft Edge TTS — `fr-FR-HenriNeural` |
| Notifications | Telegram Bot API |
| Musique | Spotify Web API + spotipy |
| Serveur local | Python Flask |

---

## Installation

### Prérequis

- Python 3.10+
- Node.js (pour n8n)
- Compte Spotify Premium + app Developer
- Bot Telegram (@BotFather)
- Clé API Google Gemini (gratuite sur [aistudio.google.com](https://aistudio.google.com))

### 1. Serveur Python

```bash
cd pc-server
pip install -r requirements.txt
```

Crée un fichier `.env` :
```env
SPOTIFY_CLIENT_ID=ton_client_id
SPOTIFY_CLIENT_SECRET=ton_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
TELEGRAM_BOT_TOKEN=ton_token_bot
TELEGRAM_CHAT_ID=ton_chat_id
GEMINI_API_KEY=ta_cle_gemini
```

Authentifie Spotify (première fois) :
```bash
python auth_spotify.py
```

Lance le serveur :
```bash
python server.py
```

### 2. n8n

```bash
npm install -g n8n
npx n8n start
```

Ouvre [localhost:5678](http://localhost:5678) et importe les 4 workflows depuis le dossier `n8n-workflows/`.

### 3. Credentials n8n

Dans n8n → Settings → Credentials :
- **Header Auth** (Gemini) : `Authorization` = `Bearer ta_cle_gemini`
- **Telegram API** : ton token bot

---

## Utilisation

Lance chaque session avec deux terminaux :

```bash
# Terminal 1
python pc-server/server.py

# Terminal 2
npx n8n start
```

Lance Spotify et écoute de la musique — TuneZine fait le reste.

**Commandes Telegram disponibles :**
- `analyse` → analyse immédiate du morceau en cours
- `concentration` / `soiree` / `sport` / `detente` / `sad` → playlist adaptée
- Texte libre → "je suis fatigué mais je dois bosser" → playlist générée

---

## Tests

```bash
cd pc-server
pytest tests/ -v
```

11 tests couvrant `spotify_control`, `tts_engine` et `server`.

---

## Inspiration

> *"J'écoutais Power de Kanye West un matin. J'aimais le flow mais je ne comprenais rien aux paroles. La limite était la langue."*

Ce projet est né de cette frustration — et de l'envie de donner du sens à chaque morceau écouté.
