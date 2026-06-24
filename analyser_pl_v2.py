# ============================================================
#  ANALYSER_PL.PY — Version 2 · Importable par Flask
# ============================================================
#
#  Différence avec la version Phase 1 :
#  → On a encapsulé toute la logique dans une fonction analyser_fichier()
#  → Flask peut maintenant appeler cette fonction comme un outil
#  → Le script peut toujours tourner seul (test en terminal)
#
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime


# --- FONCTION PRINCIPALE : analyser_fichier() ----------------
#
#  En Phase 1, le code s'exécutait ligne par ligne au lancement.
#  Maintenant, tout est dans une fonction que Flask appelle à la demande.
#
#  C'est la différence entre :
#  - Un cuisinier qui cuisine dès qu'il arrive (Phase 1)
#  - Un cuisinier qui attend la commande avant de cuisiner (Phase 5)

def analyser_fichier(chemin_fichier):
    """
    Lit un fichier P&L (Excel ou CSV) et retourne un dictionnaire
    complet avec scores, valorisation et indicateurs.

    chemin_fichier = le chemin vers le fichier sur le serveur
    Retourne       = un dictionnaire Python (converti en JSON par Flask)
    """

    # ── Étape 1 : Lecture du fichier ──────────────────────
    extension = chemin_fichier.rsplit('.', 1)[-1].lower()

    if extension == 'csv':
        df_brut = pd.read_csv(chemin_fichier, index_col=0)
    else:
        df_brut = pd.read_excel(
            chemin_fichier,
            sheet_name=0,      # premier onglet (quel que soit son nom)
            header=3,          # ligne 4 = en-têtes
            index_col=0
        )

    # Normaliser les colonnes en entiers (2022, 2023, 2024)
    df_brut.columns = [
        int(c) if str(c).strip().replace('.0','').isdigit() else c
        for c in df_brut.columns
    ]

    # Détecter les années automatiquement
    annees = sorted([
        c for c in df_brut.columns
        if isinstance(c, (int, float)) and 1990 < int(c) < 2100
    ])

    if len(annees) < 2:
        raise ValueError("Le fichier doit contenir au moins 2 années de données.")

    premiere_annee = annees[0]
    derniere_annee = annees[-1]

    # ── Étape 2 : Extraction des valeurs ──────────────────
    def extraire(nom_poste, annee):
        """Cherche une valeur dans le tableau, retourne 0 si absente."""
        try:
            valeur = df_brut.loc[nom_poste, annee]
            return float(valeur) if not pd.isna(valeur) else 0.0
        except KeyError:
            return 0.0

    # Chercher les postes clés par mot-clé (tolérant aux variantes)
    def trouver_poste(motcle):
        motcle_bas = motcle.lower()
        for idx in df_brut.index:
            if isinstance(idx, str) and motcle_bas in idx.lower():
                return idx
        return None

    nom_ca      = trouver_poste("chiffre d'affaires") or trouver_poste("chiffre d")
    nom_ebitda  = trouver_poste("ebitda")
    nom_net     = trouver_poste("résultat net") or trouver_poste("resultat net")

    ca      = {a: extraire(nom_ca,     a) if nom_ca     else 0 for a in annees}
    ebitda  = {a: extraire(nom_ebitda, a) if nom_ebitda else 0 for a in annees}
    res_net = {a: extraire(nom_net,    a) if nom_net    else 0 for a in annees}

    # ── Étape 3 : Calcul du score (identique Phase 1) ─────
    score_total   = 0
    details_score = []

    # Critère 1 : Croissance du CA
    croissance_ca = (
        (ca[derniere_annee] / ca[premiere_annee] - 1) * 100
        if ca[premiere_annee] > 0 else 0
    )
    if   croissance_ca > 20: pts_c = 25; niv_c = "Excellent"
    elif croissance_ca > 10: pts_c = 15; niv_c = "Bon"
    elif croissance_ca > 0:  pts_c = 8;  niv_c = "Stable"
    else:                    pts_c = 0;  niv_c = "En déclin"
    score_total += pts_c
    details_score.append({"critere": "Croissance CA", "valeur": round(croissance_ca, 1), "points": pts_c, "max": 25, "niveau": niv_c})

    # Critère 2 : Marge EBITDA
    marge_ebitda = (ebitda[derniere_annee] / ca[derniere_annee] * 100) if ca[derniere_annee] > 0 else 0
    if   marge_ebitda > 20: pts_e = 25; niv_e = "Excellent"
    elif marge_ebitda > 10: pts_e = 18; niv_e = "Bon"
    elif marge_ebitda > 5:  pts_e = 10; niv_e = "Acceptable"
    else:                   pts_e = 3;  niv_e = "Faible"
    score_total += pts_e
    details_score.append({"critere": "Marge EBITDA", "valeur": round(marge_ebitda, 1), "points": pts_e, "max": 25, "niveau": niv_e})

    # Critère 3 : Rentabilité nette
    marge_nette = (res_net[derniere_annee] / ca[derniere_annee] * 100) if ca[derniere_annee] > 0 else 0
    if   marge_nette > 10: pts_n = 25; niv_n = "Excellent"
    elif marge_nette > 5:  pts_n = 18; niv_n = "Bon"
    elif marge_nette > 0:  pts_n = 10; niv_n = "Acceptable"
    else:                  pts_n = 0;  niv_n = "Perte"
    score_total += pts_n
    details_score.append({"critere": "Rentabilité nette", "valeur": round(marge_nette, 1), "points": pts_n, "max": 25, "niveau": niv_n})

    # Critère 4 : Régularité
    annees_positives = sum(1 for a in annees if res_net[a] > 0)
    if   annees_positives == len(annees): pts_r = 25; niv_r = "Régulière"
    elif annees_positives >= len(annees) / 2: pts_r = 12; niv_r = "Irrégulière"
    else:                                     pts_r = 0;  niv_r = "Instable"
    score_total += pts_r
    details_score.append({"critere": "Régularité", "valeur": f"{annees_positives}/{len(annees)}", "points": pts_r, "max": 25, "niveau": niv_r})

    # ── Étape 4 : Valorisation ────────────────────────────
    if   score_total >= 75: multi_bas, multi_haut, profil = 6.0, 8.0, "Premium"
    elif score_total >= 50: multi_bas, multi_haut, profil = 4.0, 6.0, "Standard"
    else:                   multi_bas, multi_haut, profil = 2.5, 4.0, "Décote"

    valeur_basse  = ebitda[derniere_annee] * multi_bas
    valeur_haute  = ebitda[derniere_annee] * multi_haut
    valeur_centre = (valeur_basse + valeur_haute) / 2

    # ── Étape 5 : Construire le dictionnaire de résultats ─
    # C'est ce dictionnaire que Flask convertira en JSON
    # et renverra au navigateur.
    # Un dictionnaire Python → JSON, c'est automatique avec jsonify().

    return {
        # Identité
        "annees":           annees,
        "premiere_annee":   premiere_annee,
        "derniere_annee":   derniere_annee,

        # Indicateurs financiers (dernière année)
        "ca":               round(ca[derniere_annee], 0),
        "ebitda":           round(ebitda[derniere_annee], 0),
        "resultat_net":     round(res_net[derniere_annee], 0),
        "marge_ebitda":     round(marge_ebitda, 1),
        "marge_nette":      round(marge_nette, 1),
        "croissance_ca":    round(croissance_ca, 1),

        # Historique sur toutes les années
        "historique_ca":      {str(a): ca[a]      for a in annees},
        "historique_ebitda":  {str(a): ebitda[a]  for a in annees},
        "historique_net":     {str(a): res_net[a] for a in annees},

        # Score
        "score_total":      score_total,
        "details_score":    details_score,
        "profil":           profil,

        # Valorisation
        "valeur_basse":     round(valeur_basse, 0),
        "valeur_haute":     round(valeur_haute, 0),
        "valeur_centre":    round(valeur_centre, 0),
        "multiple_bas":     multi_bas,
        "multiple_haut":    multi_haut,
    }


# --- TEST EN MODE AUTONOME -----------------------------------
# Ce bloc s'exécute UNIQUEMENT si on lance directement :
#   python analyser_pl.py
# Il ne s'exécute PAS quand Flask importe le fichier.

if __name__ == '__main__':
    import sys
    fichier = sys.argv[1] if len(sys.argv) > 1 else 'pl_techdistrib.xlsx'
    print(f"\n Test autonome sur : {fichier}\n")
    resultats = analyser_fichier(fichier)
    print(f"  Score     : {resultats['score_total']} / 100")
    print(f"  Profil    : {resultats['profil']}")
    print(f"  CA        : {resultats['ca']:,.0f} €")
    print(f"  EBITDA    : {resultats['ebitda']:,.0f} €")
    print(f"  Valo basse: {resultats['valeur_basse']:,.0f} €")
    print(f"  Valo haute: {resultats['valeur_haute']:,.0f} €")
