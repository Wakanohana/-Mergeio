// ============================================================
//  API_CONNECTOR.JS — Connecteur front ↔ back
//  Plateforme M&A IA · Phase 5
// ============================================================
//
//  Ce fichier est inclus dans chaque page HTML.
//  Il centralise TOUS les appels au serveur Flask.
//
//  Principe : au lieu que chaque page parle directement
//  au serveur, elle passe par ce "traducteur" unique.
//  Si l'URL de l'API change un jour, on ne modifie qu'ici.
//
// ============================================================


// --- BLOC 1 : CONFIGURATION ----------------------------------

const API = {
    BASE_URL: 'http://localhost:5000',   // adresse du serveur Flask

    // Les routes de l'API (= les "numéros de téléphone" du serveur)
    ROUTES: {
        analyser:  '/api/analyser',       // POST  — uploader un P&L
        dossiers:  '/api/dossiers',       // GET   — liste des dossiers
        dossier:   '/api/dossiers/',      // GET   — un dossier précis
        stats:     '/api/stats',          // GET   — statistiques du marché
        ping:      '/api/ping',           // GET   — test de connexion
    }
};


// --- BLOC 2 : FONCTION DE BASE — appelerAPI() ----------------
//
//  C'est la fonction centrale. Toutes les autres l'utilisent.
//
//  async/await = façon moderne de gérer les opérations qui prennent
//  du temps (comme attendre une réponse du serveur).
//  Sans async/await, le navigateur "bloquerait" pendant l'attente.
//  Avec, il continue à fonctionner et reprend quand la réponse arrive.
//
//  C'est comme envoyer un SMS et continuer à travailler
//  au lieu d'attendre debout près de votre téléphone.

async function appelerAPI(route, options = {}) {
    try {
        const url      = API.BASE_URL + route;
        const reponse  = await fetch(url, options);

        // Si le serveur répond avec une erreur HTTP (4xx, 5xx)
        if (!reponse.ok) {
            const erreur = await reponse.json();
            throw new Error(erreur.erreur || `Erreur HTTP ${reponse.status}`);
        }

        // Convertir la réponse JSON en objet JavaScript
        return await reponse.json();

    } catch (erreur) {
        // Distinguer "serveur éteint" de "erreur dans la réponse"
        if (erreur.name === 'TypeError') {
            throw new Error('Serveur Flask non accessible. Lancez : python app.py');
        }
        throw erreur;
    }
}


// --- BLOC 3 : FONCTIONS MÉTIER --------------------------------
//
//  Une fonction par action — chacune appelle appelerAPI()
//  avec les bons paramètres. C'est le principe DRY :
//  "Don't Repeat Yourself" — on n'écrit la logique qu'une fois.


// ── Analyser un fichier P&L ───────────────────────────────
//
//  FormData = objet JavaScript pour envoyer des fichiers.
//  Équivalent d'un formulaire HTML avec enctype="multipart/form-data".
//  C'est le seul moyen d'envoyer un fichier binaire (Excel) via fetch().

async function analyserPL(fichier, infos = {}) {
    const formData = new FormData();
    formData.append('fichier',     fichier);                    // le fichier Excel
    formData.append('statut',      infos.statut      || 'vente');
    formData.append('secteur',     infos.secteur     || '');
    formData.append('region',      infos.region      || '');
    formData.append('description', infos.description || '');

    return appelerAPI(API.ROUTES.analyser, {
        method: 'POST',
        body:   formData,
        // Note : ne pas mettre Content-Type ici — le navigateur
        // le définit automatiquement avec le bon "boundary" pour FormData
    });
}


// ── Récupérer tous les dossiers (avec filtres optionnels) ─
//
//  URLSearchParams construit automatiquement la chaîne de filtres :
//  { score_min: 75, profil: 'Premium' } → "?score_min=75&profil=Premium"

async function recupererDossiers(filtres = {}) {
    const params = new URLSearchParams();

    if (filtres.score_min) params.append('score_min', filtres.score_min);
    if (filtres.profil)    params.append('profil',    filtres.profil);
    if (filtres.statut)    params.append('statut',    filtres.statut);
    if (filtres.secteur)   params.append('secteur',   filtres.secteur);
    if (filtres.tri)       params.append('tri',        filtres.tri);

    const route = API.ROUTES.dossiers + (params.toString() ? '?' + params : '');
    return appelerAPI(route);
}


// ── Récupérer un dossier précis ───────────────────────────
async function recupererDossier(id) {
    return appelerAPI(API.ROUTES.dossier + id);
}


// ── Modifier le statut ou secteur d'un dossier ───────────
//
//  PATCH = modification partielle (seuls les champs envoyés changent)
//  JSON.stringify() convertit l'objet JS en texte JSON pour l'envoi

async function modifierDossier(id, champs) {
    return appelerAPI(API.ROUTES.dossier + id, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(champs),
    });
}


// ── Supprimer un dossier ──────────────────────────────────
async function supprimerDossier(id) {
    return appelerAPI(API.ROUTES.dossier + id, { method: 'DELETE' });
}


// ── Statistiques du marché ────────────────────────────────
async function recupererStats() {
    return appelerAPI(API.ROUTES.stats);
}


// ── Vérifier que le serveur est accessible ────────────────
async function verifierServeur() {
    try {
        const reponse = await appelerAPI(API.ROUTES.ping);
        return reponse.status === 'ok';
    } catch {
        return false;
    }
}


// --- BLOC 4 : INDICATEUR DE CONNEXION ------------------------
//
//  Affiche un badge vert/rouge dans le coin de chaque page
//  pour indiquer si le serveur Flask est actif.
//  Vérifie toutes les 10 secondes.

async function afficherEtatConnexion() {
    const badge = document.getElementById('connexion-badge');
    if (!badge) return;

    const actif = await verifierServeur();
    badge.textContent = actif ? '● API connectée' : '● API hors ligne';
    badge.style.color = actif ? '#4ade80' : '#f87171';
}

// Vérifier au chargement de la page puis toutes les 10 secondes
document.addEventListener('DOMContentLoaded', () => {
    afficherEtatConnexion();
    setInterval(afficherEtatConnexion, 10_000);
});


// --- BLOC 5 : UTILITAIRES ------------------------------------

// Formater un nombre en euros (réutilisé dans toutes les pages)
function formaterEuros(valeur) {
    if (valeur >= 1_000_000) return (valeur / 1_000_000).toFixed(2).replace('.', ',') + ' M€';
    if (valeur >= 1_000)     return (valeur / 1_000).toFixed(0) + ' k€';
    return valeur + ' €';
}

// Formater un pourcentage
function formaterPct(valeur) {
    return (valeur >= 0 ? '+' : '') + valeur.toFixed(1) + ' %';
}

// Couleur selon le profil
function couleurProfil(profil) {
    return profil === 'Premium'  ? '#4ade80' :
           profil === 'Standard' ? '#fbbf24' : '#f87171';
}

// Afficher un message d'erreur dans un conteneur
function afficherErreur(conteneurId, message) {
    const el = document.getElementById(conteneurId);
    if (el) {
        el.innerHTML = `
            <div style="text-align:center;padding:40px;color:#f87171;font-family:monospace;font-size:13px">
                ⚠️ ${message}
            </div>`;
    }
}
