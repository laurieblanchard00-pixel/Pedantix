"""
=============================================================
 PÉDANTIX CLONE — Serveur Web Local
=============================================================
 Lance un serveur HTTP local.
 Aucune dépendance externe requise !

 Usage :
   python server.py
 Puis ouvrir : http://localhost:8000
 Sur iPhone  : http://[IP-DU-PC]:8000  (même Wi-Fi)
=============================================================
"""

import json
import os
import sys
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from game_engine import GameManager, PedantixGame, WIKIPEDIA_PAGES

# ── État global ──
GAMES: dict = {}
GAME_MODES: dict = {}
manager = GameManager()

MANIFEST = json.dumps({
    "name": "Pédantix Clone",
    "short_name": "Pédantix",
    "description": "Devinez la page Wikipédia en proposant des mots",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0e0e11",
    "theme_color": "#0e0e11",
    "orientation": "portrait",
    "icons": [
        {"src": "/icon.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon.png", "sizes": "512x512", "type": "image/png"}
    ]
}, ensure_ascii=False)

# SVG icon encodé en PNG minimal (1x1 bleu, juste pour satisfaire iOS)
# On génère un vrai PNG 192x192 bleu avec le texte "P"
def make_icon_png():
    """Génère un PNG 192x192 simple sans dépendance."""
    import struct, zlib
    w, h = 192, 192
    # Couleur de fond #0e0e11, lettre P en #4d8ef5 approximative
    bg = (14, 14, 17)
    fg = (77, 142, 245)

    # Créer les pixels (RGB)
    pixels = []
    for y in range(h):
        row = []
        for x in range(w):
            # Cercle de fond bleu
            cx, cy = w//2, h//2
            r = 80
            dist = ((x-cx)**2 + (y-cy)**2)**0.5
            if dist <= r:
                row.extend(list(fg))
            else:
                row.extend(list(bg))
        pixels.append(bytes([0] + row))  # filtre None pour chaque ligne

    raw = b''.join(pixels)
    compressed = zlib.compress(raw, 9)

    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        crc = zlib.crc32(name + data) & 0xffffffff
        return c + struct.pack('>I', crc)

    png = (
        b'\x89PNG\r\n\x1a\n'
        + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
        + chunk(b'IDAT', compressed)
        + chunk(b'IEND', b'')
    )
    return png

ICON_PNG = make_icon_png()

SW_JS = """
// Service Worker minimal pour PWA iOS
const CACHE = 'pedantix-v1';
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(['/']))
  );
});
self.addEventListener('fetch', e => {
  if (e.request.url.includes('/api/')) return; // pas de cache pour l'API
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request))
  );
});
"""


def get_or_create_game(session_id, mode='daily', custom=None):
    game = manager.start_game(mode=mode, custom_title=custom)
    GAMES[session_id] = game
    GAME_MODES[session_id] = mode
    return game


class GameHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Silence les logs

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        p = self.path.split('?')[0]
        if p in ('/', '/index.html'):
            self._serve_file('index.html', 'text/html; charset=utf-8')
        elif p == '/manifest.json':
            self._serve_bytes(MANIFEST.encode(), 'application/json')
        elif p == '/sw.js':
            self._serve_bytes(SW_JS.encode(), 'application/javascript')
        elif p == '/icon.png':
            self._serve_bytes(ICON_PNG, 'image/png')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        p = self.path

        if p == '/api/new_game':
            mode = data.get('mode', 'daily')
            custom = data.get('custom', None)
            session = data.get('session', 'default')
            game = get_or_create_game(session, mode, custom)
            self._json({
                'ok': True,
                'tokens': game.get_display_tokens(),
                'title_tokens': game.get_title_display(),
                'stats': game.get_stats(),
            })

        elif p == '/api/guess':
            session = data.get('session', 'default')
            word = data.get('word', '').strip()
            game = GAMES.get(session)
            if not game:
                game = get_or_create_game(session)
            result = game.guess(word)
            if result.get('won'):
                manager.save_result(game, GAME_MODES.get(session, 'random'))
            self._json({
                'result': result,
                'tokens': game.get_display_tokens(),
                'title_tokens': game.get_title_display(),
                'stats': game.get_stats(),
                'guesses': game.guesses[-10:],
            })

        elif p == '/api/history':
            self._json({'history': manager.get_history()[-20:]})

        else:
            self.send_response(404)
            self.end_headers()

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, filename, content_type):
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'rb') as f:
            content = f.read()
        self._serve_bytes(content, content_type)

    def _serve_bytes(self, content, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(content)


def get_local_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run(port=8000):
    server = HTTPServer(('0.0.0.0', port), GameHandler)
    local_ip = get_local_ip()

    # Détecter si on est sur Railway (pas d'affichage IP locale)
    on_cloud = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT')

    print(f"\n{'═'*58}")
    print(f"  🧠  PÉDANTIX CLONE")
    print(f"{'═'*58}")
    if on_cloud:
        print(f"  ☁️   Serveur cloud démarré sur le port {port}")
    else:
        print(f"  💻  Sur ce PC      →  http://localhost:{port}")
        print(f"  📱  Sur iPhone     →  http://{local_ip}:{port}")
        print(f"{'─'*58}")
        print(f"  📲  INSTALLER SUR IPHONE :")
        print(f"      1. Ouvrez Safari → http://{local_ip}:{port}")
        print(f"      2. Appuyez sur ⎋ (Partager) en bas")
        print(f"      3. Choisissez « Sur l'écran d'accueil »")
        print(f"      4. L'app apparaît comme une vraie appli !")
        # Ouvrir le navigateur automatiquement (local seulement)
        import threading, webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    print(f"{'─'*58}")
    print(f"  ⛔  Ctrl+C pour arrêter")
    print(f"{'═'*58}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Serveur arrêté. À bientôt !")


if __name__ == '__main__':
    # Railway injecte le PORT via variable d'environnement
    port = int(os.environ.get('PORT', 8000))
    run(port)
