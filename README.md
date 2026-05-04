# Tchoutzify Agent — TuneZine AI

> Un agent musical intelligent qui analyse chaque morceau que tu écoutes sur Spotify, te raconte son histoire en français, et génère des playlists adaptées à ton humeur — 100% gratuit.

---

## L'origine du projet

Un matin, j'écoutais **Power de Kanye West** — extrait de *My Beautiful Dark Twisted Fantasy*. J'aimais profondément le flow, l'énergie, la construction du son. Mais les paroles m'échappaient. Je ne comprenais pas ce que Kanye voulait dire, ce qu'il vivait, ce qu'il transmettait.

J'aime donner du sens à ce que je fais. Écouter de la musique sans en comprendre le message, c'est comme lire un livre en ne regardant que les illustrations. La beauté est là, mais la profondeur manque.

De cette frustration est né **TuneZine AI** : un agent qui transforme chaque écoute en apprentissage. Chaque morceau devient une histoire. Chaque changement de son devient une leçon de culture, d'émotion, et d'humanité.

---

## Ce que fait TuneZine AI

| Fonctionnalité | Description |
|----------------|-------------|
| **Analyse en temps réel** | Détecte chaque nouveau morceau (toutes les 5s) et génère une narration |
| **Narration vocale** | Henri (voix masculine Microsoft Edge TTS) lit l'analyse à voix haute |
| **Notification Telegram** | L'analyse complète arrive sur ton bot Telegram |
| **Playlist par humeur** | Envoie "soirée", "concentration", "sport"... → playlist lancée sur Spotify |
| **Résumé quotidien** | Chaque soir à 18h, résumé des thèmes musicaux de ta journée |
| **Analyse à la demande** | Envoie "analyse" au bot → narration immédiate du morceau en cours |

### Exemple de narration

> *"Tu écoutes Power de Kanye West. Nous sommes en 2010, et Kanye West sort l'un des albums les plus ambitieux du hip-hop moderne. Dans ce morceau, il se met en scène comme un dieu déchu, conscient de sa grandeur mais aussi de ses contradictions. Les samples de King Crimson et de Pete Rock créent une atmosphère épique et mélancolique à la fois. Kanye parle de la corruption inhérente au pouvoir — qu'il soit politique, artistique ou culturel. Il sait qu'il détient une influence immense, et cette prise de conscience le dévore. Le message profond : plus tu montes, plus tu dois rester humble — la chute est proportionnelle à l'orgueil."*

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  n8n (4 workflows)                   │
│                                                      │
│  spotify-watcher    → détection 5s + narration       │
│  playlist-generator → bot Telegram + Spotify         │
│  daily-summary      → résumé à 18h                  │
│  manual-analyze     → commande "analyse"             │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼─────────────┐
          │   Serveur Python local    │
          │   Flask · port 5001       │
          │                          │
          │  /currently-playing       │
          │  /speak → pause/TTS/play  │
          │  /create-playlist         │
          │  /recently-played         │
          └──────────────────────────┘
```

**Flux complet :**
1. Spotify détecte un nouveau morceau → n8n le capte en 5s
2. Gemini génère une narration culturelle et musicale
3. Henri (Edge TTS) pause la musique, lit la narration, reprend
4. Le message complet arrive sur Telegram

---

## Stack technique — 100% gratuit

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Orchestration | n8n self-hosted | Gratuit |
| Analyse musicale | Google Gemini 2.5 Flash | Gratuit |
| Voix | Microsoft Edge TTS `fr-FR-HenriNeural` | Gratuit |
| Notifications | Telegram Bot API | Gratuit |
| Musique | Spotify Web API + spotipy | Gratuit* |
| Serveur local | Python Flask | Gratuit |

*\*Spotify Premium requis pour le contrôle de lecture (3,29$/mois)*

---

## Installation

### Prérequis

- Python 3.10+
- Node.js (pour n8n)
- Compte Spotify Premium + [app Developer](https://developer.spotify.com/dashboard)
- Bot Telegram via [@BotFather](https://t.me/BotFather)
- Clé API Gemini gratuite sur [aistudio.google.com](https://aistudio.google.com)

### 1. Cloner le projet

```bash
git clone https://github.com/zoom-BT/Tchoutzify-Agent.git
cd Tchoutzify-Agent
```

### 2. Serveur Python

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

Authentifie Spotify (première fois uniquement) :
```bash
python auth_spotify.py
```

Lance le serveur :
```bash
python server.py
```

### 3. n8n

```bash
npm install -g n8n
npx n8n start
```

Ouvre [localhost:5678](http://localhost:5678) et configure les credentials :
- **Header Auth** → `Authorization: Bearer ta_cle_gemini`
- **Telegram API** → ton token bot

### 4. Lancement quotidien

```bash
# Terminal 1 — Serveur Python
python pc-server/server.py

# Terminal 2 — n8n
npx n8n start
```

Lance Spotify et écoute de la musique — TuneZine fait le reste.

---

## Commandes Telegram

| Commande | Action |
|----------|--------|
| `analyse` | Analyse immédiate du morceau en cours |
| `concentration` | Playlist focus deep work |
| `soiree` | Playlist ambiance soirée |
| `sport` | Playlist énergie et motivation |
| `detente` | Playlist relaxation |
| `sad` | Playlist introspection |
| Texte libre | *"je suis fatigué mais je dois bosser"* → playlist sur mesure |

---

## Tests

```bash
cd pc-server
pytest tests/ -v
# 11 tests — spotify_control, tts_engine, server
```

---

## Conception & Design

Le processus de conception est documenté dans `docs/superpowers/specs/` :
- **Spec** : `2026-05-03-spotify-music-companion-design.md` — architecture, flux de données, décisions techniques

Ce projet a été conçu avec une approche **spec-first** : le design complet a été validé avant d'écrire la moindre ligne de code.

---

## Ce que j'ai appris en buildant ça

- **n8n** : orchestration de workflows sans code, puissant pour les agents IA
- **Spotify API** : les contraintes du mode développement (quota, scopes OAuth)
- **Edge TTS** : la qualité de la voix change tout à l'expérience
- **Gemini** : des narrations riches et contextuelles en quelques tokens
- **Architecture agent** : séparer le serveur local (Python) de l'orchestration (n8n)

---

## Inspiré par

> *"La musique est une langue universelle, mais comprendre ce qu'elle dit vraiment demande un guide."*

TuneZine AI est ce guide.
