# ============================================================
#  APP_PRODUCTION.PY — Version prête pour Render
# ============================================================
#
#  Deux différences avec app_v3.py :
#  1. La clé JWT vient des variables d'environnement (sécurisé)
#  2. SQLite est remplacé par un fichier en /tmp/ sur Render
#     (Render ne permet pas d'écrire ailleurs)
#
#  Note importante sur SQLite en production :
#  SQLite convient parfaitement pour un MVP avec < 1000 utilisateurs.
#  Pour scaler davantage, on migrera vers PostgreSQL (Phase 8).
#
# ============================================================

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv   # lit le fichier .env
import os, uuid
from datetime import datetime

# Charger les variables d'environnement AVANT tout le reste
load_dotenv()

# Importer nos modules — ils liront JWT_SECRET_KEY depuis l'environnement
from analyser_pl_v2 import analyser_fichier
from base_donnees   import (
    initialiser_base, sauvegarder_dossier,
    lire_tous_les_dossiers, lire_dossier_par_id,
    mettre_a_jour_dossier, supprimer_dossier,
    statistiques_marche,
)
from auth import (
    initialiser_table_utilisateurs,
    inscrire_utilisateur, connecter_utilisateur,
    verifier_token,
)

# --- Configuration -------------------------------------------
app = Flask(__name__, static_folder='static')

# Sur Render, on écrit dans /tmp (seul dossier accessible en écriture)
# En local, on reste dans le dossier courant
EST_EN_PRODUCTION = os.environ.get('RENDER', False)
UPLOAD_FOLDER = '/tmp/uploads' if EST_EN_PRODUCTION else 'uploads'
EXTENSIONS_OK = {'xlsx', 'xls', 'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialisation des tables
initialiser_base()
initialiser_table_utilisateurs()


# --- Utilitaire ----------------------------------------------
def extension_autorisee(nom):
    return '.' in nom and nom.rsplit('.', 1)[1].lower() in EXTENSIONS_OK


# ════════════════════════════════════════════════════════════
#  ROUTES — identiques à app_v3.py
#  (on ne recopie que les différences clés ici)
# ════════════════════════════════════════════════════════════

@app.route('/')
def accueil():
    return send_from_directory('static', 'login.html')

@app.route('/static/<path:nom_fichier>')
def fichier_statique(nom_fichier):
    return send_from_directory('static', nom_fichier)

@app.route('/api/ping')
def ping():
    return jsonify({
        'status':      'ok',
        'version':     '3.0-prod',
        'environnement': 'Render' if EST_EN_PRODUCTION else 'local',
        'heure':       datetime.now().strftime('%H:%M:%S')
    }), 200

# Auth
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'erreur': 'Données manquantes'}), 400
    resultat = inscrire_utilisateur(
        data.get('email', ''), data.get('mot_de_passe', ''),
        data.get('prenom', ''), data.get('nom', ''),
        data.get('role', 'acheteur'),
        entreprise=data.get('entreprise', ''),
        budget_max=data.get('budget_max', 0),
        score_min=data.get('score_min', 50),
        secteurs_cibles=data.get('secteurs_cibles', []),
    )
    return jsonify(resultat), 201 if 'succes' in resultat else 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'erreur': 'Données manquantes'}), 400
    resultat = connecter_utilisateur(data.get('email', ''), data.get('mot_de_passe', ''))
    return jsonify(resultat), 200 if 'succes' in resultat else 401

@app.route('/api/auth/moi', methods=['GET'])
@verifier_token
def moi():
    return jsonify({'utilisateur': request.utilisateur}), 200

# P&L + Dossiers (identiques à app_v3.py)
@app.route('/api/analyser', methods=['POST'])
@verifier_token
def analyser():
    if 'fichier' not in request.files:
        return jsonify({'erreur': 'Aucun fichier reçu'}), 400
    fichier = request.files['fichier']
    if not fichier.filename or not extension_autorisee(fichier.filename):
        return jsonify({'erreur': 'Format non accepté'}), 400
    identifiant    = str(uuid.uuid4())
    extension      = fichier.filename.rsplit('.', 1)[1].lower()
    chemin_fichier = os.path.join(UPLOAD_FOLDER, f"{identifiant}.{extension}")
    fichier.save(chemin_fichier)
    try:
        resultats = analyser_fichier(chemin_fichier)
    except Exception as e:
        return jsonify({'erreur': str(e)}), 500
    resultats.update({
        'id': identifiant, 'nom_fichier': fichier.filename,
        'date_analyse': datetime.now().strftime('%d/%m/%Y à %H:%M'),
        'vendeur_id':   request.utilisateur['id'],
        'statut':       request.form.get('statut', 'vente'),
        'secteur':      request.form.get('secteur', ''),
        'region':       request.form.get('region', ''),
        'description':  request.form.get('description', ''),
    })
    sauvegarder_dossier(resultats)
    return jsonify(resultats), 200

@app.route('/api/dossiers', methods=['GET'])
@verifier_token
def liste_dossiers():
    dossiers = lire_tous_les_dossiers(
        score_min=int(request.args.get('score_min', 0)),
        profil=request.args.get('profil'),
        statut=request.args.get('statut'),
        tri=request.args.get('tri', 'score_total'),
    )
    if request.utilisateur.get('role') == 'vendeur':
        dossiers = [d for d in dossiers if d.get('vendeur_id') == request.utilisateur['id']]
    return jsonify({'total': len(dossiers), 'dossiers': dossiers}), 200

@app.route('/api/dossiers/<identifiant>', methods=['GET'])
@verifier_token
def detail_dossier(identifiant):
    dossier = lire_dossier_par_id(identifiant)
    return jsonify(dossier) if dossier else (jsonify({'erreur': 'Introuvable'}), 404)

@app.route('/api/stats', methods=['GET'])
def stats():
    data = statistiques_marche()
    data['derniere_maj'] = datetime.now().strftime('%d/%m/%Y à %H:%M')
    return jsonify(data), 200


# --- Démarrage -----------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = not EST_EN_PRODUCTION     # debug=False en production
    print(f"Serveur démarré · port {port} · prod={EST_EN_PRODUCTION}")
    app.run(host='0.0.0.0', port=port, debug=debug)
