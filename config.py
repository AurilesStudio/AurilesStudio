# -*- coding: utf-8 -*-
"""
Tout ce que tu peux modifier sans toucher au reste du code.
"""

# --- Identite -------------------------------------------------------------
USERNAME = "AurilesStudio"           # ton pseudo GitHub
DISPLAY_NAME = "Auriles"             # nom affiche dans le prompt
TITLE = ""                           # vide = deduit du compte (rename-proof)
LOCATION = "Paris, FR"
OS_LABEL = "macOS"
EDITOR = "VS Code + Claude Code"

# Date de creation du compte GitHub (fallback si l'API n'est pas joignable)
FALLBACK_CREATED_AT = "2015-03-01T00:00:00Z"

# --- Lignes libres de la carte --------------------------------------------
# (label, valeur) — le label est complete par des points comme dans neofetch
FOCUS = "IA / Data  -  Automatisation  -  Web"
TOOLS = "n8n, Airtable, Notion, Docker"

# --- Barre de langages ----------------------------------------------------
# Utilisee telle quelle si USE_REAL_LANGUAGES = False,
# sinon calculee depuis tes depots et seulement utilisee en secours.
USE_REAL_LANGUAGES = True
LANGUAGES_FALLBACK = [
    ("TypeScript", 34.0, "#5e8fdc"),
    ("Python",     29.0, "#8aaadf"),
    ("JavaScript", 18.0, "#e2b45e"),
    ("HTML/CSS",    9.0, "#dd7a6f"),
    ("SQL",         6.0, "#b8851f"),
    ("Autres",      4.0, "#46536a"),
]

# True  : la barre de langages utilise la rampe de la marque (recommande,
#         la carte reste coherente avec le site).
# False : chaque langage garde sa couleur officielle GitHub.
BRAND_LANGUAGE_COLORS = True
BRAND_RAMP = ["#5e8fdc", "#8aaadf", "#b7ccec", "#e2b45e", "#dd7a6f", "#46536a"]

# Couleur associee a un langage (le reste tombe sur la palette de secours)
LANGUAGE_COLORS = {
    "TypeScript": "#3178c6", "Python": "#4b8bbe", "JavaScript": "#f0d84a",
    "HTML": "#e56c46", "CSS": "#8a63d2", "SCSS": "#c6538c", "Shell": "#89e051",
    "Go": "#00ADD8", "Rust": "#dea584", "Java": "#b07219", "PHP": "#8993be",
    "Ruby": "#701516", "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Vue": "#41b883",
    "Svelte": "#ff3e00", "Jupyter Notebook": "#DA5B0B", "Dockerfile": "#384d54",
    "Makefile": "#427819", "Lua": "#000080", "R": "#198CE7", "SQL": "#f2a541",
}
PALETTE_FALLBACK = ["#5e8fdc", "#8aaadf", "#b7ccec", "#e2b45e", "#dd7a6f", "#46536a"]

# --- Animation ------------------------------------------------------------
# "loop"    : la carte est lisible immediatement, puis s'efface et se retape
#             toutes les LOOP_PERIOD secondes. Seul mode qui reste lisible
#             dans les navigateurs qui figent les images animees (Chrome 151
#             le fait : il n'affiche que l'image du temps zero).
# "ambient" : lisible immediatement, seuls le curseur et la scanline bougent.
# "intro"   : retape une fois au chargement. Plus joli la ou ca marche, mais
#             carte BLANCHE la ou les animations sont figees.
ANIMATION = "loop"
LOOP_PERIOD = 14.0          # secondes entre deux retapes

# --- Typographie ----------------------------------------------------------
# Memes declarations que le site (--font-mono / --font-serif).
# JetBrains Mono ne peut pas etre garantie chez tous les visiteurs de GitHub :
# depose fonts/JetBrainsMono.woff2 dans le depot et today.py l'embarquera
# automatiquement dans le SVG (voir SETUP.md).
FONT_MONO = ("'JetBrains Mono','JetBrains Mono NL',ui-monospace,SFMono-Regular,"
             "'SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace")
FONT_SERIF = "'Spectral',Georgia,'Times New Roman',serif"
EMBED_FONT = "fonts/JetBrainsMono.woff2"   # optionnel, ignore si absent

# --- Themes ---------------------------------------------------------------
# Tokens repris tels quels du design system d'auriles.studio :
#   canvas #06080d · paper #0c111b · night-100 #131a28
#   ink #eaf1fb · secondary #bfc8d6 · muted #97a3b7 · faint #6e7c93
#   accent #5e8fdc · accent-text #88aae6 · accent-active #93b6ec
#   lignes #fffdfa0f / #fffdfa1f · ok #5fb389 · rose #dd7a6f · radius 6px
THEMES = {
    "dark": dict(
        bg="#06080d", chrome="#0c111b", border="#fffdfa1f", grid="#04050a",
        text="#eaf1fb", value="#bfc8d6", dim="#97a3b7", faint="#6e7c93",
        accent="#88aae6", accent2="#5e8fdc",
        ascii_top="#b7ccec", ascii_bottom="#5783ce",
        ok="#5fb389", danger="#dd7a6f",
        dot1="#dd7a6f", dot2="#e2b45e", dot3="#5fb389",
        rule="#fffdfa1f", divider="#fffdfa0f", glow=0.09, radius=6,
    ),
    "light": dict(
        bg="#ffffff", chrome="#f6f8fc", border="#06080d1f", grid="#f2efe9",
        text="#06080d", value="#1b2434", dim="#46536a", faint="#6e7c93",
        accent="#284f96", accent2="#2f5fb3",
        ascii_top="#3f74c4", ascii_bottom="#1b3159",
        ok="#2f8c5f", danger="#b8503f",
        dot1="#dd7a6f", dot2="#b8851f", dot3="#2f8c5f",
        rule="#06080d1a", divider="#06080d0f", glow=0.05, radius=6,
    ),
}
