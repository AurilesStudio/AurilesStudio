# Installation — 10 minutes

## 1. Créer le dépôt spécial

Sur GitHub : **New repository** → nom **exactement** `auriles`
(même nom que ton pseudo — c'est ce qui en fait un dépôt de profil ;
ton projet « Auriles Studio » garde son propre nom, aucun conflit).
Coche « Public », n'ajoute pas de README.

## 2. Pousser les fichiers

```bash
cd auriles                 # le dossier que je t'ai livré
git init -b main
git add .
git commit -m "feat: carte de profil animée"
git remote add origin git@github.com:auriles/auriles.git
git push -u origin main
```

## 3. Créer le token

GitHub → **Settings** → *Developer settings* → *Personal access tokens* →
**Tokens (classic)** → *Generate new token (classic)*

- Note : `profile-card`
- Expiration : *No expiration* (ou 1 an, à renouveler)
- Scopes à cocher : **`repo`** et **`read:user`**

Copie le token.

## 4. Enregistrer le token dans le dépôt

Dépôt `auriles` → **Settings** → *Secrets and variables* → *Actions* →
**New repository secret**

- Name : `ACCESS_TOKEN`
- Secret : le token copié

## 5. Lancer la première génération

Onglet **Actions** → *Générer la carte de profil* → **Run workflow**.

Compte 1 à 5 minutes (le calcul des lignes de code parcourt tout ton
historique de commits ; les runs suivants sont beaucoup plus rapides grâce
au cache). Va ensuite sur `github.com/auriles` : la carte est là.

Ensuite ça tourne tout seul chaque nuit à 03h17 UTC.

---

# Personnaliser

Tout est dans **`config.py`** — aucune autre ligne à toucher :

| Réglage | Effet |
|---|---|
| `DISPLAY_NAME`, `TITLE` | nom dans le prompt et titre de la fenêtre |
| `LOCATION`, `OS_LABEL`, `EDITOR` | lignes du haut |
| `FOCUS`, `TOOLS` | tes spécialités et tes outils |
| `USE_REAL_LANGUAGES` | `True` = langages calculés depuis tes dépôts, `False` = liste figée |
| `LANGUAGES_FALLBACK` | la liste figée (utile tant que tes dépôts sont vides) |
| `THEMES` | toutes les couleurs, clair et sombre |
| `BRAND_LANGUAGE_COLORS` | `True` : la barre de langages suit la rampe de la marque. `False` : couleurs officielles GitHub |
| `FONT_MONO`, `FONT_SERIF` | les piles de polices, identiques à celles du site |

Les couleurs du thème sombre sont les tokens d'auriles.studio, repris tels
quels : `--canvas #06080d`, `--paper #0c111b`, `--accent #5e8fdc`,
`--accent-text #88aae6`, `--text-primary #eaf1fb`, `--text-muted #97a3b7`,
`--border #fffdfa1f`, `--radius 6px`, plus `#5fb389` et `#dd7a6f` pour les
lignes ajoutées / supprimées. Le thème clair en est la transposition — le site
n'ayant pas de mode clair, il est dérivé de la même échelle de bleus.

Après modification :

```bash
python3 today.py --demo    # aperçu local, sans réseau ni token
open dark_mode.svg
```

## Changer le portrait ASCII

`ascii_portrait.txt` : 36 colonnes × 28 lignes de texte brut. Tu peux
l'éditer à la main, ou le régénérer depuis une autre photo avec
`tools/photo_to_ascii.py` :

```bash
pip install pillow
python3 tools/photo_to_ascii.py ma_photo.jpg > ascii_portrait.txt
```

Le script recadre au centre ; si le cadrage ne te plaît pas, ajuste les
valeurs `CROP` en haut du fichier.

> Le `ascii_portrait.txt` livré est la sortie de ce script sur ta photo, avec
> les 7 premières lignes légèrement nettoyées à la main : le poster
> « BUILD SOLVE REPEAT » de l'arrière-plan créait du bruit au-dessus du crâne.

## La police

La carte demande `JetBrains Mono` — la même que le site — puis retombe sur la
monospace du système si le visiteur ne l'a pas installée. Comme GitHub sert le
SVG en image, aucune police ne peut être chargée depuis le réseau : la seule
façon de garantir le rendu chez tout le monde est de l'embarquer dans le
fichier.

Pour ça, copie le `.woff2` de JetBrains Mono dans le dépôt :

```
fonts/JetBrainsMono.woff2
```

`today.py` le détecte tout seul et l'inline en base64 dans les deux SVG au
prochain run (ça ajoute ~25 ko par fichier). Tu peux récupérer le fichier
depuis le build de ton site (`.next/static/media/*.woff2`) ou depuis
jetbrains.com/lp/mono. Sans ce fichier, tout fonctionne — c'est juste la
police système qui prend le relais.

Le titre de la fenêtre utilise `Spectral`, avec Georgia en secours : ce sont
les mêmes déclarations que `--font-serif` sur le site.

## Régler le rythme de l'animation

Dans `svg_builder.py`, section *Timings* :

```python
T_ASCII_START = 0.45   # début du dessin du portrait
T_ASCII_STEP  = 0.045  # décalage entre deux lignes du portrait
T_INFO_START  = 1.35   # début de la frappe à droite
T_INFO_STEP   = 0.20   # décalage entre deux lignes de texte
T_LINE_DUR    = 0.42   # durée de frappe d'une ligne
```

L'animation dure ~5 s et se rejoue à chaque chargement de la page (GitHub
met l'image en cache mais l'animation CSS repart de zéro côté navigateur).

---

# Notes

- Les commits privés ne sont comptés que si ton profil autorise
  « Include private contributions on my profile »
  (Settings → Public profile → Contributions).
- Le compteur de lignes de code ne compte que les commits dont **tu** es
  l'auteur, sur la branche par défaut de chaque dépôt non-fork.
- Le fichier `cache/loc.json` évite de tout recalculer : ne le supprime pas.
- Si l'action échoue avec `403`, c'est presque toujours le token :
  vérifie les scopes `repo` + `read:user`.
