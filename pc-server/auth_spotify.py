from spotify_control import SpotifyController

print("Connexion à Spotify...")
ctrl = SpotifyController()
track = ctrl.get_current_track()
print("Authentification réussie !")
print("Morceau en cours:", track)
