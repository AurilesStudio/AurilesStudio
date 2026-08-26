#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertit une photo en portrait ASCII pour la carte de profil.

    pip install pillow
    python3 tools/photo_to_ascii.py ma_photo.jpg > ascii_portrait.txt

Ajuste CROP si le cadrage ne te convient pas : (gauche, haut, droite, bas)
en fraction de l'image (0 = bord gauche/haut, 1 = bord droit/bas).
"""
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

COLS = 36           # largeur en caracteres (doit rester coherent avec le SVG)
ASPECT = 0.47       # hauteur/largeur d'un caractere monospace
RAMP = " .:-=+*#%@"  # du plus sombre au plus clair
CROP = (0.2911, 0.1156, 0.7057, 0.8094)
CONTRAST = 2.2
BLUR = 1.4
VIGNETTE = True     # estompe l'arriere-plan autour du visage


def main(path):
    im = Image.open(path).convert("L")
    W, H = im.size
    box = (int(CROP[0] * W), int(CROP[1] * H), int(CROP[2] * W), int(CROP[3] * H))
    img = im.crop(box)

    if BLUR:
        img = img.filter(ImageFilter.GaussianBlur(BLUR))
    img = img.filter(ImageFilter.UnsharpMask(radius=6, percent=90, threshold=3))
    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(CONTRAST)

    if VIGNETTE:
        w, h = img.size
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).ellipse(
            [w * 0.52 - w * 0.58, h * 0.48 - h * 0.62,
             w * 0.52 + w * 0.58, h * 0.48 + h * 0.62], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(w * 0.08))
        img = Image.composite(img, Image.new("L", (w, h), 0), mask)

    rows = max(1, int(COLS * img.height / img.width * ASPECT))
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = img.load()
    n = len(RAMP) - 1
    for y in range(rows):
        line = "".join(RAMP[int(px[x, y] / 255 * n + 0.5)] for x in range(COLS))
        print(line.rstrip())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1])
