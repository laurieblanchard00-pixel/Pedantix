"""
=============================================================
 PÉDANTIX CLONE — Moteur de Jeu
=============================================================
 Reproduit le fonctionnement de Pédantix :
 - Récupère une page Wikipédia (intro uniquement)
 - Masque tous les mots
 - Le joueur propose des mots successifs
 - Les mots exacts sont révélés en blanc
 - Les mots proches sémantiquement sont grisés (par niveau)
 - Victoire quand tous les mots du TITRE sont trouvés
=============================================================
"""

import re
import unicodedata
import json
import os
import random
import hashlib
from datetime import datetime
from difflib import SequenceMatcher


# ─────────────────────────────────────────────
#  LISTE DE PAGES WIKIPEDIA POUR LE JEU
#  (On simule la sélection quotidienne + aléatoire)
# ─────────────────────────────────────────────

WIKIPEDIA_PAGES = [
    "Tour Eiffel",
    "Napoléon Bonaparte",
    "Révolution française",
    "Louis XIV",
    "Paris",
    "Versailles",
    "Charles de Gaulle",
    "Victor Hugo",
    "Marcel Proust",
    "Albert Camus",
    "Simone de Beauvoir",
    "Monet",
    "Gustave Eiffel",
    "Lumière (frères)",
    "Marie Curie",
    "Louis Pasteur",
    "René Descartes",
    "Voltaire",
    "Molière",
    "Jean-Paul Sartre",
    "Jeanne d'Arc",
    "Charlemagne",
    "Jules César",
    "Cléopâtre",
    "Léonard de Vinci",
    "Michel-Ange",
    "Shakespeare",
    "Mozart",
    "Beethoven",
    "Darwin",
    "Einstein",
    "Freud",
    "Newton",
    "Galilée",
    "Christophe Colomb",
    "Magellan",
    "Amazon (fleuve)",
    "Himalaya",
    "Sahara",
    "Atlantique",
    "Photosynthèse",
    "Évolution",
    "ADN",
    "Big Bang",
    "Trou noir",
    "Lune",
    "Mars (planète)",
    "Dinosaure",
    "Requin blanc",
    "Baleine bleue",
]


# ─────────────────────────────────────────────
#  UTILITAIRES TEXTE
# ─────────────────────────────────────────────

def normalize(word: str) -> str:
    """Normalise un mot : minuscule, sans accents, sans ponctuation."""
    word = word.lower().strip()
    # Supprimer les accents
    word = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if unicodedata.category(c) != 'Mn'
    )
    # Garder uniquement les lettres et chiffres
    word = re.sub(r"[^a-z0-9]", "", word)
    return word


def stem_word(word: str) -> str:
    """Stemming simple français : retire suffixes courants."""
    w = normalize(word)
    suffixes = ['ement', 'ation', 'itions', 'ition', 'ments', 'ment',
                'aient', 'aient', 'euse', 'eux', 'aux', 'aux',
                'ique', 'iques', 'iste', 'istes', 'iser', 'ise',
                'elles', 'elle', 'els', 'el', 'aux', 'al',
                'ants', 'ant', 'ente', 'ents', 'ent',
                'ées', 'ée', 'és', 'é',
                'ons', 'ions', 'ez', 'er', 'ir',
                'ux', 'ux', 's']
    for suffix in suffixes:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def similarity_score(word1: str, word2: str) -> float:
    """
    Calcule un score de proximité entre deux mots.
    Utilise plusieurs heuristiques pour simuler Word2Vec :
    - Correspondance exacte → 1.0
    - Même radical (stem) → 0.85
    - Correspondance partielle (SequenceMatcher) → valeur proportionnelle
    - Sinon → 0.0
    """
    n1 = normalize(word1)
    n2 = normalize(word2)

    if not n1 or not n2:
        return 0.0

    # Exact match
    if n1 == n2:
        return 1.0

    # Même radical
    if stem_word(n1) == stem_word(n2) and len(stem_word(n1)) >= 3:
        return 0.85

    # Préfixe commun long
    min_len = min(len(n1), len(n2))
    if min_len >= 4:
        common_prefix = 0
        for a, b in zip(n1, n2):
            if a == b:
                common_prefix += 1
            else:
                break
        if common_prefix >= min_len * 0.75:
            return 0.70

    # SequenceMatcher pour similarité de chaîne
    ratio = SequenceMatcher(None, n1, n2).ratio()
    if ratio >= 0.80:
        return round(ratio * 0.65, 2)

    return 0.0


def proximity_level(score: float) -> str:
    """
    Retourne le niveau de proximité visuel.
    'exact'  → le mot est dans le texte
    'proche' → très proche (gris foncé)
    'tiede'  → proche (gris moyen)
    'froid'  → peu proche (gris clair)
    'rien'   → aucun rapport
    """
    if score >= 1.0:
        return 'exact'
    elif score >= 0.80:
        return 'proche'
    elif score >= 0.65:
        return 'tiede'
    elif score >= 0.50:
        return 'froid'
    else:
        return 'rien'


# ─────────────────────────────────────────────
#  RÉCUPÉRATION WIKIPEDIA
# ─────────────────────────────────────────────

def get_wikipedia_intro(title: str) -> tuple[str, str]:
    """
    Récupère 3 à 4 paragraphes depuis une page Wikipédia.
    Sans exintro : récupère le corps complet, puis on garde
    les N premiers paragraphes non vides jusqu'à ~500 mots.
    """
    try:
        import urllib.request
        import urllib.parse

        params = urllib.parse.urlencode({
            'action': 'query',
            'titles': title,
            'prop': 'extracts',
            # PAS de exintro : on veut tout le corps de l'article
            'explaintext': True,
            'exsectionformat': 'plain',  # pas de titres de sections
            'redirects': True,
            'format': 'json',
            'utf8': True,
        })
        url = f"https://fr.wikipedia.org/w/api.php?{params}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'PedantixClone/1.0 (educational game)'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        pages = data.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if page_id == '-1':
                break
            real_title = page_data.get('title', title)
            full_text = page_data.get('extract', '').strip()
            if not full_text or len(full_text) < 50:
                break

            # Découper en paragraphes (séparés par lignes vides ou \n)
            paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text) if p.strip()]

            # Filtrer les paragraphes trop courts (titres de sections, notes)
            # et ceux qui ressemblent à des titres (pas de point, courts)
            good = []
            for p in paragraphs:
                # Ignorer les pseudo-titres de section (courts, sans ponctuation de fin)
                if len(p) < 80 and not re.search(r'[.!?]', p):
                    continue
                good.append(p)

            # Prendre les paragraphes jusqu'à atteindre ~400-600 mots
            selected = []
            total_words = 0
            for p in good:
                words_in_p = len(p.split())
                selected.append(p)
                total_words += words_in_p
                # S'arrêter après 4 paragraphes ou ~600 mots
                if len(selected) >= 4 or total_words >= 600:
                    break

            # Si on n'a rien de bon, prendre les 600 premiers mots bruts
            if not selected:
                words = full_text.split()
                return real_title, ' '.join(words[:600]) + '…'

            extract = '\n\n'.join(selected)
            return real_title, extract

    except Exception:
        pass

    # ── Fallback : API summary ──
    try:
        import urllib.request
        import urllib.parse
        encoded = urllib.parse.quote(title.replace(' ', '_'))
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'PedantixClone/1.0 (educational game)'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get('title', title), data.get('extract', '')
    except Exception:
        pass

    # ── Fallback final ──
    return title, (
        f"{title} est un sujet important dans l'histoire et la culture mondiale. "
        f"Il est reconnu pour ses nombreuses contributions et son influence considérable. "
        f"Son histoire est riche et complexe, marquée par des événements déterminants "
        f"qui ont façonné le monde tel que nous le connaissons aujourd'hui. "
        f"De nombreux chercheurs et historiens se sont penchés sur ce sujet fascinant."
    )


# ─────────────────────────────────────────────
#  TOKENISATION DU TEXTE
# ─────────────────────────────────────────────

def tokenize_text(text: str) -> list[dict]:
    """
    Découpe le texte en tokens : mots et non-mots.
    Les tirets et apostrophes sont toujours visibles (ponctuation normale).
    Chaque partie d'un mot composé ou élidé est un mot indépendant.
    Ex : "l'accusé"   → [l] ['] [accusé]
         "sous-estime" → [sous] [-] [estime]
    """
    tokens = []
    # Séparer sur tout ce qui n'est pas une lettre/chiffre
    # (tirets, apostrophes, espaces, virgules, etc.)
    pattern = re.compile(r"([a-zA-ZÀ-ÿ0-9]+|[^a-zA-ZÀ-ÿ0-9]+)")

    for match in pattern.finditer(text):
        chunk = match.group()
        if re.match(r"^[a-zA-ZÀ-ÿ0-9]", chunk):
            # Mot normal
            tokens.append({
                'type': 'word',
                'text': chunk,
                'normalized': normalize(chunk),
                'revealed': False,
                'proximity': 'rien',
                'best_score': 0.0,
            })
        else:
            # Toute ponctuation est visible dès le début
            tokens.append({
                'type': 'punct',
                'text': chunk,
                'revealed': True,
                'proximity': 'exact',
            })
    return tokens


# ─────────────────────────────────────────────
#  CLASSE PRINCIPALE : PARTIE
# ─────────────────────────────────────────────

class PedantixGame:
    """
    Représente une partie de Pédantix.
    
    Utilisation :
        game = PedantixGame()
        game.start("Tour Eiffel")
        result = game.guess("construction")
        # result = {'matches': 3, 'proximity_hits': [...], 'won': False}
    """

    def __init__(self):
        self.title = ""
        self.title_words = []          # mots normalisés du titre
        self.intro_text = ""
        self.tokens = []               # liste de tokens (voir tokenize_text)
        self.guesses = []              # historique des propositions
        self.guess_count = 0
        self.won = False
        self.started = False
        self.start_time = None

    def start(self, page_title: str) -> bool:
        """Initialise la partie avec une page Wikipedia."""
        real_title, intro = get_wikipedia_intro(page_title)

        self.title = real_title
        self.intro_text = intro
        self.tokens = tokenize_text(intro)

        # Mots du titre (normalisés)
        self.title_words = [
            normalize(w)
            for w in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", real_title)
            if len(normalize(w)) >= 2
        ]

        # Tracker quels mots du titre ont été trouvés
        self.title_found = {w: False for w in self.title_words}

        self.guesses = []
        self.guess_count = 0
        self.won = False
        self.started = True
        self.start_time = datetime.now()
        return True

    def guess(self, word: str) -> dict:
        """
        Traite une proposition du joueur.
        
        Retourne un dict :
        {
            'word': str,                  # le mot proposé
            'matches': int,               # nb de mots révélés (exact)
            'proximity_results': [        # détail par token mis à jour
                {'text': str, 'proximity': str, 'score': float}
            ],
            'already_guessed': bool,
            'won': bool,
            'title_progress': int,        # % du titre découvert
        }
        """
        if not self.started:
            return {'error': 'Partie non démarrée'}

        word = word.strip()
        if not word:
            return {'error': 'Mot vide'}

        norm_guess = normalize(word)

        # Déjà proposé ?
        already = norm_guess in [normalize(g['word']) for g in self.guesses]

        matches = 0
        proximity_results = []

        for token in self.tokens:
            if token['type'] != 'word':
                continue

            score = similarity_score(word, token['text'])
            level = proximity_level(score)

            if score > token.get('best_score', 0.0):
                token['best_score'] = score
                token['proximity'] = level
                # Mémoriser le mot proposé (pour l'affichage orange)
                if level != 'exact':
                    token['best_word'] = word
                else:
                    token.pop('best_word', None)

                if level == 'exact':
                    token['revealed'] = True
                    matches += 1
                    # Vérifier si c'est un mot du titre
                    if token['normalized'] in self.title_found:
                        self.title_found[token['normalized']] = True

            if level != 'rien':
                proximity_results.append({
                    'text': token['text'],
                    'proximity': level,
                    'score': round(score, 2),
                })

        self.guess_count += 1
        self.guesses.append({
            'word': word,
            'matches': matches,
            'count': self.guess_count,
        })

        # Vérifier la victoire
        self.won = all(self.title_found.values()) and len(self.title_words) > 0

        # Progression du titre
        found_title = sum(1 for v in self.title_found.values() if v)
        title_progress = int(found_title / max(len(self.title_words), 1) * 100)

        return {
            'word': word,
            'matches': matches,
            'proximity_results': proximity_results,
            'already_guessed': already,
            'won': self.won,
            'title_progress': title_progress,
            'guess_count': self.guess_count,
        }

    def get_display_tokens(self) -> list[dict]:
        """
        Retourne les tokens pour l'affichage :
        - mots révélés → texte visible
        - mots non révélés → blocs gris (longueur visible, niveau de gris)
        """
        display = []
        for token in self.tokens:
            if token['type'] == 'punct':
                display.append({'type': 'punct', 'text': token['text']})
            elif token['type'] == 'hidden_punct':
                # Tiret masqué : visible seulement quand les mots adjacents sont révélés
                display.append({
                    'type': 'hidden_punct',
                    'text': token['text'],
                    'revealed': token.get('revealed', False),
                    'proximity': token.get('proximity', 'rien'),
                    'length': 1,
                })
            elif token['revealed']:
                display.append({
                    'type': 'word',
                    'text': token['text'],
                    'revealed': True,
                    'proximity': 'exact',
                })
            else:
                display.append({
                    'type': 'word',
                    'text': None,
                    'length': len(token['text']),
                    'revealed': False,
                    'proximity': token['proximity'],
                    'best_word': token.get('best_word', None),
                })
        return display

    def get_title_display(self) -> list[dict]:
        """Retourne les mots du titre (révélés ou masqués)."""
        title_tokens = []
        for match in re.finditer(r"[a-zA-ZÀ-ÿ0-9]+|[^a-zA-ZÀ-ÿ0-9]+", self.title):
            chunk = match.group()
            if re.match(r"^[a-zA-ZÀ-ÿ0-9]", chunk):
                norm = normalize(chunk)
                found = self.title_found.get(norm, False) if hasattr(self, 'title_found') else False
                title_tokens.append({
                    'type': 'word',
                    'text': chunk,
                    'revealed': found,
                    'length': len(chunk),
                })
            else:
                title_tokens.append({'type': 'punct', 'text': chunk})
        return title_tokens

    def get_stats(self) -> dict:
        """Retourne les statistiques de la partie."""
        elapsed = (datetime.now() - self.start_time).seconds if self.start_time else 0
        return {
            'guess_count': self.guess_count,
            'elapsed_seconds': elapsed,
            'won': self.won,
            'title': self.title if self.won else '???',
            'words_revealed': sum(1 for t in self.tokens if t['type'] == 'word' and t['revealed']),
            'words_total': sum(1 for t in self.tokens if t['type'] == 'word'),
        }


# ─────────────────────────────────────────────
#  GESTIONNAIRE DE PARTIES
# ─────────────────────────────────────────────

class GameManager:
    """
    Gère la sélection des pages et permet plusieurs parties par jour.
    
    - Partie du jour : déterministe (seed = date)
    - Parties libres : pages aléatoires
    - Historique sauvegardé en JSON local
    """

    SAVE_FILE = os.path.expanduser("~/.pedantix_saves.json")

    def __init__(self):
        self.history = self._load_history()

    def get_daily_page(self) -> str:
        """Retourne la page du jour (déterministe, change à midi)."""
        now = datetime.now()
        # La partie change à midi
        if now.hour < 12:
            seed_date = now.strftime("%Y-%m-%d") + "_morning"
        else:
            seed_date = now.strftime("%Y-%m-%d") + "_afternoon"

        # Hash déterministe → index dans la liste
        h = int(hashlib.md5(seed_date.encode()).hexdigest(), 16)
        idx = h % len(WIKIPEDIA_PAGES)
        return WIKIPEDIA_PAGES[idx]

    def get_random_page(self) -> str:
        """Retourne une page aléatoire (différente des récentes)."""
        recent = [e['page'] for e in self.history[-5:]]
        candidates = [p for p in WIKIPEDIA_PAGES if p not in recent]
        if not candidates:
            candidates = WIKIPEDIA_PAGES
        return random.choice(candidates)

    def get_custom_page(self, title: str) -> str:
        """Permet de jouer avec un titre personnalisé."""
        return title

    def start_game(self, mode: str = 'daily', custom_title: str = None) -> PedantixGame:
        """
        Crée et démarre une nouvelle partie.
        modes : 'daily', 'random', 'custom'
        """
        if mode == 'daily':
            page = self.get_daily_page()
        elif mode == 'random':
            page = self.get_random_page()
        elif mode == 'custom' and custom_title:
            page = self.get_custom_page(custom_title)
        else:
            page = self.get_random_page()

        game = PedantixGame()
        success = game.start(page)
        if success:
            print(f"✅ Partie démarrée : '{page}' ({mode})")
        return game

    def save_result(self, game: PedantixGame, mode: str):
        """Sauvegarde le résultat d'une partie terminée."""
        stats = game.get_stats()
        entry = {
            'date': datetime.now().isoformat(),
            'mode': mode,
            'page': game.title,
            'guesses': stats['guess_count'],
            'won': stats['won'],
            'time_seconds': stats['elapsed_seconds'],
        }
        self.history.append(entry)
        self._save_history()
        return entry

    def get_history(self) -> list:
        return self.history

    def _load_history(self) -> list:
        try:
            if os.path.exists(self.SAVE_FILE):
                with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            with open(self.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde : {e}")
