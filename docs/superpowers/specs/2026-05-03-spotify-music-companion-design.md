# Spotify Music Companion — Design Spec
**Date :** 2026-05-03
**Projet :** Agent n8n d'analyse musicale en temps réel

---

## Contexte & Motivation

L'idée est née d'une écoute matinale de Kanye West (MBDTF) : aimer un son sans en comprendre le message crée une frustration. L'agent résout ça en donnant du sens à chaque morceau écouté — quelle que soit la langue — en temps réel, via Telegram et une voix sur PC.

---

## Objectif

Construire un agent n8n qui :
1. Analyse chaque morceau Spotify à la volée (début + fin)
2. Livre l'analyse en français sur Telegram et en audio sur PC
3. Crée des playlists personnalisées selon l'humeur et le moment
4. Produit un résumé quotidien des thèmes écoutés

---

## Architecture — 4 Workflows n8n

### Workflow 1 : `spotify-watcher`
**Déclencheur :** Schedule toutes les 5 secondes

**Flow :**
1. Appel Spotify API `currently-playing`
2. Comparaison avec le titre stocké en Static Data n8n
3. Si nouveau titre détecté → déclenche l'analyse de début du nouveau titre
4. Simultanément → déclenche l'analyse de fin pour le titre précédent (la détection d'un nouveau titre = confirmation que l'ancien est terminé)

**Analyse début (Claude) :**
- De quoi parle le morceau (2-3 phrases, en français)
- Message profond / intention artistique (1-2 phrases)

**Analyse fin (Claude) :**
- Ce qu'il faut retenir (1 phrase impactante)

**Sorties :**
- Telegram : message formaté (voir format ci-dessous)
- Webhook local PC : texte envoyé au serveur Python → pause Spotify → TTS → reprise

---

### Workflow 2 : `playlist-generator`
**Déclencheur :** Message Telegram (bot)

**Entrées acceptées :**
- Boutons inline Telegram prédéfinis : `Concentration 🧠`, `Soirée 🌙`, `Sport ⚡`, `Détente 🌿`, `Sad mood 🌧️`
- Texte libre en langage naturel : *"je suis fatigué mais je dois bosser"*

**Flow :**
1. Réception du message Telegram
2. Claude analyse l'état + heure du jour → sélectionne 5-10 titres adaptés basés sur les 50 derniers titres écoutés (limite API Spotify) + genres favoris
3. Création de la playlist sur Spotify via API
4. Lancement immédiat sur le device actif
5. Confirmation Telegram avec nom de playlist + aperçu des titres

---

### Workflow 3 : `daily-summary`
**Déclencheur :** Schedule chaque jour à 18h00

**Flow :**
1. Récupération de l'historique d'écoute Spotify du jour (recently played)
2. Claude synthétise : thèmes récurrents, artistes dominants, évolution émotionnelle
3. Suggestion de 2-3 nouveaux artistes à explorer
4. Envoi Telegram du résumé

---

### Workflow 4 : `manual-analyze`
**Déclencheur :** Message Telegram contenant le mot "analyse"

**Flow :**
1. Appel Spotify `currently-playing`
2. Même pipeline que Workflow 1 (analyse Claude)
3. Envoi Telegram + audio PC TTS

---

## Composant PC : Serveur Local Python

**Technologie :** Flask (~30 lignes)
**Port :** localhost:5001 (5678 est réservé à n8n)

**Endpoints :**
- `POST /speak` — reçoit `{ "text": "...", "type": "intro"|"outro" }` → pause Spotify → TTS → reprise Spotify
  
**TTS :** `gTTS` (Google Text-to-Speech, voix française naturelle) + `playsound` pour la lecture

**Contrôle Spotify :** via `spotipy` (bibliothèque Python officielle Spotify)

**Comportement :**
1. Mise en pause via Spotify API
2. Génération audio TTS du texte reçu
3. Lecture du fichier audio
4. Reprise Spotify

---

## Format des Messages Telegram

### Début de morceau
```
🎵 {titre} — {artiste}
📀 {album}

📖 De quoi ça parle :
{analyse 2-3 phrases}

💭 Message profond :
{message 1-2 phrases}
```

### Fin de morceau
```
✅ À retenir :
{phrase impactante}
```

### Confirmation playlist
```
🎧 Playlist créée : "{nom généré par Claude}"
{N} titres sélectionnés pour toi :
• {titre 1} – {artiste 1}
• {titre 2} – {artiste 2}
• ...
▶️ Lancée sur Spotify !
```

### Résumé quotidien (18h)
```
📊 Ton journal musical du {date}

🎵 {N} titres écoutés
🎨 Artistes dominants : {liste}

💭 Thèmes du jour :
{synthèse Claude 3-4 phrases}

🔭 À découvrir :
• {artiste suggéré 1}
• {artiste suggéré 2}
```

---

## Stack Technique — 100% Gratuit

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Orchestration | n8n self-hosted (Docker ou npm) | Gratuit |
| Musique | Spotify Web API + spotipy | Gratuit |
| Intelligence | Groq API (Llama 3.3 70B) | Gratuit |
| Notifications | Telegram Bot API | Gratuit |
| Audio PC | Python Flask + gTTS + playsound | Gratuit |
| Stockage état | n8n Static Data (titre courant) | Gratuit |

---

## Prérequis

- Compte Spotify Developer (Client ID + Secret) — gratuit sur developer.spotify.com
- Bot Telegram (token via @BotFather) — gratuit
- Clé API Groq — gratuite sur console.groq.com
- Python 3.10+ sur le PC
- n8n self-hosted : `npm install -g n8n` ou Docker

---

## Gestion d'erreurs

- **Spotify non actif** (rien en lecture) : le watcher ignore silencieusement, pas de spam
- **Échec Claude** : Telegram envoie uniquement les métadonnées du titre (artiste, album) sans analyse
- **Serveur PC hors ligne** : n8n log l'erreur, continue d'envoyer sur Telegram normalement
- **Limite API Spotify** : le polling 5s reste bien en dessous des limites (180 req/min autorisées)

---

## Ce que ce projet couvre comme nodes n8n

- `Schedule Trigger` — polling et automations horaires
- `HTTP Request` — appels Spotify API
- `Code` — logique de détection de changement de titre
- `AI Agent / Groq (Llama 3.3 70B)` — analyse textuelle
- `Telegram` — envoi de messages et réception de commandes
- `Webhook` — communication avec le serveur PC local
- `Static Data` — persistance légère entre les exécutions
- `IF / Switch` — routage conditionnel
