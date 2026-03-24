#!/usr/bin/env python3
"""
Client en ligne de commande pour l'API REST de correction orthographique.

Usage :
    echo "Texte à corriger" | python spellcheck_client.py [--url URL] [--language LANG] [--technique TECH]

Arguments :
    --url        URL du serveur HTTP (défaut: http://127.0.0.1:5000)
    --language   Langue du texte, ou 'auto' pour détection automatique (défaut: auto)
    --technique  Technique de correction : 'levenshtein' ou 'prefsuff' (défaut: levenshtein)

Comportement :
    - Lit le texte depuis l'entrée standard
    - Interroge l'API /spellcheck
    - Pour chaque mot inconnu, remplace par la première suggestion
    - Affiche le texte corrigé sur la sortie standard
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def spellcheck(url: str, text: str, language: str, technique: str) -> dict:
    """
    Appelle l'API REST de correction orthographique.
    """
    endpoint = url.rstrip("/") + "/spellcheck"
    payload = json.dumps({
        "text": text,
        "language": language,
        "technique": technique,
    }).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERREUR] HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERREUR] Impossible de joindre le serveur : {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERREUR] Réponse JSON invalide : {e}", file=sys.stderr)
        sys.exit(1)


def apply_corrections(text: str, errors: list[dict]) -> str:
    """
    Applique les corrections au texte en utilisant les positions caractères
    renvoyées par l'API (`start`, `end`).

    Pour chaque mot inconnu, on remplace par la première suggestion disponible.
    """
    if not errors:
        return text

    # On trie par position croissante dans le texte original
    errors_sorted = sorted(errors, key=lambda e: e["start"])

    parts = []
    last_end = 0

    for error in errors_sorted:
        start = error.get("start")
        end = error.get("end")
        suggestions = error.get("suggestions", [])

        # On garde le texte inchangé avant le mot
        parts.append(text[last_end:start])

        # On remplace par la première suggestion, sinon on garde le mot original
        if suggestions:
            parts.append(suggestions[0])
        else:
            parts.append(text[start:end])

        last_end = end

    parts.append(text[last_end:])
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Client CLI de correction orthographique",
        epilog="Exemple : echo 'Bonjour, je sui heurex' | python spellcheck_client.py --language auto",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000",
        help="URL du serveur HTTP (défaut: http://127.0.0.1:5000)",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Langue du texte ou 'auto' pour détection automatique (défaut: auto)",
    )
    parser.add_argument(
        "--technique",
        default="levenshtein",
        choices=["levenshtein", "prefsuff"],
        help="Technique de correction (défaut: levenshtein)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Affiche les détails des erreurs sur stderr",
    )
    args = parser.parse_args()

    if sys.stdin.isatty():
        print("[INFO] Entrez le texte à corriger (Ctrl+D pour terminer) :", file=sys.stderr)

    text = sys.stdin.read()

    if not text.strip():
        print("[ERREUR] Aucun texte fourni.", file=sys.stderr)
        sys.exit(1)

    result = spellcheck(args.url, text, args.language, args.technique)
    errors = result.get("errors", [])
    detected_language = result.get("language", "?")

    if args.verbose:
        print(f"[INFO] Langue détectée : {detected_language}", file=sys.stderr)
        print(f"[INFO] Erreurs trouvées : {len(errors)}", file=sys.stderr)
        for e in errors:
            suggestions = ", ".join(e.get("suggestions", []))
            print(
                f"  - Position mot={e.get('position')} caractères=[{e.get('start')},{e.get('end')}] "
                f"'{e.get('word')}' → {suggestions}",
                file=sys.stderr
            )

    corrected = apply_corrections(text, errors)
    print(corrected, end="")


if __name__ == "__main__":
    main()