# ============================================================
#  BASE_DONNEES.PY — Gestion SQLite · Plateforme M&A IA
# ============================================================
#
#  Ce fichier fait une seule chose : parler à la base de données.
#  Flask l'appelle pour sauvegarder ou récupérer des dossiers.
#
#  Architecture :
#  app.py  →  base_donnees.py  →  ma_plateforme.db (fichier SQLite)
#
# ============================================================

import sqlite3      # inclus dans Python — aucune installation nécessaire
import json         # pour convertir les listes/dicts en texte stockable
from datetime import datetime


# --- BLOC 1 : CONFIGURATION ----------------------------------

NOM_BASE = 'ma_plateforme.db'   # le fichier qui contiendra toutes nos données

# Structure de notre table "dossiers" — comme définir les colonnes d'un Excel
# Chaque ligne = un champ avec son type de données
SCHEMA_TABLE = """
CREATE TABLE IF NOT EXISTS dossiers (

    -- Identité du dossier
    id              TEXT PRIMARY KEY,   -- identifiant unique (uuid)
    nom_fichier     TEXT NOT NULL,      -- nom du fichier uploadé
    date_analyse    TEXT NOT NULL,      -- date et heure de l'analyse

    -- Indicateurs financiers
    ca              REAL,               -- chiffre d'affaires (€)
    ebitda          REAL,               -- EBITDA (€)
    resultat_net    REAL,               -- résultat net (€)
    marge_ebitda    REAL,               -- marge EBITDA (%)
    marge_nette     REAL,               -- marge nette (%)
    croissance_ca   REAL,               -- croissance CA sur la période (%)

    -- Score et valorisation
    score_total     INTEGER,            -- score /100
    profil          TEXT,               -- Premium / Standard / Décote
    valeur_basse    REAL,               -- valorisation basse (€)
    valeur_haute    REAL,               -- valorisation haute (€)
    valeur_centre   REAL,               -- valorisation centrale (€)

    -- Données complexes stockées en JSON (listes, dictionnaires)
    -- SQLite ne supporte pas les tableaux → on les convertit en texte
    annees          TEXT,               -- ex: "[2022, 2023, 2024]"
    details_score   TEXT,               -- liste des 4 critères en JSON
    historique_ca   TEXT,               -- évolution du CA en JSON
    historique_ebitda TEXT,             -- évolution EBITDA en JSON

    -- Statut sur la marketplace
    statut          TEXT DEFAULT 'vente',    -- vente / opportunite
    secteur         TEXT DEFAULT '',         -- secteur d'activité
    region          TEXT DEFAULT '',         -- région géographique
    description     TEXT DEFAULT ''          -- description libre
)
"""


# --- BLOC 2 : CONNEXION À LA BASE ----------------------------
#
# sqlite3.connect() ouvre le fichier .db (le crée s'il n'existe pas)
# C'est comme ouvrir un classeur Excel — s'il n'existe pas, on en crée un neuf.
#
# Le "context manager" (with ... as conn:) garantit que la connexion
# se ferme proprement même si une erreur survient.
# C'est l'équivalent de try/finally automatique.

def get_connexion():
    """Ouvre et retourne une connexion à la base de données."""
    conn = sqlite3.connect(NOM_BASE)
    # row_factory permet de lire les résultats comme des dictionnaires
    # Ex: row['score_total'] au lieu de row[7]
    conn.row_factory = sqlite3.Row
    return conn


# --- BLOC 3 : INITIALISATION ---------------------------------

def initialiser_base():
    """
    Crée la table 'dossiers' si elle n'existe pas encore.
    À appeler une seule fois au démarrage du serveur Flask.
    'CREATE TABLE IF NOT EXISTS' = crée seulement si absente (idempotent).
    """
    with get_connexion() as conn:
        conn.execute(SCHEMA_TABLE)
        conn.commit()   # commit = "valider les changements" (comme Ctrl+S)
    print(f"✅ Base de données prête : {NOM_BASE}")


# --- BLOC 4 : SAUVEGARDER UN DOSSIER -------------------------

def sauvegarder_dossier(resultats):
    """
    Insère un nouveau dossier analysé dans la base.

    resultats = le dictionnaire retourné par analyser_fichier()
    Retourne  = l'identifiant du dossier créé

    INSERT OR REPLACE = si l'id existe déjà, on le remplace
    (utile si on ré-analyse le même fichier)
    """

    # Les listes et dictionnaires Python ne peuvent pas être stockés
    # directement en SQLite → on les convertit en chaîne JSON
    # json.dumps()  = Python → texte JSON  (pour stocker)
    # json.loads()  = texte JSON → Python  (pour récupérer)

    sql = """
    INSERT OR REPLACE INTO dossiers (
        id, nom_fichier, date_analyse,
        ca, ebitda, resultat_net, marge_ebitda, marge_nette, croissance_ca,
        score_total, profil, valeur_basse, valeur_haute, valeur_centre,
        annees, details_score, historique_ca, historique_ebitda,
        statut, secteur, region, description
    ) VALUES (
        :id, :nom_fichier, :date_analyse,
        :ca, :ebitda, :resultat_net, :marge_ebitda, :marge_nette, :croissance_ca,
        :score_total, :profil, :valeur_basse, :valeur_haute, :valeur_centre,
        :annees, :details_score, :historique_ca, :historique_ebitda,
        :statut, :secteur, :region, :description
    )
    """
    # Les :nom sont des "paramètres nommés" — SQLite les remplace
    # par les valeurs du dictionnaire. C'est plus sûr que de concaténer
    # des chaînes (protection contre les injections SQL).

    params = {
        'id':              resultats['id'],
        'nom_fichier':     resultats['nom_fichier'],
        'date_analyse':    resultats.get('date_analyse', datetime.now().strftime('%d/%m/%Y à %H:%M')),
        'ca':              resultats.get('ca', 0),
        'ebitda':          resultats.get('ebitda', 0),
        'resultat_net':    resultats.get('resultat_net', 0),
        'marge_ebitda':    resultats.get('marge_ebitda', 0),
        'marge_nette':     resultats.get('marge_nette', 0),
        'croissance_ca':   resultats.get('croissance_ca', 0),
        'score_total':     resultats.get('score_total', 0),
        'profil':          resultats.get('profil', ''),
        'valeur_basse':    resultats.get('valeur_basse', 0),
        'valeur_haute':    resultats.get('valeur_haute', 0),
        'valeur_centre':   resultats.get('valeur_centre', 0),
        # Conversion listes/dicts → JSON texte
        'annees':          json.dumps(resultats.get('annees', [])),
        'details_score':   json.dumps(resultats.get('details_score', [])),
        'historique_ca':   json.dumps(resultats.get('historique_ca', {})),
        'historique_ebitda': json.dumps(resultats.get('historique_ebitda', {})),
        'statut':          resultats.get('statut', 'vente'),
        'secteur':         resultats.get('secteur', ''),
        'region':          resultats.get('region', ''),
        'description':     resultats.get('description', ''),
    }

    with get_connexion() as conn:
        conn.execute(sql, params)
        conn.commit()

    return resultats['id']


# --- BLOC 5 : LIRE LES DOSSIERS ------------------------------

def lire_tous_les_dossiers(
    score_min=0,
    profil=None,
    statut=None,
    secteur=None,
    tri='score_total'
):
    """
    Récupère les dossiers avec filtres optionnels.
    C'est l'équivalent SQL du .filter() pandas de la Phase 1.

    score_min = score minimum (0 par défaut = tous)
    profil    = 'Premium', 'Standard', 'Décote' ou None (tous)
    statut    = 'vente', 'opportunite' ou None (tous)
    tri       = colonne de tri ('score_total', 'ca', 'valeur_centre')
    """

    # On construit la requête SQL dynamiquement selon les filtres
    # Les conditions WHERE s'ajoutent au fur et à mesure
    conditions = ['score_total >= :score_min']
    params     = {'score_min': score_min}

    if profil:
        conditions.append('profil = :profil')
        params['profil'] = profil

    if statut:
        conditions.append('statut = :statut')
        params['statut'] = statut

    if secteur:
        conditions.append('secteur = :secteur')
        params['secteur'] = secteur

    # Sécurité : s'assurer que la colonne de tri est valide
    # (évite les injections SQL via le paramètre tri)
    tris_autorises = {'score_total', 'ca', 'ebitda', 'valeur_centre', 'date_analyse'}
    if tri not in tris_autorises:
        tri = 'score_total'

    sql = f"""
    SELECT * FROM dossiers
    WHERE {' AND '.join(conditions)}
    ORDER BY {tri} DESC
    """

    with get_connexion() as conn:
        rows = conn.execute(sql, params).fetchall()

    # Convertir chaque ligne en dictionnaire Python exploitable
    return [deserialiser(dict(row)) for row in rows]


def lire_dossier_par_id(identifiant):
    """
    Récupère un seul dossier par son identifiant unique.
    Retourne None si introuvable.
    """
    sql = "SELECT * FROM dossiers WHERE id = ?"
    # Le ? est un paramètre positionnel (alternative aux :nom)
    with get_connexion() as conn:
        row = conn.execute(sql, (identifiant,)).fetchone()

    return deserialiser(dict(row)) if row else None


# --- BLOC 6 : METTRE À JOUR UN DOSSIER -----------------------

def mettre_a_jour_dossier(identifiant, champs):
    """
    Met à jour des champs spécifiques d'un dossier.
    Utile pour modifier le statut, secteur, région ou description.

    champs = dictionnaire des champs à modifier
    Ex: {'statut': 'opportunite', 'region': 'Bretagne'}
    """
    # Construire SET dynamiquement selon les champs fournis
    champs_autorises = {'statut', 'secteur', 'region', 'description'}
    champs_valides   = {k: v for k, v in champs.items() if k in champs_autorises}

    if not champs_valides:
        return False

    set_clause = ', '.join(f"{k} = :{k}" for k in champs_valides)
    champs_valides['id'] = identifiant

    sql = f"UPDATE dossiers SET {set_clause} WHERE id = :id"

    with get_connexion() as conn:
        conn.execute(sql, champs_valides)
        conn.commit()

    return True


# --- BLOC 7 : SUPPRIMER UN DOSSIER ---------------------------

def supprimer_dossier(identifiant):
    """Supprime un dossier de la base. Retourne True si supprimé."""
    sql = "DELETE FROM dossiers WHERE id = ?"
    with get_connexion() as conn:
        curseur = conn.execute(sql, (identifiant,))
        conn.commit()
    # rowcount = nombre de lignes affectées (0 si dossier introuvable)
    return curseur.rowcount > 0


# --- BLOC 8 : STATISTIQUES -----------------------------------

def statistiques_marche():
    """
    Calcule les indicateurs synthétiques pour le Terminal.
    Une seule requête SQL fait tout le calcul côté base — très rapide.
    AVG = moyenne, COUNT = compter, SUM = somme (SQL standard)
    """
    sql = """
    SELECT
        COUNT(*)                            AS nb_dossiers,
        ROUND(AVG(score_total), 1)          AS score_moyen,
        COUNT(CASE WHEN profil = 'Premium'  THEN 1 END) AS nb_premium,
        ROUND(SUM(valeur_centre), 0)        AS valo_totale,
        ROUND(AVG(marge_ebitda), 1)         AS marge_ebitda_moyenne,
        ROUND(AVG(croissance_ca), 1)        AS croissance_moyenne
    FROM dossiers
    """
    with get_connexion() as conn:
        row = conn.execute(sql).fetchone()

    return dict(row) if row else {}


# --- BLOC 9 : DÉSÉRIALISATION --------------------------------

def deserialiser(row):
    """
    Convertit une ligne de base de données en dictionnaire Python propre.
    Reconvertit les champs JSON (texte → listes/dicts Python).
    C'est l'inverse de ce qu'on a fait dans sauvegarder_dossier().
    """
    for champ in ['annees', 'details_score', 'historique_ca', 'historique_ebitda']:
        if champ in row and isinstance(row[champ], str):
            try:
                row[champ] = json.loads(row[champ])
            except (json.JSONDecodeError, TypeError):
                row[champ] = []
    return row


# --- TEST EN MODE AUTONOME -----------------------------------

if __name__ == '__main__':
    print("Test de la base de données...")
    initialiser_base()

    # Insérer un dossier de test
    dossier_test = {
        'id':           'test-001',
        'nom_fichier':  'test_pl.xlsx',
        'date_analyse': '01/06/2026 à 10:00',
        'ca':           1_550_000,
        'ebitda':       461_000,
        'resultat_net': 320_250,
        'marge_ebitda': 29.7,
        'marge_nette':  20.7,
        'croissance_ca': 29.2,
        'score_total':  100,
        'profil':       'Premium',
        'valeur_basse': 2_766_000,
        'valeur_haute': 3_688_000,
        'valeur_centre': 3_227_000,
        'annees':       [2022, 2023, 2024],
        'details_score': [],
        'historique_ca': {},
        'historique_ebitda': {},
        'statut':       'vente',
        'secteur':      'Distribution',
        'region':       'Île-de-France',
    }
    sauvegarder_dossier(dossier_test)
    print("✅ Dossier test sauvegardé")

    # Lire tous les dossiers
    tous = lire_tous_les_dossiers()
    print(f"✅ {len(tous)} dossier(s) en base")
    print(f"   → {tous[0]['nom_fichier']} | Score : {tous[0]['score_total']}/100")

    # Statistiques
    stats = statistiques_marche()
    print(f"✅ Score moyen du marché : {stats['score_moyen']}/100")
