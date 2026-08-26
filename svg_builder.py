# -*- coding: utf-8 -*-
"""
Construit la carte SVG animee (style terminal / neofetch) a partir des donnees
recuperees par today.py. Aucune dependance externe.
"""
from xml.sax.saxutils import escape

import config

# --- Geometrie ------------------------------------------------------------
CARD_W, CARD_H = 900, 476
BAR_H = 34                      # hauteur de la barre de titre

ASCII_X = 26
ASCII_Y = 66
ASCII_FS = 12.0
ASCII_CW = ASCII_FS * 0.6       # largeur d'un caractere monospace
ASCII_LH = 13.6

INFO_X = 316
INFO_Y = 68
INFO_FS = 12.5
INFO_CW = INFO_FS * 0.6
INFO_LH = 20.0
INFO_W = CARD_W - INFO_X - 26

MONO = config.FONT_MONO
SERIF = config.FONT_SERIF

LABEL_W = 13                    # largeur de la colonne label (en caracteres)

# --- Timings (secondes) ---------------------------------------------------
T_BOOT = 0.25                   # apparition du cadre
T_ASCII_START = 0.45
T_ASCII_STEP = 0.045
T_INFO_START = 1.35
T_INFO_STEP = 0.20
T_LINE_DUR = 0.42


def _e(s):
    return escape(str(s))


def _span(cls, text):
    return '<tspan class="%s">%s</tspan>' % (cls, _e(text))


def _label(text):
    """auriles -> 'OS...........:' aligne comme neofetch."""
    return text + "." * max(1, LABEL_W - len(text)) + ":"


class Card:
    def __init__(self, theme_name, data):
        self.tn = theme_name
        self.c = config.THEMES[theme_name]
        self.d = data
        self.defs = []
        self.css = []
        self.body = []
        self._uid = 0

    def uid(self, p="i"):
        self._uid += 1
        return "%s%s%d" % (p, self.tn[0], self._uid)

    # ---------------------------------------------------------------- lignes
    def typed_line(self, y, spans, delay, chars):
        """Une ligne de texte revelee de gauche a droite, facon frappe clavier."""
        cid = self.uid("c")
        self.defs.append(
            '<clipPath id="{id}" clipPathUnits="userSpaceOnUse">'
            '<rect class="rev" id="r{id}" x="{x}" y="{y}" width="{w}" height="{h}"/>'
            '</clipPath>'.format(id=cid, x=INFO_X - 2, y=y - INFO_FS, w=INFO_W + 4,
                                 h=INFO_LH)
        )
        self.css.append(
            "#r%s{animation:type %.2fs steps(%d,end) %.2fs backwards}"
            % (cid, T_LINE_DUR, max(6, chars), delay)
        )
        self.body.append(
            '<g clip-path="url(#%s)"><text class="info" x="%s" y="%s" '
            'xml:space="preserve">%s</text></g>' % (cid, INFO_X, y, "".join(spans))
        )

    def kv(self, y, label, parts, delay):
        parts = [("lbl", _label(label) + " ")] + list(parts)
        self.typed_line(y, [_span(c, t) for c, t in parts], delay,
                        sum(len(t) for _, t in parts))

    def rule(self, y, delay):
        n = int(INFO_W / INFO_CW)
        self.typed_line(y, [_span("rule", "─" * n)], delay, n)

    # ------------------------------------------------------------------ SVG
    def build(self):
        c, d = self.c, self.d
        A = lambda s: ("acc", str(s))
        V = lambda s: ("val", str(s))
        DIM = lambda s: ("dim", str(s))

        # ---- portrait ASCII
        rows = d["ascii"]
        gid = self.uid("g")
        self.defs.append(
            '<linearGradient id="%s" gradientUnits="userSpaceOnUse" '
            'x1="%s" y1="%s" x2="%s" y2="%s">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
            '</linearGradient>' % (gid, ASCII_X, ASCII_Y - ASCII_LH,
                                   ASCII_X + 36 * ASCII_CW * 0.5,
                                   ASCII_Y + len(rows) * ASCII_LH,
                                   c["ascii_top"], c["ascii_bottom"])
        )
        art = []
        for i, row in enumerate(rows):
            if not row.strip():
                continue
            y = ASCII_Y + i * ASCII_LH
            art.append(
                '<text class="art a%d" x="%s" y="%.1f" textLength="%.2f" '
                'lengthAdjust="spacingAndGlyphs" xml:space="preserve">%s</text>'
                % (i, ASCII_X, y, ASCII_CW * len(row), _e(row))
            )
            self.css.append(
                ".a%d{animation:fadein .5s ease-out %.2fs backwards}"
                % (i, T_ASCII_START + i * T_ASCII_STEP)
            )
        self.body.append('<g fill="url(#%s)" class="artgrp">%s</g>'
                         % (gid, "".join(art)))

        # ---- colonne de droite
        y = INFO_Y
        t = T_INFO_START
        self.typed_line(y, [_span("acc bold", config.TITLE)], t,
                        len(config.TITLE))
        y += INFO_LH * 0.9
        t += T_INFO_STEP
        self.rule(y, t)

        rows_kv = [
            ("OS", [V(config.OS_LABEL), DIM("  ·  "), V(config.LOCATION)]),
            ("Uptime", [A(d["uptime"])]),
            ("Focus", [V(config.FOCUS)]),
            ("Editor", [V(config.EDITOR)]),
            ("Tools", [V(config.TOOLS)]),
        ]
        for lab, val in rows_kv:
            y += INFO_LH
            t += T_INFO_STEP
            self.kv(y, lab, val, t)

        y += INFO_LH * 1.05
        t += T_INFO_STEP
        self.rule(y, t)

        stats = [
            ("Repos", [A(d["repos"]), DIM("  {"), V("public "), A(d["public"]),
                       DIM(" | "), V("privé "), A(d["private"]), DIM("}")]),
            ("Commits", [A(d["commits"]), DIM("   sur "), V(d["years_label"])]),
            ("Stars", [A(d["stars"]), DIM("      Followers  "), A(d["followers"])]),
            ("Code", [A(d["loc_total"]), DIM(" lignes  "),
                      ("plus", "++" + str(d["loc_add"])), DIM(" / "),
                      ("minus", "--" + str(d["loc_del"]))]),
        ]
        for lab, val in stats:
            y += INFO_LH
            t += T_INFO_STEP
            self.kv(y, lab, val, t)

        y += INFO_LH * 1.05
        t += T_INFO_STEP
        self.rule(y, t)

        # ---- barre de langages
        y += INFO_LH * 0.95
        t += T_INFO_STEP
        self.lang_bar(y, t)

        # ---- legende
        langs = d["languages"]
        y += 26
        for k in range(0, len(langs), 3):
            t += 0.12
            chunk = langs[k:k + 3]
            self.legend_row(y, chunk, t)
            y += 17

        # ---- separateur vertical entre les deux colonnes
        self.body.append(
            '<line class="divider" x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>'
            % (INFO_X - 26, BAR_H + 22, INFO_X - 26, CARD_H - 22, c["divider"]))
        self.css.append(".divider{animation:fadein .6s ease-out %.2fs backwards}"
                        % (T_INFO_START - 0.2))

        # ---- prompt clignotant
        y += 12
        t += 0.2
        pid = self.uid("p")
        self.body.append(
            '<g class="%s"><text class="info" x="%s" y="%s" xml:space="preserve">'
            '<tspan class="acc2">%s</tspan><tspan class="dim"> $ </tspan>'
            '<tspan class="val">%s</tspan></text>'
            '<rect class="caret" x="%.1f" y="%.1f" width="%.1f" height="%.1f"/></g>'
            % (pid, INFO_X, y, _e(config.DISPLAY_NAME.lower()), _e(d["tagline"]),
               INFO_X + (len(config.DISPLAY_NAME) + 3 + len(d["tagline"]) + 0.4) * INFO_CW,
               y - INFO_FS + 1.5, INFO_CW * 0.9, INFO_FS + 1)
        )
        self.css.append(".%s{animation:fadein .4s ease-out %.2fs backwards}" % (pid, t))

        # ---- pied de carte
        fid = self.uid("f")
        self.body.append(
            '<text class="foot %s" x="%s" y="%s">%s</text>'
            % (fid, INFO_X, CARD_H - 24, _e(d["footer"])))
        self.css.append(".foot{font-size:10px;fill:%s;letter-spacing:.3px}"
                        % c["faint"])
        self.css.append(".%s{animation:fadein .5s ease-out %.2fs backwards}"
                        % (fid, t + 0.25))

        return self.render()

    def lang_bar(self, y, delay):
        langs = self.d["languages"]
        x = INFO_X
        total = sum(p for _, p, _ in langs) or 100.0
        clip = self.uid("lb")
        self.defs.append(
            '<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="9" rx="4.5"/>'
            '</clipPath>' % (clip, INFO_X, y, INFO_W)
        )
        segs = []
        for i, (name, pct, col) in enumerate(langs):
            w = INFO_W * pct / total
            sid = self.uid("s")
            segs.append('<rect class="seg %s" x="%.2f" y="%s" width="%.2f" '
                        'height="9" fill="%s"/>' % (sid, x, y, max(w, 1.0), col))
            self.css.append(".%s{transform-box:fill-box;transform-origin:left center;"
                            "animation:grow .55s cubic-bezier(.2,.9,.3,1) %.2fs backwards}"
                            % (sid, delay + i * 0.09))
            x += w
        self.body.append('<g clip-path="url(#%s)">%s</g>' % (clip, "".join(segs)))

    def legend_row(self, y, chunk, delay):
        x = INFO_X
        parts = []
        for name, pct, col in chunk:
            parts.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>'
                         % (x + 4, y - 4, col))
            parts.append('<text class="leg" x="%.1f" y="%s">%s <tspan class="dim">'
                         '%.1f%%</tspan></text>' % (x + 14, y, _e(name), pct))
            x += 14 + (len(name) + 7) * 6.6 + 14
        gid = self.uid("lg")
        self.body.append('<g class="%s">%s</g>' % (gid, "".join(parts)))
        self.css.append(".%s{animation:fadein .4s ease-out %.2fs backwards}"
                        % (gid, delay))

    # ---------------------------------------------------------------- render
    def render(self):
        c = self.c
        scan = self.uid("sc")
        self.defs.append(
            '<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="%s" stop-opacity="0"/>'
            '<stop offset="0.5" stop-color="%s" stop-opacity="0.9"/>'
            '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            % (scan, c["accent"], c["accent"], c["accent"])
        )
        glow = self.uid("gl")
        self.defs.append(
            '<radialGradient id="%s" cx="0.2" cy="0.15" r="0.9">'
            '<stop offset="0" stop-color="%s" stop-opacity="%.2f"/>'
            '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
            % (glow, c["accent"], 0.10 if self.tn == "dark" else 0.05, c["accent"])
        )

        css = """%(fontface)s
  text{font-family:%(mono)s;dominant-baseline:auto}
  .art{font-size:%(afs).1fpx;letter-spacing:0}
  .info{font-size:%(ifs).1fpx;fill:%(text)s}
  .lbl{fill:%(dim)s}
  .dim{fill:%(faint)s}
  .val{fill:%(value)s}
  .acc{fill:%(acc)s}
  .acc2{fill:%(acc2)s}
  .bold{font-weight:600;letter-spacing:.2px}
  .rule{fill:%(rule)s}
  .plus{fill:%(plus)s}
  .minus{fill:%(minus)s}
  .leg{font-size:10.5px;fill:%(value)s}
  .title{font-family:%(serif)s;font-size:13px;fill:%(dim)s;letter-spacing:.2px}
  .caret{fill:%(acc)s;animation:blink 1.05s steps(1) infinite}
  .artgrp{animation:crt 4.2s ease-in-out infinite}
  .scan{animation:scan 7s linear infinite}
  .frame{animation:boot .5s ease-out backwards}
  .chrome{animation:fadein .45s ease-out %(tb).2fs backwards}
  @keyframes type{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes fadein{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:translateY(0)}}
  @keyframes blink{0%%,49%%{opacity:1}50%%,100%%{opacity:0}}
  @keyframes crt{0%%,100%%{opacity:.97}45%%{opacity:1}70%%{opacity:.94}}
  @keyframes scan{0%%{transform:translateY(%(top)dpx)}100%%{transform:translateY(%(bot)dpx)}}
  @keyframes boot{from{opacity:0;transform:scale(.985)}to{opacity:1;transform:scale(1)}}
  .rev{transform-box:fill-box;transform-origin:left center}
  @media (prefers-reduced-motion:reduce){*{animation:none !important}}
""" % dict(mono=MONO, serif=SERIF, afs=ASCII_FS, ifs=INFO_FS,
           fontface=self.d.get("font_face", ""),
           text=c["text"], dim=c["dim"], faint=c["faint"], value=c["value"],
           acc=c["accent"], acc2=c["accent2"], rule=c["rule"],
           plus=c["ok"], minus=c["danger"],
           tb=T_BOOT, top=BAR_H, bot=CARD_H)

        bodyclip = self._bodyclip()
        css += "\n  ".join(self.css)

        dots = "".join(
            '<circle cx="%d" cy="17" r="4.5" fill="%s"/>' % (24 + i * 17, col)
            for i, col in enumerate([c["dot1"], c["dot2"], c["dot3"]])
        )

        return """<svg xmlns="http://www.w3.org/2000/svg" width="%(W)d" height="%(H)d" \
viewBox="0 0 %(W)d %(H)d" role="img" aria-label="%(alt)s">
<title>%(alt)s</title>
<defs>
%(defs)s
</defs>
<style>%(css)s</style>
<g class="frame">
  <rect x="0.5" y="0.5" width="%(W1)s" height="%(H1)s" rx="%(r)s" fill="%(bg)s" stroke="%(border)s"/>
  <rect x="0.5" y="0.5" width="%(W1)s" height="%(H1)s" rx="%(r)s" fill="url(#%(glow)s)"/>
  <g class="chrome">
    <path d="M0.5 %(r15)s a%(r)s %(r)s 0 0 1 %(r)s -%(r)s h%(inner)s a%(r)s %(r)s 0 0 1 %(r)s %(r)s V%(bar)s H0.5 Z" fill="%(chrome)s"/>
    <line x1="0.5" y1="%(bar)s" x2="%(W1)s" y2="%(bar)s" stroke="%(border)s"/>
    %(dots)s
    <text class="title" x="%(cx)s" y="21" text-anchor="middle">%(title)s</text>
  </g>
  <g clip-path="url(#%(bodyclip)s)">
    <rect class="scan" x="0" y="-52" width="%(W)d" height="52" fill="url(#%(scan)s)" opacity="0.07"/>
  </g>
%(body)s
</g>
</svg>
""" % dict(W=CARD_W, H=CARD_H, W1=CARD_W - 1, H1=CARD_H - 1, inner=CARD_W - 1 - 2 * c["radius"],
           bar=BAR_H, bg=c["bg"], border=c["border"], chrome=c["chrome"],
           r=c["radius"], r15=c["radius"] + 0.5,
           dots=dots, cx=CARD_W / 2, title=_e(config.TITLE + "  —  ~/profile"),
           defs="\n".join(self.defs), css=css, body="\n".join(self.body),
           scan=scan, glow=glow, bodyclip=bodyclip,
           alt=_e("Carte de profil GitHub de " + config.DISPLAY_NAME))

    def _bodyclip(self):
        cid = self.uid("bc")
        self.defs.append('<clipPath id="%s"><rect x="1" y="%s" width="%s" '
                         'height="%s" rx="%s"/></clipPath>'
                         % (cid, BAR_H, CARD_W - 2, CARD_H - BAR_H - 1,
                            self.c["radius"]))
        return cid


def build(theme_name, data):
    return Card(theme_name, data).build()
