#!/usr/bin/env python3
"""Génère la map du bureau virtuel Sésame (style illustration moderne, tuiles 32px)."""
import json, os, subprocess, hashlib
from PIL import Image

T = 32
W, H = 44, 30
OUT = os.path.dirname(os.path.abspath(__file__))

C = dict(
    night="#0B1220", ink="#0F1729", ink2="#16213A", blue="#2F5DFF", blue_soft="#E4EBFF",
    wall_top="#E9EDF5", wall_face="#C9D2E3", wall_edge="#9AA6BF",
    hall="#F3F1EC", hall_line="#E7E3DA",
    wood="#E8D3B5", wood_line="#DCC29F",
    lounge="#F4E2D8", lounge_line="#EAD2C4",
    call="#DDE6F7", call_line="#CFDBF2",
    exec="#2A3550", exec_line="#323F5E",
    glass="#BFD3FF", desk="#FFFFFF", desk_edge="#D6DCE8",
    plant="#3FA56B", plant2="#2E8A56", pot="#C8B79E",
    sofa="#2F5DFF", sofa2="#2448CC", amber="#F2A93B", red="#E5484D", green="#22C17A",
)

svg = []
collide = [[0] * W for _ in range(H)]

def px(t): return t * T
def rect(x, y, w, h, fill, rx=0, extra=""):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>')
def block(tx, ty, tw, th):
    for j in range(ty, ty + th):
        for i in range(tx, tx + tw):
            if 0 <= i < W and 0 <= j < H:
                collide[j][i] = 1
def text(x, y, s, size=11, fill="#0F1729", weight=600, anchor="middle", family="Inter", spacing=0):
    svg.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
               f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{spacing}">{s}</text>')

def floor(tx, ty, tw, th, base, line, kind="planks"):
    x, y, w, h = px(tx), px(ty), px(tw), px(th)
    rect(x, y, w, h, base)
    if kind == "planks":
        for k in range(0, h, 12):
            svg.append(f'<line x1="{x}" y1="{y+k}" x2="{x+w}" y2="{y+k}" stroke="{line}" stroke-width="1"/>')
        for k in range(0, h, 12):
            off = (k // 12) % 3 * 37
            for xx in range(x + off, x + w, 111):
                svg.append(f'<line x1="{xx}" y1="{y+k}" x2="{xx}" y2="{y+k+12}" stroke="{line}" stroke-width="1"/>')
    elif kind == "tiles":
        for k in range(0, w + 1, 64):
            svg.append(f'<line x1="{x+k}" y1="{y}" x2="{x+k}" y2="{y+h}" stroke="{line}" stroke-width="1"/>')
        for k in range(0, h + 1, 64):
            svg.append(f'<line x1="{x}" y1="{y+k}" x2="{x+w}" y2="{y+k}" stroke="{line}" stroke-width="1"/>')
    elif kind == "carpet":
        for k in range(4, h, 8):
            for xx in range(x + (k % 16), x + w, 16):
                svg.append(f'<circle cx="{xx}" cy="{y+k}" r="0.8" fill="{line}"/>')

def wall_h(tx, ty, tw):
    """Mur horizontal en 3/4 : dessus clair + face."""
    x, y, w = px(tx), px(ty), px(tw)
    rect(x, y, w, 14, C["wall_top"])
    rect(x, y + 14, w, 18, C["wall_face"])
    rect(x, y + 30, w, 2, C["wall_edge"])
    block(tx, ty, tw, 1)

def wall_v(tx, ty, th):
    x, y, h = px(tx), px(ty), px(th)
    rect(x + 8, y, 16, h, C["wall_top"])
    rect(x + 8, y, 2, h, C["wall_edge"]); rect(x + 22, y, 2, h, C["wall_edge"])
    block(tx, ty, 1, th)

def glass_v(tx, ty, th):
    x, y, h = px(tx), px(ty), px(th)
    rect(x + 13, y, 6, h, C["glass"], extra='opacity="0.75"')
    rect(x + 13, y, 1, h, "#FFFFFF", extra='opacity="0.9"')
    for k in range(0, h, 64):
        rect(x + 12, y + k, 8, 3, C["wall_edge"])
    block(tx, ty, 1, th)

def glass_h(tx, ty, tw):
    x, y, w = px(tx), px(ty), px(tw)
    rect(x, y + 13, w, 6, C["glass"], extra='opacity="0.75"')
    rect(x, y + 13, w, 1, "#FFFFFF", extra='opacity="0.9"')
    for k in range(0, w, 64):
        rect(x + k, y + 12, 3, 8, C["wall_edge"])
    block(tx, ty, tw, 1)

def shadow(x, y, w, h, rx=6):
    rect(x + 3, y + 4, w, h, "#0B1220", rx, 'opacity="0.10"')

def desk(tx, ty, tw=3, th=2, screens=2, lamp=False):
    x, y, w, h = px(tx) + 4, px(ty) + 6, px(tw) - 8, px(th) - 10
    shadow(x, y, w, h)
    rect(x, y, w, h, C["desk"], 6)
    rect(x, y + h - 4, w, 4, C["desk_edge"], 2)
    sw = 30
    gap = (w - screens * sw) / (screens + 1)
    for s in range(screens):
        sx = x + gap + s * (sw + gap)
        rect(sx, y + 4, sw, 16, C["ink"], 3)
        rect(sx + 2, y + 6, sw - 4, 11, C["blue"], 2, 'opacity="0.85"')
        rect(sx + sw / 2 - 2, y + 20, 4, 4, C["ink2"])
    rect(x + w / 2 - 14, y + h - 16, 28, 8, "#E3E7F0", 2)
    if lamp:
        svg.append(f'<circle cx="{x+w-10}" cy="{y+10}" r="5" fill="{C["amber"]}" opacity="0.9"/>')
    block(tx, ty, tw, th)

def chair(cx, cy, col=C["ink2"]):
    svg.append(f'<circle cx="{cx+2}" cy="{cy+3}" r="10" fill="#0B1220" opacity="0.10"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="{col}"/>')
    svg.append(f'<rect x="{cx-9}" y="{cy-12}" width="18" height="6" rx="3" fill="{col}"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#FFFFFF" opacity="0.12"/>')

def plant(tx, ty, big=False):
    cx, cy = px(tx) + 16, px(ty) + 16
    r = 15 if big else 11
    svg.append(f'<circle cx="{cx+2}" cy="{cy+4}" r="{r}" fill="#0B1220" opacity="0.12"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy+4}" r="{r-5}" fill="{C["pot"]}"/>')
    for dx, dy in [(-6, -4), (6, -4), (0, -9), (-4, 4), (5, 4), (0, 0)]:
        svg.append(f'<circle cx="{cx+dx*r/12}" cy="{cy+dy*r/12}" r="{r*0.55}" fill="{C["plant"]}"/>')
    for dx, dy in [(-3, -5), (4, -2), (0, 3)]:
        svg.append(f'<circle cx="{cx+dx*r/12}" cy="{cy+dy*r/12}" r="{r*0.3}" fill="{C["plant2"]}"/>')
    block(tx, ty, 1, 1)

def sofa(tx, ty, tw, vertical=False, col=C["sofa"], col2=C["sofa2"]):
    if not vertical:
        x, y, w, h = px(tx) + 2, px(ty) + 4, px(tw) - 4, 26
        shadow(x, y, w, h, 8)
        rect(x, y, w, h, col2, 8); rect(x + 4, y + 8, w - 8, h - 10, col, 6)
        for k in range(1, tw):
            svg.append(f'<line x1="{x+k*w/tw}" y1="{y+9}" x2="{x+k*w/tw}" y2="{y+h-3}" stroke="{col2}" stroke-width="1.5"/>')
        block(tx, ty, tw, 1)
    else:
        x, y, w, h = px(tx) + 4, px(ty) + 2, 26, px(tw) - 4
        shadow(x, y, w, h, 8)
        rect(x, y, w, h, col2, 8); rect(x + 8, y + 4, w - 10, h - 8, col, 6)
        block(tx, ty, 1, tw)

def rug(tx, ty, tw, th, col, rx=14, op=1):
    rect(px(tx), px(ty), px(tw), px(th), col, rx, f'opacity="{op}"')

def screen_wall(tx, ty, tw, title):
    x, y, w = px(tx) + 6, px(ty) + 2, px(tw) - 12
    rect(x, y, w, 26, C["night"], 4)
    rect(x + 3, y + 3, w - 6, 20, C["ink2"], 3)
    text(x + 10, y + 16, title, 8, "#AEB8D0", 600, "start")
    for k in range(5):
        bh = [6, 11, 8, 14, 10][k]
        rect(x + w - 64 + k * 11, y + 21 - bh, 7, bh, C["blue"], 1)

def nameplate(cx, cy, label):
    w = 26 + len(label) * 5.6
    rect(cx - w / 2, cy - 9, w, 17, C["ink"], 8.5)
    svg.append(f'<circle cx="{cx - w/2 + 10}" cy="{cy-0.5}" r="3.2" fill="{C["green"]}"/>')
    text(cx + 6, cy + 3, label, 9, "#FFFFFF", 600)

# ---------------------------------------------------------------- sol global
rect(0, 0, px(W), px(H), "#DDE2EC")
floor(1, 1, W - 2, H - 2, C["hall"], C["hall_line"], "tiles")

# zones
floor(1, 1, 15, 10, C["exec"], C["exec_line"], "planks")          # Chahid & Rachid
floor(17, 1, 12, 10, C["wood"], C["wood_line"], "planks")         # Louis
floor(30, 1, 13, 10, C["wood"], C["wood_line"], "planks")         # Redwane
floor(1, 19, 20, 10, C["call"], C["call_line"], "carpet")        # salle de call
floor(23, 19, 20, 10, C["lounge"], C["lounge_line"], "carpet")   # coin pause

# murs extérieurs
wall_h(0, 0, W); wall_h(0, H - 1, W)
wall_v(0, 1, H - 2); wall_v(W - 1, 1, H - 2)
# rangée de bureaux (haut) : murs nord déjà ; séparations
wall_v(16, 1, 10); wall_v(29, 1, 10)
# façades vitrées des bureaux avec portes
for (a, b, door) in [(1, 15, 7), (17, 12, 22), (30, 13, 35)]:
    glass_h(a, 11, door - a); glass_h(door + 2, 11, a + b - door - 2)
# salles du bas : façades vitrées avec portes
for (a, b, door) in [(1, 20, 9), (23, 20, 31)]:
    glass_h(a, 18, door - a); glass_h(door + 3, 18, a + b - door - 3)
wall_v(21, 18, 11); wall_v(22, 18, 11)
for i in range(21, 23):
    block(i, 18, 1, 11)

# ------------------------------------------------ bureau Chahid & Rachid
rug(3, 4, 11, 5, "#1D2740", 10)
desk(3, 4, 4, 2, screens=2, lamp=True); chair(px(5), px(6) + 14, C["blue"])
desk(9, 4, 4, 2, screens=2, lamp=True); chair(px(11), px(6) + 14, C["blue"])
screen_wall(4, 2, 8, "TRÉSO · CA DU MOIS · RDV")
sofa(2, 8, 4, col="#3A4766", col2="#2A3550")
plant(1, 2, True); plant(14, 2, True); plant(14, 9)
text(px(8), px(10) + 20, "CHAHID · RACHID", 9, "#AEB8D0", 600, spacing=2)
nameplate(px(8), px(12) + 6, "Chahid · Rachid")

# ------------------------------------------------ bureau Louis
rug(19, 4, 8, 5, "#F1E4CF", 10)
desk(20, 4, 4, 2, screens=2); chair(px(22), px(6) + 14)
screen_wall(19, 2, 8, "MES RDV · MES APPELS")
svg.append(f'<circle cx="{px(26)+10}" cy="{px(5)}" r="6" fill="{C["red"]}"/>')
plant(17, 2, True); plant(27, 9); plant(17, 9)
sofa(25, 7, 2, vertical=True, col="#8FA8FF", col2="#6F8EF5")
nameplate(px(23), px(12) + 6, "Louis")

# ------------------------------------------------ bureau Redwane
rug(32, 4, 9, 5, "#F1E4CF", 10)
desk(33, 4, 4, 2, screens=2); chair(px(35), px(6) + 14)
screen_wall(32, 2, 8, "MES RDV · MES APPELS")
svg.append(f'<circle cx="{px(39)+10}" cy="{px(5)}" r="6" fill="{C["green"]}"/>')
plant(30, 2, True); plant(41, 9); plant(41, 2, True)
sofa(39, 7, 2, vertical=True, col="#8FA8FF", col2="#6F8EF5")
nameplate(px(36), px(12) + 6, "Redwane")

# ------------------------------------------------ hall central
svg.append(f'<ellipse cx="{px(22)}" cy="{px(15)}" rx="{px(7)}" ry="{px(2)-2}" fill="{C["blue_soft"]}" stroke="{C["blue"]}" stroke-width="2"/>')
svg.append(f'<ellipse cx="{px(22)}" cy="{px(15)}" rx="{px(7)-10}" ry="{px(2)-12}" fill="none" stroke="{C["blue"]}" stroke-width="1" opacity="0.4"/>')
text(px(22), px(15) + 4, "SÉSAME", 22, C["ink"], 700, family="Poppins", spacing=7)
text(px(22), px(15) + 18, "B2B SALES PARTNER", 7, C["blue"], 700, spacing=3)
# mur des scores (sur le mur gauche du hall)
x0 = px(2) + 4
rect(x0, px(12) + 22, px(8), px(5) + 4, C["night"], 8)
text(x0 + 10, px(13) + 18, "MUR DES SCORES", 9, "#FFFFFF", 700, "start", spacing=1)
for k, (nm, v) in enumerate([("RDV jour", 0.7), ("Appels", 0.85), ("Objectif", 0.55)]):
    yy = px(14) + 6 + k * 18
    text(x0 + 10, yy + 7, nm, 8, "#AEB8D0", 500, "start")
    rect(x0 + 70, yy, 160, 8, C["ink2"], 4)
    rect(x0 + 70, yy, 160 * v, 8, [C["blue"], C["green"], C["amber"]][k], 4)
block(2, 13, 8, 4)
# accueil + plantes du hall
plant(34, 13, True); plant(41, 13, True); plant(34, 16); plant(41, 16)
sofa(36, 14, 4, col="#E9EDF5", col2="#C9D2E3")
rect(px(37) + 4, px(16) - 4, px(2) - 8, 18, "#FFFFFF", 6); block(37, 15, 2, 1)

# ------------------------------------------------ salle de call
rx_, ry_ = px(5), px(21) + 8
svg.append(f'<ellipse cx="{px(11)+3}" cy="{px(24)+6}" rx="{px(5)}" ry="{px(2)+4}" fill="#0B1220" opacity="0.10"/>')
svg.append(f'<ellipse cx="{px(11)}" cy="{px(24)}" rx="{px(5)}" ry="{px(2)+4}" fill="#FFFFFF"/>')
svg.append(f'<ellipse cx="{px(11)}" cy="{px(24)}" rx="{px(5)-8}" ry="{px(2)-4}" fill="#F3F5FA"/>')
block(6, 22, 10, 4)
for k in range(5):
    chair(px(7) + k * 40 + 4, px(21) + 18, C["blue"])
    chair(px(7) + k * 40 + 4, px(26) + 14, C["blue"])
screen_wall(5, 19, 10, "SALLE DE CALL · PARTAGE D'ÉCRAN")
plant(1, 19, True); plant(19, 19, True); plant(1, 27); plant(19, 27)
text(px(11), px(28) + 8, "SALLE DE CALL", 9, "#5A6580", 700, spacing=2)

# ------------------------------------------------ coin pause
rug(25, 21, 11, 6, "#E8CBB9", 18)
sofa(25, 21, 5); sofa(25, 26, 5)
sofa(24, 22, 4, vertical=True)
rect(px(27), px(23) + 6, px(3), px(2) - 8, "#FFFFFF", 10); block(27, 23, 3, 2)
svg.append(f'<circle cx="{px(28)+16}" cy="{px(24)}" r="5" fill="{C["amber"]}"/>')
# comptoir café
rect(px(37), px(20), px(5), px(2) - 6, "#FFFFFF", 6); block(37, 20, 5, 2)
rect(px(38), px(20) + 6, 22, 30, C["ink"], 4)
svg.append(f'<circle cx="{px(38)+11}" cy="{px(21)+2}" r="4" fill="{C["amber"]}"/>')
rect(px(40), px(20) + 8, 20, 14, "#C9D2E3", 3)
text(px(39) + 16, px(22) + 10, "CAFÉ", 9, "#5A6580", 700, spacing=2)
# tables hautes
for (a, b) in [(37, 24), (40, 24), (37, 27), (40, 27)]:
    svg.append(f'<circle cx="{px(a)+16}" cy="{px(b)+16}" r="13" fill="#FFFFFF" stroke="#E3D3C7"/>'); block(a, b, 1, 1)
plant(23, 19, True); plant(41, 19); plant(23, 27, True); plant(33, 27)
text(px(30), px(28) + 8, "COIN PAUSE", 9, "#8A5A44", 700, spacing=2)


# ------------------------------------------------ déco supplémentaire
def shelf(tx, ty, tw):
    x, y, w = px(tx) + 2, px(ty) + 4, px(tw) - 4
    shadow(x, y, w, 22, 3); rect(x, y, w, 22, "#B08E6A", 3)
    cols_ = ["#2F5DFF", "#F2A93B", "#22C17A", "#E5484D", "#8FA8FF", "#0F1729"]
    for k in range(int(w // 7)):
        rect(x + 3 + k * 7, y + 3, 5, 16, cols_[k % len(cols_)], 1)
    block(tx, ty, tw, 1)
def whiteboard(tx, ty, tw):
    x, y, w = px(tx) + 4, px(ty) + 3, px(tw) - 8
    rect(x, y, w, 24, "#FFFFFF", 3, f'stroke="{C["wall_edge"]}"')
    svg.append(f'<polyline points="{x+8},{y+18} {x+20},{y+10} {x+32},{y+14} {x+46},{y+6}" fill="none" stroke="{C["blue"]}" stroke-width="2"/>')
    rect(x + w - 40, y + 7, 30, 3, C["amber"], 1); rect(x + w - 40, y + 13, 22, 3, C["green"], 1)
def glow(cx, cy, r, col, op=0.18):
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="{op}"/>')
def beanbag(tx, ty, col):
    cx, cy = px(tx) + 16, px(ty) + 16
    svg.append(f'<ellipse cx="{cx+2}" cy="{cy+4}" rx="13" ry="11" fill="#0B1220" opacity="0.12"/>')
    svg.append(f'<ellipse cx="{cx}" cy="{cy}" rx="13" ry="11" fill="{col}"/>')
    svg.append(f'<ellipse cx="{cx-3}" cy="{cy-3}" rx="6" ry="4" fill="#FFFFFF" opacity="0.25"/>')
    block(tx, ty, 1, 1)
# Louis / Redwane : étagères + tableau blanc
shelf(18, 9, 3); whiteboard(19, 1, 0) if False else None
shelf(31, 9, 3)
shelf(10, 9, 4)
# lumières suspendues (halo doux)
for (a, b) in [(8, 6), (23, 6), (36, 6), (11, 24), (30, 24), (22, 15)]:
    glow(px(a), px(b), 70, "#FFFFFF", 0.10)
# hall : poufs + bornes
beanbag(13, 16, C["amber"]); beanbag(30, 16, C["green"]); beanbag(13, 13, C["blue"]); beanbag(30, 13, "#E5484D")
# coin pause : télé + jeu
rect(px(25) + 8, px(19) + 2, px(4) - 16, 12, C["night"], 3)
rect(px(25) + 11, px(19) + 4, px(4) - 22, 8, C["blue"], 2, 'opacity="0.8"')
beanbag(33, 22, C["blue"]); beanbag(33, 24, C["amber"])
# salle de call : écran latéral + tableau
whiteboard(16, 19, 3)

# ------------------------------------------------ rendu
svg_doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{px(W)}" height="{px(H)}" '
           f'viewBox="0 0 {px(W)} {px(H)}">' + "".join(svg) + "</svg>")
open(f"{OUT}/map.svg", "w").write(svg_doc)
for scale, name in [(1, "map.png"), (2, "preview@2x.png")]:
    subprocess.run(["rsvg-convert", "-z", str(scale), "-o", f"{OUT}/{name}", f"{OUT}/map.svg"], check=True)

# ------------------------------------------------ découpe en tileset (tuiles dédupliquées)
img = Image.open(f"{OUT}/map.png").convert("RGBA")
uniq, index, data = [], {}, []
for j in range(H):
    for i in range(W):
        tile = img.crop((i * T, j * T, (i + 1) * T, (j + 1) * T))
        h = hashlib.md5(tile.tobytes()).hexdigest()
        if h not in index:
            index[h] = len(uniq); uniq.append(tile)
        data.append(index[h] + 1)
cols = 32
rows = (len(uniq) + cols - 1) // cols
ts = Image.new("RGBA", (cols * T, rows * T), (0, 0, 0, 0))
for k, tile in enumerate(uniq):
    ts.paste(tile, ((k % cols) * T, (k // cols) * T))
ts.save(f"{OUT}/sesame-tiles.png", optimize=True)
coll_png = Image.new("RGBA", (T, T), (255, 0, 0, 0)); coll_png.save(f"{OUT}/collide.png")

n = len(uniq)
cgid = n + 1
start = [0] * (W * H)
for (i, j) in [(21, 27 - 13), (22, 27 - 13), (21, 16 - 2), (22, 16 - 2)]:
    pass
for i in range(18, 26):
    for j in range(13, 17):
        start[j * W + i] = cgid  # zone d'arrivée dans le hall (sur le tapis)
coll = [cgid if collide[j][i] else 0 for j in range(H) for i in range(W)]

def area(oid, name, tx, ty, tw, th, props):
    return {"id": oid, "name": name, "type": "area", "class": "area", "visible": True, "rotation": 0,
            "x": px(tx), "y": px(ty), "width": px(tw), "height": px(th),
            "properties": [{"name": k, "type": t, "value": v} for (k, t, v) in props]}

tmj = {
    "compressionlevel": -1, "infinite": False, "orientation": "orthogonal", "renderorder": "right-down",
    "tiledversion": "1.10.2", "type": "map", "version": "1.10",
    "width": W, "height": H, "tilewidth": T, "tileheight": T, "nextlayerid": 6, "nextobjectid": 10,
    "properties": [
        {"name": "mapName", "type": "string", "value": "Bureau Sésame"},
        {"name": "mapDescription", "type": "string", "value": "Le bureau virtuel de l'équipe Sésame"},
        {"name": "mapCopyright", "type": "string", "value": "Sésame Agency"},
    ],
    "layers": [
        {"id": 1, "name": "start", "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0,
         "opacity": 1, "visible": True, "data": start},
        {"id": 2, "name": "sol", "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0,
         "opacity": 1, "visible": True, "data": data},
        {"id": 3, "name": "collisions", "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0,
         "opacity": 1, "visible": True, "data": coll},
        {"id": 4, "name": "floorLayer", "type": "objectgroup", "draworder": "topdown", "x": 0, "y": 0,
         "opacity": 1, "visible": True, "objects": [
             area(1, "Bureau Chahid et Rachid", 1, 2, 15, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(2, "Bureau Louis", 17, 2, 12, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(3, "Bureau Redwane", 30, 2, 13, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(4, "Salle de call", 1, 19, 20, 10, [("focusable", "bool", True), ("zoom_margin", "float", 0.2)]),
             area(5, "Coin pause", 23, 19, 20, 10, []),
         ]},
    ],
    "tilesets": [
        {"firstgid": 1, "name": "sesame-tiles", "image": "sesame-tiles.png",
         "imagewidth": cols * T, "imageheight": rows * T, "tilewidth": T, "tileheight": T,
         "tilecount": rows * cols, "columns": cols, "margin": 0, "spacing": 0,
         "properties": [{"name": "tilesetCopyright", "type": "string", "value": "Sésame Agency"}]},
        {"firstgid": cgid, "name": "collide", "image": "collide.png", "imagewidth": T, "imageheight": T,
         "tilewidth": T, "tileheight": T, "tilecount": 1, "columns": 1, "margin": 0, "spacing": 0,
         "tiles": [{"id": 0, "properties": [{"name": "collides", "type": "bool", "value": True}]}]},
    ],
}
# la grille de collision et de départ doit rester invisible
tmj["layers"][0]["visible"] = True
json.dump(tmj, open(f"{OUT}/sesame.tmj", "w"), ensure_ascii=False)
print("tuiles uniques:", n, "| tileset", ts.size, "| collisions:", sum(1 for v in coll if v))
