"""
Module de correction orthographique.
Implémente les techniques Levenshtein et prefsuff pour suggérer des corrections.
"""


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcule la distance d'édition (Levenshtein) entre deux chaînes.
    Implémentation sans bibliothèque externe.

    Args:
        s1: Première chaîne
        s2: Deuxième chaîne

    Returns:
        Distance d'édition minimale (int)
    """
    len1, len2 = len(s1), len(s2)

    # Cas de base
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Matrice de programmation dynamique
    # On utilise deux rangées seulement pour économiser la mémoire
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            curr[j] = min(
                prev[j] + 1,       # suppression
                curr[j - 1] + 1,   # insertion
                prev[j - 1] + cost # substitution
            )
        prev, curr = curr, prev

    return prev[len2]


def common_prefix_length(s1: str, s2: str) -> int:
    """Retourne la longueur du préfixe commun entre deux chaînes."""
    length = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            length += 1
        else:
            break
    return length


def common_suffix_length(s1: str, s2: str) -> int:
    """Retourne la longueur du suffixe commun entre deux chaînes."""
    length = 0
    for c1, c2 in zip(reversed(s1), reversed(s2)):
        if c1 == c2:
            length += 1
        else:
            break
    return length


def prefsuff_score(x: str, y: str) -> float:
    """
    Calcule le score de similarité prefsuff entre deux mots.

    ps(x, y) = min(pc(x,y), sc(x,y)) / min(|x|, |y|)

    où pc = longueur du préfixe commun, sc = longueur du suffixe commun.
    Retourne 1.0 si les mots sont identiques, 0.0 si aucun préfixe/suffixe commun.

    Args:
        x: Premier mot
        y: Deuxième mot

    Returns:
        Score entre 0.0 et 1.0
    """
    if x == y:
        return 1.0

    min_len = min(len(x), len(y))
    if min_len == 0:
        return 0.0

    pc = common_prefix_length(x, y)
    sc = common_suffix_length(x, y)

    return min(pc, sc) / min_len


def get_suggestions_levenshtein(word: str, dictionary: set[str], max_suggestions: int = 5) -> list[str]:
    """
    Propose des corrections par distance de Levenshtein.

    Args:
        word: Mot inconnu à corriger
        dictionary: Ensemble des mots valides
        max_suggestions: Nombre maximum de suggestions

    Returns:
        Liste triée des meilleures suggestions (distance croissante)
    """
    word_lower = word.lower()
    scored = []

    for dict_word in dictionary:
        dist = levenshtein_distance(word_lower, dict_word)
        scored.append((dist, dict_word))

    scored.sort(key=lambda x: (x[0], x[1]))
    return [w for _, w in scored[:max_suggestions]]


def get_suggestions_prefsuff(word: str, dictionary: set[str], max_suggestions: int = 5) -> list[str]:
    """
    Propose des corrections par score prefsuff (préfixe/suffixe commun).

    Args:
        word: Mot inconnu à corriger
        dictionary: Ensemble des mots valides
        max_suggestions: Nombre maximum de suggestions

    Returns:
        Liste triée des meilleures suggestions (score décroissant)
    """
    word_lower = word.lower()
    scored = []

    for dict_word in dictionary:
        score = prefsuff_score(word_lower, dict_word)
        scored.append((score, dict_word))

    # Tri décroissant par score, puis alphabétique pour égalité
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [w for _, w in scored[:max_suggestions]]


def get_suggestions(word: str, dictionary: set[str], technique: str, max_suggestions: int = 5) -> list[str]:
    """
    Dispatcher pour les techniques de correction.

    Args:
        word: Mot à corriger
        dictionary: Dictionnaire de la langue
        technique: 'levenshtein' ou 'prefsuff'
        max_suggestions: Nombre maximum de propositions

    Returns:
        Liste de suggestions
    """
    if technique == "levenshtein":
        return get_suggestions_levenshtein(word, dictionary, max_suggestions)
    elif technique == "prefsuff":
        return get_suggestions_prefsuff(word, dictionary, max_suggestions)
    else:
        raise ValueError(f"Technique inconnue : {technique}. Utilisez 'levenshtein' ou 'prefsuff'.")
