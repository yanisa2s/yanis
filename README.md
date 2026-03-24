## Documentation individuelle

### Membre 1 — Nadir OUCHALLAL
Tâches réalisées :
- chargement des dictionnaires (`dictionary_manager.py`) ;
- détection automatique de langue ;
- participation aux tests de validation ;
- corrections pour améliorer la conformité du projet avec le sujet.

Difficultés rencontrées :
- gestion des cas où aucun mot du texte n’est reconnu ;
- stabilisation de la détection automatique en cas d’égalité ;
- vérification de la conformité entre les consignes du sujet et l’implémentation réelle.

### Membre 2 — Yanis ASSEF
Tâches réalisées :
- implémentation des algorithmes de correction dans `spell_corrector.py` ;
- intégration avec le serveur UDP (`udp_server.py`) ;
- réglage du nombre maximal de suggestions ;
- participation aux tests du correcteur.

Difficultés rencontrées :
- implémentation de Levenshtein sans bibliothèque externe ;
- tri correct des suggestions selon la technique choisie ;
- gestion propre des réponses UDP selon les différents cas (`OK`, `KO`, erreurs).

### Travail commun
Travail réalisé ensemble :
- conception générale de l’architecture du projet ;
- mise en place du serveur HTTP (`http_server.py`) ;
- création des templates Jinja2 ;
- mise en place de l’API `/spellcheck` ;
- développement du client CLI (`spellcheck_client.py`) ;
- rédaction, relecture et amélioration de la documentation ;
- tests finaux du projet et validation de la conformité au sujet.