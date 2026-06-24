# ============================================================
#  PROCFILE — Commande de démarrage pour Render
# ============================================================
#
#  Render lit ce fichier pour savoir comment lancer l'app.
#  Une seule ligne suffit.
#
#  gunicorn = serveur de production (plus robuste que flask run)
#  app_v3:app = "dans le fichier app_v3.py, lance l'objet 'app'"
#  --workers 2 = 2 processus parallèles (gère plusieurs visiteurs)
#  --bind 0.0.0.0:$PORT = écouter sur le port fourni par Render
#
# ============================================================

web: gunicorn app_v3:app --workers 2 --bind 0.0.0.0:$PORT
