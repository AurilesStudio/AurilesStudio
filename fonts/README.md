# Polices

Dépose ici `JetBrainsMono.woff2` (variable, poids 100–800) pour que la carte
utilise exactement la même police que le site chez tous les visiteurs de
GitHub. `today.py` détecte le fichier et l'inline en base64 dans les deux SVG.

Sans ce fichier, la carte demande `JetBrains Mono` puis retombe sur la
monospace du système : tout fonctionne, seul le dessin des glyphes change.

Sources possibles :
- le build de ton site : `.next/static/media/*.woff2`
- https://www.jetbrains.com/lp/mono/ (licence OFL)
