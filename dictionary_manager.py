"""
Module de gestion des dictionnaires orthographiques.
Charge et maintient en mémoire les dictionnaires de toutes les langues disponibles.
"""

import os
import re


class DictionaryManager:
    """Gère le chargement et l'accès aux dictionnaires de langues."""

    def __init__(self, dictionaries_dir: str):
        """
        Initialise le gestionnaire en chargeant tous les dictionnaires du répertoire.

        Args:
            dictionaries_dir: Chemin vers le répertoire contenant les fichiers .txt
        """
        self.dictionaries: dict[str, set[str]] = {}
        self.dictionaries_dir = dictionaries_dir
        self._load_all(dictionaries_dir)

    def _load_all(self, directory: str):
        """Charge tous les fichiers .txt du répertoire comme dictionnaires."""
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Répertoire introuvable : {directory}")

        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                language = filename[:-4]  # retire l'extension .txt
                filepath = os.path.join(directory, filename)
                self._load_dict(language, filepath)

        if not self.dictionaries:
            raise ValueError(f"Aucun dictionnaire trouvé dans {directory}")

    def _load_dict(self, language: str, filepath: str):
        """Charge un fichier dictionnaire en mémoire."""
        words = set()
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    words.add(word)
        self.dictionaries[language] = words
        print(f"[Dict] Chargé '{language}' : {len(words)} mots")

    def get_languages(self) -> list[str]:
        """Retourne la liste des langues disponibles."""
        return list(self.dictionaries.keys())

    def contains(self, language: str, word: str) -> bool:
        """Vérifie si un mot est dans le dictionnaire d'une langue (insensible à la casse)."""
        if language not in self.dictionaries:
            raise ValueError(f"Langue inconnue : {language}")
        return word.lower() in self.dictionaries[language]

    def get_words(self, language: str) -> set[str]:
        """Retourne l'ensemble des mots pour une langue donnée."""
        if language not in self.dictionaries:
            raise ValueError(f"Langue inconnue : {language}")
        return self.dictionaries[language]

    def detect_language(self, text: str) -> str:
        """
        Détecte la langue d'un texte en comptant les mots communs avec chaque dictionnaire.

        Comportement voulu pour un correcteur orthographique :
        - si des mots exacts du texte existent dans un dictionnaire, on prend la meilleure langue ;
        - si aucun mot exact n'est reconnu, on ne bloque pas :
          on prend 'french' si disponible, sinon la première langue disponible.
        """
        words = set(re.findall(r"[a-zA-ZÀ-ÿ]+", text.lower()))

        if not self.dictionaries:
            raise ValueError("Impossible de détecter la langue : aucun dictionnaire disponible")

        best_language = None
        best_count = -1

        for language, dictionary in self.dictionaries.items():
            count = len(words & dictionary)
            if count > best_count:
                best_count = count
                best_language = language

        if best_language is None:
            raise ValueError("Impossible de détecter la langue : aucun dictionnaire disponible")

        # Important : ne pas bloquer si le texte contient uniquement des fautes.
        if best_count == 0:
            if "french" in self.dictionaries:
                return "french"
            return next(iter(self.dictionaries.keys()))

        return best_language