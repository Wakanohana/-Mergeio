# ============================================================
#  AUTH.PY — Authentification · Plateforme M&A IA · Phase 6
# ============================================================
#
#  Ce fichier gère tout ce qui concerne les utilisateurs :
#  → Création de compte (inscription)
#  → Vérification de mot de passe (connexion)
#  → Génération et validation de tokens JWT
#
#  Pour installer les dépendances nécessaires :
#  pip install flask bcrypt pyjwt
#
# ============================================================

import sqlite3
import bcrypt        # pour hasher les mots de passe (sécurité)
import jwt           # JSON Web Token — le "badge" numérique
import uuid
from datetime import datetime, timedelta


# --- BLOC 1 : CONFIGURATION ----------------------------------

NOM_BASE   = 'ma_plateforme.db'

# Clé secrète pour signer les tokens JWT.
# En production : stocker dans une variable d'environnement, jamais dans le code.
# Ex: SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
SECRET_KEY = 'ma_cle_secrete_a_changer_en_production_absolument'

# Durée de validité d'un token : 24 heures
# Après, l'utilisateur devra se reconnecter.
DUREE_TOKEN = timedelta(hours=24)

# Les deux types d'utilisateurs de notre plateforme
ROLES_AUTORISES = {'acheteur', 'vendeur', 'admin'}


# --- BLOC 2 : SCHÉMA DE LA TABLE UTILISATEURS ---------------
#
#  On ajoute une nouvelle table à notre base SQLite existante.
#  Elle s'ajoute à côté de la table "dossiers" déjà créée.

SCHEMA_UTILISATEURS = """
CREATE TABLE IF NOT EXISTS utilisateurs (

    id              TEXT PRIMARY KEY,   -- identifiant unique (uuid)
    email           TEXT UNIQUE NOT NULL, -- email = identifiant de connexion
    mot_de_passe    TEXT NOT NULL,      -- JAMAIS en clair — toujours hashé

    -- Profil
    prenom          TEXT DEFAULT '',
    nom             TEXT DEFAULT '',
    entreprise      TEXT DEFAULT '',
    role            TEXT DEFAULT 'acheteur',  -- acheteur / vendeur / admin

    -- Préférences acheteur (pour les alertes)
    budget_max      REAL DEFAULT 0,           -- budget d'acquisition max (€)
    secteurs_cibles TEXT DEFAULT '[]',        -- secteurs recherchés (JSON)
    score_min       INTEGER DEFAULT 50,       -- score minimum recherché

    -- Métadonnées
    date_inscription TEXT NOT NULL,
    derniere_connexion TEXT DEFAULT '',
    actif           INTEGER DEFAULT 1   -- 1 = actif, 0 = suspendu
)
"""


# --- BLOC 3 : CONNEXION À LA BASE ----------------------------

def get_connexion():
    conn = sqlite3.connect(NOM_BASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialiser_table_utilisateurs():
    """Crée la table utilisateurs si elle n'existe pas."""
    with get_connexion() as conn:
        conn.execute(SCHEMA_UTILISATEURS)
        conn.commit()
    print("✅ Table utilisateurs prête")


# --- BLOC 4 : HASHAGE DU MOT DE PASSE -----------------------
#
#  RÈGLE D'OR : on ne stocke JAMAIS un mot de passe en clair.
#  bcrypt.hashpw() transforme "monMotDePasse123" en une chaîne
#  illisible comme "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
#
#  Même en cas de piratage de la base, les mots de passe
#  sont inexploitables. C'est une protection légale obligatoire (RGPD).
#
#  bcrypt est "lent intentionnellement" — il faut ~0.1 seconde pour
#  hasher. Imperceptible pour un humain, mais qui rend les attaques
#  par force brute (millions d'essais) impossibles.

def hasher_mot_de_passe(mot_de_passe_clair):
    """
    Transforme un mot de passe lisible en hash sécurisé.
    'monPassword' → '$2b$12$eImiTXuWVx...' (60 caractères)
    """
    # encode() convertit le texte Python en bytes (bcrypt travaille en bytes)
    # gensalt() génère un "sel" aléatoire — même mot de passe = hash différent
    sel  = bcrypt.gensalt(rounds=12)    # 12 = niveau de sécurité (standard)
    hash = bcrypt.hashpw(mot_de_passe_clair.encode('utf-8'), sel)
    return hash.decode('utf-8')         # reconvertir en texte pour SQLite


def verifier_mot_de_passe(mot_de_passe_clair, hash_stocke):
    """
    Vérifie si un mot de passe correspond au hash en base.
    Retourne True si correct, False sinon.
    On ne "décode" jamais le hash — bcrypt compare directement.
    """
    return bcrypt.checkpw(
        mot_de_passe_clair.encode('utf-8'),
        hash_stocke.encode('utf-8')
    )


# --- BLOC 5 : INSCRIPTION ------------------------------------

def inscrire_utilisateur(email, mot_de_passe, prenom, nom, role='acheteur', **extras):
    """
    Crée un nouveau compte utilisateur.
    Retourne {'succes': True, 'id': '...'} ou {'erreur': '...'}

    **extras = paramètres optionnels (entreprise, budget_max, etc.)
    """

    # Validation basique
    if not email or '@' not in email:
        return {'erreur': 'Email invalide'}

    if len(mot_de_passe) < 8:
        return {'erreur': 'Le mot de passe doit faire au moins 8 caractères'}

    if role not in ROLES_AUTORISES:
        return {'erreur': f'Rôle invalide. Choisissez parmi : {ROLES_AUTORISES}'}

    # Vérifier que l'email n'existe pas déjà
    with get_connexion() as conn:
        existant = conn.execute(
            'SELECT id FROM utilisateurs WHERE email = ?', (email,)
        ).fetchone()

    if existant:
        return {'erreur': 'Cet email est déjà utilisé'}

    # Hasher le mot de passe AVANT de stocker
    hash_mdp = hasher_mot_de_passe(mot_de_passe)

    # Créer l'utilisateur
    nouvel_id = str(uuid.uuid4())
    import json

    sql = """
    INSERT INTO utilisateurs (
        id, email, mot_de_passe, prenom, nom, entreprise,
        role, budget_max, secteurs_cibles, score_min, date_inscription
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        nouvel_id,
        email.lower().strip(),          # normaliser l'email
        hash_mdp,                       # hash, jamais le mot de passe clair
        prenom.strip(),
        nom.strip(),
        extras.get('entreprise', ''),
        role,
        extras.get('budget_max', 0),
        json.dumps(extras.get('secteurs_cibles', [])),
        extras.get('score_min', 50),
        datetime.now().strftime('%d/%m/%Y à %H:%M'),
    )

    with get_connexion() as conn:
        conn.execute(sql, params)
        conn.commit()

    return {'succes': True, 'id': nouvel_id, 'role': role}


# --- BLOC 6 : CONNEXION ET TOKEN JWT -------------------------
#
#  JWT = JSON Web Token.
#  C'est un "badge numérique" en 3 parties séparées par des points :
#
#  HEADER.PAYLOAD.SIGNATURE
#
#  HEADER   : algorithme utilisé (HS256)
#  PAYLOAD  : les données (id utilisateur, rôle, expiration)
#  SIGNATURE: preuve que le token n'a pas été falsifié
#
#  Le navigateur stocke ce token et l'envoie à chaque requête.
#  Flask vérifie la signature — si valide, il fait confiance au payload.
#  Pas besoin de consulter la base à chaque requête !

def connecter_utilisateur(email, mot_de_passe):
    """
    Vérifie les identifiants et retourne un token JWT si corrects.
    Retourne {'token': '...', 'utilisateur': {...}} ou {'erreur': '...'}
    """

    # Récupérer l'utilisateur par email
    with get_connexion() as conn:
        row = conn.execute(
            'SELECT * FROM utilisateurs WHERE email = ? AND actif = 1',
            (email.lower().strip(),)
        ).fetchone()

    if not row:
        # Message volontairement vague — ne pas dire si c'est l'email ou le MDP
        # (sécurité : éviter l'énumération des comptes)
        return {'erreur': 'Email ou mot de passe incorrect'}

    utilisateur = dict(row)

    # Vérifier le mot de passe
    if not verifier_mot_de_passe(mot_de_passe, utilisateur['mot_de_passe']):
        return {'erreur': 'Email ou mot de passe incorrect'}

    # Générer le token JWT
    # Le payload contient les infos qu'on mettra dans chaque requête
    payload = {
        'id':    utilisateur['id'],
        'email': utilisateur['email'],
        'role':  utilisateur['role'],
        # exp = date d'expiration (datetime → timestamp Unix automatiquement)
        'exp':   datetime.utcnow() + DUREE_TOKEN,
    }

    # jwt.encode() signe le payload avec notre clé secrète
    # Si quelqu'un modifie le token, la signature ne correspondra plus
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    # Mettre à jour la date de dernière connexion
    with get_connexion() as conn:
        conn.execute(
            'UPDATE utilisateurs SET derniere_connexion = ? WHERE id = ?',
            (datetime.now().strftime('%d/%m/%Y à %H:%M'), utilisateur['id'])
        )
        conn.commit()

    # Ne jamais renvoyer le mot de passe hashé au client
    del utilisateur['mot_de_passe']

    return {
        'succes':       True,
        'token':        token,
        'utilisateur': {
            'id':         utilisateur['id'],
            'email':      utilisateur['email'],
            'prenom':     utilisateur['prenom'],
            'nom':        utilisateur['nom'],
            'role':       utilisateur['role'],
            'entreprise': utilisateur['entreprise'],
        }
    }


# --- BLOC 7 : VÉRIFICATION DU TOKEN (décorateur Flask) -------
#
#  Un "décorateur" Flask protège une route.
#  On écrit @verifier_token au-dessus d'une route,
#  et Flask vérifie automatiquement le token avant d'appeler la fonction.
#
#  C'est comme un vigile à l'entrée d'une salle VIP :
#  il vérifie le badge avant de laisser passer.

from functools import wraps
from flask import request, jsonify

def verifier_token(f):
    """
    Décorateur qui protège une route Flask.
    Usage : @verifier_token au-dessus de @app.route()

    Le client doit envoyer le token dans le header :
    Authorization: Bearer eyJhbGci...
    """
    @wraps(f)
    def decorated(*args, **kwargs):

        # Lire le header Authorization
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({'erreur': 'Token manquant'}), 401

        token = auth_header.split(' ')[1]  # "Bearer TOKEN" → "TOKEN"

        try:
            # jwt.decode() vérifie la signature ET l'expiration
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # Passer les infos de l'utilisateur à la fonction protégée
            request.utilisateur = payload

        except jwt.ExpiredSignatureError:
            return jsonify({'erreur': 'Session expirée, reconnectez-vous'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'erreur': 'Token invalide'}), 401

        return f(*args, **kwargs)

    return decorated


def verifier_role(role_requis):
    """
    Décorateur qui vérifie en plus le rôle de l'utilisateur.
    Usage : @verifier_role('admin') ou @verifier_role('vendeur')
    """
    def decorateur(f):
        @wraps(f)
        @verifier_token
        def decorated(*args, **kwargs):
            if request.utilisateur.get('role') != role_requis:
                return jsonify({'erreur': f'Accès réservé aux {role_requis}s'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorateur


# --- TEST EN MODE AUTONOME -----------------------------------

if __name__ == '__main__':
    print("Test du module d'authentification...\n")
    initialiser_table_utilisateurs()

    # Test inscription
    r = inscrire_utilisateur(
        email='acheteur@test.com',
        mot_de_passe='MonMotDePasse123',
        prenom='Jean',
        nom='Dupont',
        role='acheteur',
        budget_max=500_000,
        secteurs_cibles=['tech', 'commerce'],
        score_min=70
    )
    print(f"Inscription : {r}")

    # Test connexion
    r2 = connecter_utilisateur('acheteur@test.com', 'MonMotDePasse123')
    print(f"Connexion   : succes={r2.get('succes')} | role={r2.get('utilisateur', {}).get('role')}")
    print(f"Token JWT   : {r2.get('token', '')[:40]}...")

    # Test mauvais mot de passe
    r3 = connecter_utilisateur('acheteur@test.com', 'mauvaismdp')
    print(f"Mauvais MDP : {r3.get('erreur')}")
