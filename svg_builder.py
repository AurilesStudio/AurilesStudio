# -*- coding: utf-8 -*-
"""
Construit la carte SVG animee (style terminal / neofetch).

Le chassis de la fenetre (cadre, barre de titre, pastilles, separateur) est
dessine hors animation : il est toujours la. Seul le contenu — portrait ASCII
et colonne de droite — est anime, selon config.ANIMATION :

    "intro"   joue une fois a l'arrivee sur la page, puis se fige (defaut)
    "loop"    lisible d'emblee, s'efface et se retape toutes les N secondes
    "ambient" lisible d'emblee, seuls le curseur et la scanline bougent

Un visiteur ayant active "reduire les animations" voit toujours la carte
complete et immobile.
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

# --- Chorégraphie (secondes, relatives au debut de la frappe) -------------
T_ASCII_START = 0.35
T_ASCII_STEP = 0.045
T_INFO_START = 1.20
T_INFO_STEP = 0.20
T_LINE_DUR = 0.42

EASE_OUT = "cubic-bezier(.16,1,.3,1)"

HIDDEN = {"fade": "opacity:0;transform:translateY(3px)",
          "scale": "transform:scaleX(0)"}
SHOWN = {"fade": "opacity:1;transform:translateY(0)",
         "scale": "transform:scaleX(1)"}


def _e(s):
    return escape(str(s))


def _span(cls, text):
    return '<tspan class="%s">%s</tspan>' % (cls, _e(text))


def _label(text):
    """'OS' -> 'OS...........:' aligne comme neofetch."""
    return text + "." * max(1, LABEL_W - len(text)) + ":"


class Card:
    def __init__(self, theme_name, data):
        self.tn = theme_name
        self.c = config.THEMES[theme_name]
        self.d = data
        self.defs = []
        self.css = []
        self.anims = []          # (selecteur, kind, start, duree, easing)
        self.body = []
        self._uid = 0

    def uid(self, p="i"):
        self._uid += 1
        return "%s%s%d" % (p, self.tn[0], self._uid)

    def anim(self, sel, kind, start, dur, easing):
        self.anims.append((sel, kind, start, dur, easing))

    # ---------------------------------------------------------------- lignes
    def typed_line(self, y, spans, delay, chars):
        """Une ligne revelee de gauche a droite, facon frappe clavier."""
        cid = self.uid("c")
        self.defs.append(
            '<clipPath id="{id}" clipPathUnits="userSpaceOnUse">'
            '<rect class="rev" id="r{id}" x="{x}" y="{y}" width="{w}" height="{h}"/>'
            '</clipPath>'.format(id=cid, x=INFO_X - 2, y=y - INFO_FS, w=INFO_W + 4,
                                 h=INFO_LH)
        )
        self.anim("#r" + cid, "scale", delay, T_LINE_DUR,
                  "steps(%d,end)" % max(6, chars))
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
            self.anim(".a%d" % i, "fade", T_ASCII_START + i * T_ASCII_STEP,
                      0.5, "ease-out")
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

        for lab, val in [
            ("OS", [V(config.OS_LABEL), DIM("  ·  "), V(config.LOCATION)]),
            ("Uptime", [A(d["uptime"])]),
            ("Focus", [V(config.FOCUS)]),
            ("Editor", [V(config.EDITOR)]),
            ("Tools", [V(config.TOOLS)]),
        ]:
            y += INFO_LH
            t += T_INFO_STEP
            self.kv(y, lab, val, t)

        y += INFO_LH * 1.05
        t += T_INFO_STEP
        self.rule(y, t)

        for lab, val in [
            ("Repos", [A(d["repos"]), DIM("  {"), V("public "), A(d["public"]),
                       DIM(" | "), V("privé "), A(d["private"]), DIM("}")]),
            ("Commits", [A(d["commits"]), DIM("   sur "), V(d["years_label"])]),
            ("Stars", [A(d["stars"]), DIM("      Followers  "), A(d["followers"])]),
            ("Code", [A(d["loc_total"]), DIM(" lignes  "),
                      ("plus", "++" + str(d["loc_add"])), DIM(" / "),
                      ("minus", "--" + str(d["loc_del"]))]),
        ]:
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
            self.legend_row(y, langs[k:k + 3], t)
            y += 17

        # ---- separateur vertical (toujours visible : c'est le chassis)
        self.body.append(
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s"/>'
            % (INFO_X - 26, BAR_H + 22, INFO_X - 26, CARD_H - 22, c["divider"]))

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
        self.anim("." + pid, "fade", t, 0.4, "ease-out")

        # ---- pied de carte
        fid = self.uid("f")
        self.body.append(
            '<text class="foot %s" x="%s" y="%s">%s</text>'
            % (fid, INFO_X, CARD_H - 24, _e(d["footer"])))
        self.css.append(".foot{font-size:10px;fill:%s;letter-spacing:.3px}"
                        % c["faint"])
        self.anim("." + fid, "fade", t + 0.25, 0.5, "ease-out")

        return self.render()

    def lang_bar(self, y, delay):
        langs = self.d["languages"]
        x = INFO_X
        total = sum(p for _, p, _ in langs) or 100.0
        clip = self.uid("lb")
        self.defs.append(
            '<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="9" rx="%s"/>'
            '</clipPath>' % (clip, INFO_X, y, INFO_W, self.c["radius"]))
        segs = []
        for i, (name, pct, col) in enumerate(langs):
            w = INFO_W * pct / total
            sid = self.uid("s")
            segs.append('<rect class="seg %s" x="%.2f" y="%s" width="%.2f" '
                        'height="9" fill="%s"/>' % (sid, x, y, max(w, 1.0), col))
            self.css.append(".%s{transform-box:fill-box;transform-origin:left center}"
                            % sid)
            self.anim("." + sid, "scale", delay + i * 0.09, 0.55, EASE_OUT)
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
        self.anim("." + gid, "fade", delay, 0.4, "ease-out")

    # ------------------------------------------------------- animations CSS
    def emit_anims(self):
        """
        Transforme la liste d'animations en CSS dont l'image du temps zero est
        toujours l'etat final visible.
        """
        mode = getattr(config, "ANIMATION", "loop")
        if mode == "ambient" or not self.anims:
            return

        reveal = max(s + d for _, _, s, d, _ in self.anims)

        if mode == "intro":
            # Joue une seule fois puis se fige sur la carte complete.
            # Le chassis de la fenetre (cadre, barre de titre, separateur) est
            # dessine hors animation : meme si un navigateur ne joue pas les
            # animations, on voit le terminal vide plutot que rien.
            for sel, kind, start, dur, easing in self.anims:
                self.css.append(
                    "%s{animation:kf_%s %.2fs %s %.2fs backwards}"
                    % (sel, kind, dur, easing, start))
            self.css.append("@keyframes kf_fade{from{%s}to{%s}}"
                            % (HIDDEN["fade"], SHOWN["fade"]))
            self.css.append("@keyframes kf_scale{from{%s}to{%s}}"
                            % (HIDDEN["scale"], SHOWN["scale"]))
            return

        # mode "loop" : lisible, puis effacement et retape, en boucle.
        period = max(float(getattr(config, "LOOP_PERIOD", 14.0)), reveal + 4.0)
        clear_at = period - reveal - 0.6      # instant de l'effacement
        gap = 0.25                            # ecran vide avant la retape
        snap = period * 0.002                 # effacement quasi instantane

        for i, (sel, kind, start, dur, easing) in enumerate(self.anims):
            name = "lp%s%d" % (self.tn[0], i)
            a = (clear_at + gap + start) / period * 100.0
            b = (clear_at + gap + start + dur) / period * 100.0
            k0 = clear_at / period * 100.0
            k1 = min(k0 + snap / period * 100.0, a)
            self.css.append(
                "@keyframes %s{0%%,%.3f%%{%s}%.3f%%,%.3f%%{%s}%.3f%%,100%%{%s}}"
                % (name, k0, SHOWN[kind], k1, a, HIDDEN[kind], b, SHOWN[kind]))
            self.css.append("%s{animation:%s %.2fs %s infinite}"
                            % (sel, name, period, easing))

    # ---------------------------------------------------------------- render
    def render(self):
        c = self.c
        self.emit_anims()

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
            % (glow, c["accent"], c["glow"], c["accent"])
        )
        bodyclip = self._bodyclip()

        base = """__FONTFACE__
  text{font-family:__MONO__;dominant-baseline:auto}
  .art{font-size:__AFS__px;letter-spacing:0}
  .info{font-size:__IFS__px;fill:__TEXT__}
  .lbl{fill:__DIM__}
  .dim{fill:__FAINT__}
  .val{fill:__VALUE__}
  .acc{fill:__ACC__}
  .acc2{fill:__ACC2__}
  .bold{font-weight:600;letter-spacing:.2px}
  .rule{fill:__RULE__}
  .plus{fill:__OK__}
  .minus{fill:__DANGER__}
  .leg{font-size:10.5px;fill:__VALUE__}
  .title{font-family:__SERIF__;font-size:13px;fill:__DIM__;letter-spacing:.2px}
  .rev{transform-box:fill-box;transform-origin:left center}
  .caret{fill:__ACC__;animation:blink 1.05s steps(1) infinite}
  .artgrp{animation:crt 4.2s ease-in-out infinite}
  .scan{animation:scan 7s linear infinite}
  @keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
  @keyframes crt{0%,100%{opacity:.97}45%{opacity:1}70%{opacity:.94}}
  @keyframes scan{0%{transform:translateY(__TOP__px)}100%{transform:translateY(__BOT__px)}}
  @media (prefers-reduced-motion:reduce){*{animation:none !important}}
"""
        for k, v in [("__FONTFACE__", self.d.get("font_face", "")),
                     ("__MONO__", MONO), ("__SERIF__", SERIF),
                     ("__AFS__", "%.1f" % ASCII_FS), ("__IFS__", "%.1f" % INFO_FS),
                     ("__TEXT__", c["text"]), ("__DIM__", c["dim"]),
                     ("__FAINT__", c["faint"]), ("__VALUE__", c["value"]),
                     ("__ACC__", c["accent"]), ("__ACC2__", c["accent2"]),
                     ("__RULE__", c["rule"]), ("__OK__", c["ok"]),
                     ("__DANGER__", c["danger"]),
                     ("__TOP__", str(BAR_H)), ("__BOT__", str(CARD_H))]:
            base = base.replace(k, v)
        css = base + "  " + "\n  ".join(self.css)

        dots = "".join(
            '<circle cx="%d" cy="17" r="4.5" fill="%s"/>' % (24 + i * 17, col)
            for i, col in enumerate([c["dot1"], c["dot2"], c["dot3"]])
        )
        r = c["radius"]
        chrome_path = ('M0.5 %s a%s %s 0 0 1 %s -%s h%s a%s %s 0 0 1 %s %s V%s H0.5 Z'
                       % (r + 0.5, r, r, r, r, CARD_W - 1 - 2 * r, r, r, r, r, BAR_H))

        return """<svg xmlns="http://www.w3.org/2000/svg" width="%(W)d" height="%(H)d" \
viewBox="0 0 %(W)d %(H)d" role="img" aria-label="%(alt)s">
<title>%(alt)s</title>
<defs>
%(defs)s
</defs>
<style>%(css)s</style>
<g>
  <rect x="0.5" y="0.5" width="%(W1)s" height="%(H1)s" rx="%(r)s" fill="%(bg)s" stroke="%(border)s"/>
  <rect x="0.5" y="0.5" width="%(W1)s" height="%(H1)s" rx="%(r)s" fill="url(#%(glow)s)"/>
  <path d="%(chrome_path)s" fill="%(chrome)s"/>
  <line x1="0.5" y1="%(bar)s" x2="%(W1)s" y2="%(bar)s" stroke="%(border)s"/>
  %(dots)s
  <text class="title" x="%(cx)s" y="21" text-anchor="middle">%(title)s</text>
  <g clip-path="url(#%(bodyclip)s)">
    <rect class="scan" x="0" y="-52" width="%(W)d" height="52" fill="url(#%(scan)s)" opacity="0.07"/>
  </g>
%(body)s
</g>
</svg>
""" % dict(W=CARD_W, H=CARD_H, W1=CARD_W - 1, H1=CARD_H - 1, bar=BAR_H,
           bg=c["bg"], border=c["border"], chrome=c["chrome"], r=r,
           chrome_path=chrome_path, dots=dots, cx=CARD_W / 2,
           title=_e(config.TITLE + "  —  ~/profile"),
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
