"""
Serveur UDP de correction orthographique.
Compatible Windows (gestion du WinError 10054).
"""

import argparse
import socket
import sys

from dictionary_manager import DictionaryManager
from spell_corrector import get_suggestions

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9999
DEFAULT_DICT_DIR = "dictionaries"
DEFAULT_MAX_SUGGESTIONS = 5


def parse_request(data: str):
    parts = data.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Format invalide. Attendu 'langue:mot:technique', reçu : '{data}'")
    language, word, technique = parts[0].strip(), parts[1].strip(), parts[2].strip()
    if not language or not word or not technique:
        raise ValueError("langue, mot et technique ne peuvent pas être vides")
    if technique not in ("levenshtein", "prefsuff"):
        raise ValueError(f"Technique invalide : '{technique}'")
    return language, word, technique


def handle_request(data: str, dict_manager: DictionaryManager, max_suggestions: int) -> str:
    try:
        language, word, technique = parse_request(data)

        if language not in dict_manager.get_languages():
            return f"ERREUR:Langue inconnue '{language}'"

        if dict_manager.contains(language, word):
            return f"{word}:OK"

        dictionary = dict_manager.get_words(language)
        suggestions = get_suggestions(word, dictionary, technique, max_suggestions)

        if suggestions:
            return f"{word}:KO:" + ":".join(suggestions)
        return f"{word}:KO"

    except Exception as e:
        return f"ERREUR:{e}"


def run_server(host: str, port: int, dict_manager: DictionaryManager, max_suggestions: int):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"[UDP] Serveur démarré sur {host}:{port}")
    print(f"[UDP] Langues disponibles : {', '.join(dict_manager.get_languages())}")
    print(f"[UDP] Nombre max de suggestions : {max_suggestions}")
    print("[UDP] En attente de requêtes... (Ctrl+C pour arrêter)\n")

    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                request = data.decode("utf-8")
                print(f"[UDP] Requête de {addr}: {request!r}")
                response = handle_request(request, dict_manager, max_suggestions)
                print(f"[UDP] Réponse : {response!r}")
                sock.sendto(response.encode("utf-8"), addr)
            except ConnectionResetError:
                print("[UDP] Connexion reset ignorée (Windows), on continue...")
                continue
            except OSError as e:
                print(f"[UDP] Erreur réseau ignorée : {e}")
                continue
    except KeyboardInterrupt:
        print("\n[UDP] Arrêt du serveur.")
    finally:
        sock.close()


def main():
    parser = argparse.ArgumentParser(description="Serveur UDP de correction orthographique")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--dict", default=DEFAULT_DICT_DIR)
    parser.add_argument("--max-suggestions", type=int, default=DEFAULT_MAX_SUGGESTIONS)
    args = parser.parse_args()

    try:
        dict_manager = DictionaryManager(args.dict)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERREUR] {e}", file=sys.stderr)
        sys.exit(1)

    run_server(args.host, args.port, dict_manager, args.max_suggestions)


if __name__ == "__main__":
    main()