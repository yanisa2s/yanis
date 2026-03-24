"""
Serveur HTTP de correction orthographique (Flask + Jinja2).
"""

import argparse
import re
import sys
import socket

from flask import Flask, jsonify, render_template, request

from dictionary_manager import DictionaryManager

DEFAULT_HTTP_HOST = "0.0.0.0"
DEFAULT_HTTP_PORT = 5000
DEFAULT_UDP_HOST = "127.0.0.1"
DEFAULT_UDP_PORT = 9999
DEFAULT_DICT_DIR = "dictionaries"
DEFAULT_MAX_SUGGESTIONS = 5

app = Flask(__name__)

dict_manager: DictionaryManager = None
udp_host: str = DEFAULT_UDP_HOST
udp_port: int = DEFAULT_UDP_PORT
max_suggestions: int = DEFAULT_MAX_SUGGESTIONS


def query_udp(language: str, word: str, technique: str) -> dict:
    """
    Interroge le serveur UDP pour vérifier/corriger un mot.
    Version simple et fiable, avec timeout.
    """
    message = f"{language}:{word}:{technique}"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(60.0)

    try:
        sock.sendto(message.encode("utf-8"), ("127.0.0.1", 9999))
        data, _ = sock.recvfrom(4096)
        response = data.decode("utf-8")
    finally:
        sock.close()

    parts = response.split(":")

    if len(parts) >= 2 and parts[1] == "OK":
        return {"word": parts[0], "ok": True, "suggestions": []}

    elif len(parts) >= 2 and parts[1] == "KO":
        return {
            "word": parts[0],
            "ok": False,
            "suggestions": [s for s in parts[2:] if s]
        }

    else:
        raise Exception(response)


def spellcheck_text(text: str, language: str, technique: str):
    if language == "auto":
        language = dict_manager.detect_language(text)

    tokens = list(re.finditer(r"[a-zA-ZÀ-ÿ]+", text))
    results = []

    for i, match in enumerate(tokens):
        word = match.group()
        result = query_udp(language, word, technique)
        results.append({
            "position": i,
            "start": match.start(),
            "end": match.end(),
            "word": word,
            "ok": result["ok"],
            "suggestions": result.get("suggestions", []),
        })

    return results, language


def build_annotated_html(text: str, results: list) -> str:
    if not results:
        return text

    parts = []
    last_end = 0

    for r in results:
        parts.append(text[last_end:r["start"]])

        if r["ok"]:
            parts.append(f'<span class="word-ok">{r["word"]}</span>')
        else:
            suggestions_html = ""
            if r["suggestions"]:
                items = "".join(f'<li>{s}</li>' for s in r["suggestions"][:5])
                suggestions_html = f'<ul class="suggestions">{items}</ul>'

            parts.append(
                f'<span class="word-error">'
                f'{r["word"]}'
                f'<span class="tooltip">{suggestions_html}</span>'
                f'</span>'
            )

        last_end = r["end"]

    parts.append(text[last_end:])
    return "".join(parts)


@app.route("/", methods=["GET"])
def index():
    languages = ["auto"] + sorted(dict_manager.get_languages())
    return render_template("index.html", languages=languages)


@app.route("/check", methods=["POST"])
def check():
    text = request.form.get("text", "").strip()
    language = request.form.get("language", "auto")
    technique = request.form.get("technique", "levenshtein")
    languages = ["auto"] + sorted(dict_manager.get_languages())

    if not text:
        return render_template("index.html", languages=languages, error="Veuillez entrer un texte.")

    try:
        results, detected_language = spellcheck_text(text, language, technique)
    except Exception as e:
        return render_template(
            "index.html",
            languages=languages,
            error=f"Erreur lors de la correction : {e}"
        )

    annotated = build_annotated_html(text, results)

    return render_template(
        "result.html",
        text=text,
        annotated=annotated,
        results=results,
        language=language,
        detected_language=detected_language,
        technique=technique,
        languages=languages,
        error_count=sum(1 for r in results if not r["ok"]),
    )


@app.route("/api-doc", methods=["GET"])
def api_doc():
    return render_template("api_doc.html")


@app.route("/spellcheck", methods=["POST"])
def api_spellcheck():
    if request.is_json:
        data = request.get_json(force=True)
    else:
        data = request.form.to_dict()

    text = data.get("text", "").strip()
    language = data.get("language", "auto")
    technique = data.get("technique", "levenshtein")

    if not text:
        return jsonify({"error": "Le champ 'text' est requis"}), 400

    if technique not in ("levenshtein", "prefsuff"):
        return jsonify({"error": "technique doit être 'levenshtein' ou 'prefsuff'"}), 400

    try:
        results, detected_language = spellcheck_text(text, language, technique)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    errors = [
        {
            "position": r["position"],
            "start": r["start"],
            "end": r["end"],
            "word": r["word"],
            "suggestions": r["suggestions"],
        }
        for r in results if not r["ok"]
    ]

    return jsonify({
        "language": detected_language,
        "technique": technique,
        "errors": errors
    })


def main():
    global dict_manager, udp_host, udp_port, max_suggestions

    parser = argparse.ArgumentParser(description="Serveur HTTP de correction orthographique")
    parser.add_argument("--http-host", default=DEFAULT_HTTP_HOST)
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT)
    parser.add_argument("--udp-host", default=DEFAULT_UDP_HOST)
    parser.add_argument("--udp-port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--dict", default=DEFAULT_DICT_DIR)
    parser.add_argument("--max-suggestions", type=int, default=DEFAULT_MAX_SUGGESTIONS)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    udp_host = args.udp_host
    udp_port = args.udp_port
    max_suggestions = args.max_suggestions

    try:
        dict_manager = DictionaryManager(args.dict)
    except (FileNotFoundError, ValueError) as e:
        print(f"[ERREUR] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[HTTP] Démarrage sur http://{args.http_host}:{args.http_port}")
    print(f"[HTTP] Serveur UDP cible : {udp_host}:{udp_port}")
    app.run(host=args.http_host, port=args.http_port, debug=args.debug)


if __name__ == "__main__":
    main()