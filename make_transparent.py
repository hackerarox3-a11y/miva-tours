"""Detourage du logo.jpg (fond noir + bruit colore) -> logo.png transparent.

On ne conserve QUE les pixels appartenant aux familles de couleurs du logo :
  - bleu-vert (teal) : vert et bleu >> rouge
  - orange           : rouge > vert > bleu
  - marine/gris      : peu sature, luminosite moyenne
Tout le reste (bruit magenta/cyan, fond noir) devient transparent.

Usage : python make_transparent.py   (depuis la racine du projet)
"""
from PIL import Image, ImageFilter

SRC = "logo.jpg"
DST = "logo.png"

im = Image.open(SRC).convert("RGB")
px = im.load()
w, h = im.size
out = Image.new("RGBA", (w, h))
op = out.load()

kept = 0
for y in range(h):
    for x in range(w):
        r, g, b = px[x, y]
        mx, mn = max(r, g, b), min(r, g, b)
        alpha = 0
        # --- Teal : g et b dominent nettement r, canaux dans la plage du logo
        if g > r + 30 and b > r + 20 and 90 < g < 200 and 110 < b < 205 and r < 90:
            t = min(1.0, b / 160.0)          # melange avec le fond noir
            alpha = max(60, min(255, int(t * 255 * 1.15)))
            if alpha == 255:
                r, g, b = min(255, int(r / t)), min(255, int(g / t)), min(255, int(b / t))
        # --- Orange : r > g > b
        elif r > g > b and r > 150 and 60 < g < 190 and b < 110:
            t = min(1.0, r / 235.0)
            alpha = max(60, min(255, int(t * 255 * 1.15)))
            if alpha == 255:
                r, g, b = min(255, int(r / t)), min(255, int(g / t)), min(255, int(b / t))
        # --- Marine / gris (texte et traits fins)
        elif 40 < mx < 160 and (mx - mn) < 38:
            t = min(1.0, mx / 85.0)
            alpha = max(0, min(255, int(t * 255)))
            if alpha > 0:
                r, g, b = min(255, int(r / t)), min(255, int(g / t)), min(255, int(b / t))
        if alpha:
            kept += 1
        op[x, y] = (r, g, b, alpha)

# Desparasitage de la couche alpha (filtre median)
alpha_clean = out.getchannel("A").filter(ImageFilter.MedianFilter(3))
out.putalpha(alpha_clean)

# Recadrage : on retire le slogan du bas (affiche en texte sur le site)
CROP_BOTTOM = 336
out = out.crop((0, 0, w, CROP_BOTTOM))
w, h = out.size

# Suppression des ilots isoles (restes de bruit) : composantes < 12 px
apx = out.load()
seen = [[False] * w for _ in range(h)]
removed = 0
for y0 in range(h):
    for x0 in range(w):
        if not seen[y0][x0] and apx[x0, y0][3] > 0:
            stack = [(x0, y0)]
            seen[y0][x0] = True
            comp = []
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and apx[nx, ny][3] > 0:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(comp) < 12:
                for cx, cy in comp:
                    r, g, b, _ = apx[cx, cy]
                    apx[cx, cy] = (r, g, b, 0)
                removed += len(comp)

out.save(DST)
print(f"OK: {DST} {out.size} - {kept} pixels conserves, {removed} parasites supprimes")
