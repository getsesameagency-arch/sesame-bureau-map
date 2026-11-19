#!/usr/bin/env python3
"""Bureau Sésame V2 : pixel art natif 32px (aucun anti-aliasing), net dans WorkAdventure.
Mobilier d'appoint : "House Interior Tileset 32x32" (Graduation Cat, version gratuite), recoloré."""
import json, os, hashlib, colorsys, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font5x7 as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
T, W, H = 32, 44, 30

def hx(s, a=255):
    s = s.lstrip("#"); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)

P = {k: hx(v) for k, v in dict(
    n0="#080D19", n1="#0F1729", n2="#17223D", n3="#22304F", n4="#2E3E63",
    blue="#2F5DFF", blue2="#5B82FF", blue3="#9DB4FF", cyan="#6FD3FF",
    w0="#FFFFFF", w1="#F3F5FA", w2="#E3E8F1", w3="#CBD3E2", w4="#A3AEC6", w5="#7A86A2",
    c0="#EFEBE4", c1="#E5E0D7", c2="#D8D1C5",
    wd0="#E9D2B0", wd1="#DCC097", wd2="#C8A77A",
    cp0="#D9E3F6", cp1="#CDD9F1",
    green="#22C17A", amber="#F2A93B", red="#E5484D", pink="#FF7AB6",
).items()}

img = Image.new("RGBA", (W * T, H * T), P["w3"])
d = ImageDraw.Draw(img)
collide = [[0] * W for _ in range(H)]
above = Image.new("RGBA", img.size, (0, 0, 0, 0))   # calque au-dessus des avatars
da = ImageDraw.Draw(above)

def px(t): return t * T
def R(x0, y0, x1, y1, c, dd=None): (dd or d).rectangle([x0, y0, x1 - 1, y1 - 1], fill=c)
def block(tx, ty, tw, th):
    for j in range(ty, ty + th):
        for i in range(tx, tx + tw):
            if 0 <= i < W and 0 <= j < H: collide[j][i] = 1
def hsh(x, y): return (x * 73856093 ^ y * 19349663) & 0xFFFF
def box(x0, y0, x1, y1, fill, line, dd=None):
    """Rectangle à coins coupés (1px) avec contour, look pixel art."""
    dd = dd or d
    R(x0 + 1, y0, x1 - 1, y1, line, dd); R(x0, y0 + 1, x1, y1 - 1, line, dd)
    R(x0 + 1, y0 + 1, x1 - 1, y1 - 1, fill, dd)
def shadow(x0, y0, x1, y1, dd=None):
    sh = Image.new("RGBA", (x1 - x0, y1 - y0), (8, 13, 25, 46))
    (img if dd is None else above).alpha_composite(sh, (x0, y0))

# ------------------------------------------------------------ sprites du pack (recolorés)
PACK = Image.open(os.path.join(HERE, "InteriorTilesLITE.png")).convert("RGBA")
def sprite(box_, hue=None, sat=None, val=1.0):
    s = PACK.crop(box_); s = s.crop(s.getbbox())
    if hue is None and val == 1.0: return s
    p = s.load()
    for y in range(s.height):
        for x in range(s.width):
            r, g, b, a = p[x, y]
            if not a: continue
            h, sa, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if hue is not None: h = hue
            if sat is not None: sa = min(1, sa * sat)
            v = min(1, v * val)
            r, g, b = colorsys.hsv_to_rgb(h, sa, v)
            p[x, y] = (int(r * 255), int(g * 255), int(b * 255), a)
    return s
S = dict(
    chair=sprite((30, 170, 66, 222), hue=0.62, sat=0.9, val=1.05),
    plant=sprite((290, 156, 320, 202)),
    shelf=sprite((318, 158, 386, 210), hue=0.62, sat=0.55, val=0.9),
    tv=sprite((394, 261, 438, 291)),
    lamp=sprite((263, 260, 280, 302)),
    sofa_b=sprite((320, 336, 417, 386), hue=0.63, sat=1.25, val=1.35),
    sofa_g=sprite((320, 336, 417, 386), hue=0.62, sat=0.35, val=0.9),
    arm_b=sprite((416, 336, 482, 386), hue=0.63, sat=1.25, val=1.35),
    clock=sprite((323, 131, 350, 158)),
    paint=sprite((295, 227, 347, 255)),
    vase=sprite((328, 296, 344, 318)),
)
def put(name, x, y, layer=None):
    (layer or img).alpha_composite(S[name], (x, y))
def put_plant(tx, ty):
    s = S["plant"]; x = px(tx) + (32 - s.width) // 2; y = px(ty) + 32 - s.height
    shadow(x + 6, px(ty) + 26, x + s.width - 4, px(ty) + 31)
    put("plant", x, y)
    above.alpha_composite(s.crop((0, 0, s.width, 14)), (x, y))  # feuillage passe devant l'avatar
    block(tx, ty, 1, 1)

# ------------------------------------------------------------ sols
def floor(tx, ty, tw, th, kind):
    x0, y0, x1, y1 = px(tx), px(ty), px(tx + tw), px(ty + th)
    p = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            lx, ly = x - x0, y - y0
            if kind == "exec":           # parquet sombre
                row = ly // 8; c = P["n2"]
                if ly % 8 == 0: c = P["n1"]
                elif ly % 8 == 1: c = P["n3"]
                elif (lx + row * 29) % 64 == 0: c = P["n1"]
                elif hsh(x, y) % 97 == 0: c = P["n3"]
            elif kind == "tile":         # dalles claires
                c = P["w1"]
                if lx % 32 == 0 or ly % 32 == 0: c = P["w3"]
                elif lx % 32 == 1 or ly % 32 == 1: c = P["w0"]
            elif kind == "hall":         # béton ciré
                c = P["c0"]
                if lx % 64 == 0 or ly % 64 == 0: c = P["c2"]
                elif hsh(x, y) % 23 == 0: c = P["c1"]
            elif kind == "carpet":       # moquette bleue
                c = P["cp1"] if (x + y) % 2 == 0 and (x // 2 + y // 2) % 2 == 0 else P["cp0"]
            elif kind == "wood":         # parquet clair
                row = ly // 8; c = P["wd0"]
                if ly % 8 == 0: c = P["wd2"]
                elif ly % 8 == 1: c = P["w0"] if hsh(x, y) % 3 == 0 else P["wd0"]
                elif (lx + row * 37) % 72 == 0: c = P["wd2"]
                elif hsh(x, y) % 41 == 0: c = P["wd1"]
            p[x, y] = c

# ------------------------------------------------------------ murs
def wall_h(tx, ty, tw, dark=False):
    x0, y0, x1 = px(tx), px(ty), px(tx + tw)
    face, face2 = (P["n3"], P["n4"]) if dark else (P["w2"], P["w0"])
    R(x0, y0, x1, y0 + 8, P["n1"])
    R(x0, y0 + 8, x1, y0 + 9, P["n4"])
    R(x0, y0 + 9, x1, y0 + 28, face)
    R(x0, y0 + 10, x1, y0 + 11, face2)
    R(x0, y0 + 28, x1, y0 + 30, P["w4"] if not dark else P["n1"])
    R(x0, y0 + 30, x1, y0 + 32, (8, 13, 25, 255) if dark else P["w5"])
    block(tx, ty, tw, 1)
def wall_v(tx, ty, th):
    x0, y0, y1 = px(tx), px(ty), px(ty + th)
    R(x0 + 11, y0, x0 + 21, y1, P["n1"]); R(x0 + 12, y0, x0 + 13, y1, P["n4"])
    R(x0 + 21, y0, x0 + 23, y1, (8, 13, 25, 70))
    block(tx, ty, 1, th)
def glass_h(tx, ty, tw):
    x0, y0, x1 = px(tx), px(ty), px(tx + tw)
    gl = Image.new("RGBA", (x1 - x0, 22), (111, 211, 255, 70)); img.alpha_composite(gl, (x0, y0 + 6))
    R(x0, y0 + 4, x1, y0 + 6, P["n1"]); R(x0, y0 + 28, x1, y0 + 30, P["n1"])
    for x in range(x0, x1, 64): R(x, y0 + 4, x + 3, y0 + 30, P["n1"])
    for k in range(x0 + 10, x1 - 12, 64):      # reflets diagonaux
        for t in range(12): img.putpixel((k + t, y0 + 25 - t), P["w0"]); img.putpixel((k + t + 4, y0 + 25 - t), P["w0"])
    block(tx, ty, tw, 1)

# ------------------------------------------------------------ mobilier dessiné
def rug(tx, ty, tw, th, c0, c1, c2):
    x0, y0, x1, y1 = px(tx) + 4, px(ty) + 4, px(tx + tw) - 4, px(ty + th) - 4
    box(x0, y0, x1, y1, c0, c2); R(x0 + 4, y0 + 4, x1 - 4, y0 + 5, c1); R(x0 + 4, y1 - 5, x1 - 4, y1 - 4, c1)
    R(x0 + 4, y0 + 4, x0 + 5, y1 - 4, c1); R(x1 - 5, y0 + 4, x1 - 4, y1 - 4, c1)
def monitor(x, y, col=None, w=24):
    col = col or P["blue"]
    box(x, y, x + w, y + 16, P["n0"], P["n0"])
    R(x + 2, y + 2, x + w - 2, y + 13, col)
    R(x + 2, y + 2, x + w - 2, y + 4, P["blue3"] if col == P["blue"] else P["w0"])
    for k in range(3): R(x + 4, y + 6 + k * 2, x + 4 + [12, 8, 14][k] * w // 24, y + 7 + k * 2, P["w0"] if k == 0 else P["blue3"])
    R(x + w // 2 - 1, y + 16, x + w // 2 + 1, y + 19, P["n2"]); R(x + w // 2 - 5, y + 19, x + w // 2 + 5, y + 21, P["n2"])
def desk(tx, ty, tw=4, th=2, screens=2, accent=None, dark=False):
    x0, y0, x1, y1 = px(tx) + 2, px(ty) + 4, px(tx + tw) - 2, px(ty + th) - 2
    top, line, face = (P["n4"], P["n0"], P["n2"]) if dark else (P["w0"], P["w5"], P["w3"])
    shadow(x0 + 3, y1 - 4, x1 + 3, y1 + 3)
    box(x0, y0, x1, y1 - 6, top, line)
    R(x0 + 1, y1 - 7, x1 - 1, y1 - 1, face); R(x0 + 1, y1 - 1, x1 - 1, y1, line)
    if accent: R(x0 + 1, y1 - 7, x1 - 1, y1 - 6, accent)
    sw = 24; gap = ((x1 - x0) - screens * sw) // (screens + 1)
    for s in range(screens): monitor(x0 + gap + s * (sw + gap), y0 + 4)
    kx = (x0 + x1) // 2 - 12
    box(kx, y1 - 18, kx + 24, y1 - 11, P["w2"] if not dark else P["n3"], P["w5"] if not dark else P["n0"])
    for i in range(3): R(kx + 3, y1 - 16 + i * 2 if i < 2 else y1 - 13, kx + 21, y1 - 15 + i * 2 if i < 2 else y1 - 12, P["w4"] if not dark else P["n1"])
    R(x1 - 14, y1 - 18, x1 - 8, y1 - 12, P["w0"]); R(x1 - 13, y1 - 17, x1 - 9, y1 - 13, P["amber"])   # mug
    block(tx, ty, tw, th)
def chair_at(cx, by):
    s = S["chair"]; put("chair", cx - s.width // 2, by - s.height)
def sofa(name, tx, ty, flip=False):
    s = S[name]
    if flip: s = s.transpose(Image.FLIP_TOP_BOTTOM)
    x, y = px(tx) + 1, px(ty) + 32 * 2 - s.height - 8
    shadow(x + 4, y + s.height - 6, x + s.width + 2, y + s.height + 2)
    img.alpha_composite(s, (x, y)); block(tx, ty + 1, 3, 1)
def label(cx, y, s, col, scale=1):
    F.draw(img, cx - F.width(s, scale) // 2, y, s, col, scale)
def nameplate(cx, cy, s):
    w = F.width(s) + 22; x0, y0 = cx - w // 2, cy - 7
    box(x0, y0, x0 + w, y0 + 14, P["n1"], P["n0"])
    R(x0 + 5, y0 + 5, x0 + 9, y0 + 9, P["green"]); R(x0 + 6, y0 + 4, x0 + 8, y0 + 10, P["green"])
    F.draw(img, x0 + 14, y0 + 4, s, P["w0"])
def screen_wall(tx, ty, tw, title, bars=True):
    x0, y0, x1 = px(tx) + 4, px(ty) + 6, px(tx + tw) - 4
    box(x0, y0, x1, y0 + 22, P["n2"], P["n0"]); R(x0 + 2, y0 + 2, x1 - 2, y0 + 3, P["n4"])
    F.draw(img, x0 + 6, y0 + 8, title, P["blue3"])
    if bars:
        for k, hh in enumerate([5, 9, 7, 12, 10, 14]):
            R(x1 - 52 + k * 8, y0 + 18 - hh, x1 - 47 + k * 8, y0 + 18, P["blue"] if k < 5 else P["green"])
def beanbag(tx, ty, c, c2):
    x0, y0 = px(tx) + 5, px(ty) + 7
    shadow(x0 + 2, y0 + 16, x0 + 24, y0 + 22)
    box(x0, y0 + 2, x0 + 22, y0 + 20, c2, c2); box(x0 + 2, y0, x0 + 20, y0 + 16, c, c2)
    R(x0 + 5, y0 + 3, x0 + 10, y0 + 5, P["w0"]); block(tx, ty, 1, 1)
def hightable(tx, ty):
    x0, y0 = px(tx) + 4, px(ty) + 6
    shadow(x0 + 4, y0 + 18, x0 + 26, y0 + 24)
    box(x0, y0, x0 + 24, y0 + 16, P["w0"], P["w5"]); R(x0 + 1, y0 + 13, x0 + 23, y0 + 15, P["w3"])
    R(x0 + 11, y0 + 16, x0 + 13, y0 + 24, P["n2"]); block(tx, ty, 1, 1)
def light(tx, ty):   # suspension : disque + halo net (2 anneaux, pas de flou)
    cx, cy = px(tx), px(ty)
    for r, a in [(44, 18), (28, 22)]:
        m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=a)
        img.paste(Image.new("RGBA", (2 * r, 2 * r), (255, 255, 255, 255)), (cx - r, cy - r), m) if False else \
            img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (2 * r, 2 * r), (255, 244, 214)).split(), m)), (cx - r, cy - r))

# ============================================================ plan
floor(0, 0, W, H, "hall")
floor(1, 1, 15, 10, "exec"); floor(17, 1, 12, 10, "tile"); floor(30, 1, 13, 10, "tile")
floor(1, 19, 20, 10, "carpet"); floor(23, 19, 20, 10, "wood")

for (a, b) in [(8, 6), (23, 6), (36, 6), (11, 24), (32, 24)]: light(a, b)

# murs
wall_h(0, 0, 16, dark=True); wall_h(16, 0, W - 16)
wall_v(0, 1, H - 2); wall_v(W - 1, 1, H - 2)
wall_v(16, 1, 10); wall_v(29, 1, 10)
for (a, b, door) in [(1, 15, 7), (17, 12, 22), (30, 13, 35)]:
    glass_h(a, 11, door - a); glass_h(door + 2, 11, a + b - door - 2)
for (a, b, door) in [(1, 20, 9), (23, 20, 31)]:
    glass_h(a, 18, door - a); glass_h(door + 3, 18, a + b - door - 3)
wall_v(21, 18, 11); wall_v(22, 18, 11)
R(0, px(H - 1), px(W), px(H), P["n1"]); R(0, px(H - 1), px(W), px(H - 1) + 2, P["n4"]); block(0, H - 1, W, 1)

# --- bureau Chahid & Rachid (salle fermée, sombre, accents bleus)
rug(3, 3, 11, 6, P["n1"], P["blue"], P["n0"])
screen_wall(4, 0, 8, "TRÉSO · CA · RDV")
desk(3, 4, 4, 2, accent=P["blue"], dark=True); chair_at(px(5), px(7) + 10)
desk(9, 4, 4, 2, accent=P["blue"], dark=True); chair_at(px(11), px(7) + 10)
put("shelf", px(13) + 4, px(1) - 10); block(13, 1, 2, 1)
sofa("sofa_g", 2, 8)
put_plant(1, 1); put_plant(14, 9); put("lamp", px(14) + 8, px(7) - 4)
label(px(8), px(10) + 12, "CHAHID · RACHID", P["blue3"])
nameplate(px(8), px(12) + 10, "CHAHID · RACHID")

# --- Louis
rug(19, 3, 8, 6, P["w2"], P["blue2"], P["w4"])
screen_wall(19, 0, 8, "MES RDV · APPELS")
desk(20, 4, 4, 2, accent=P["blue2"]); chair_at(px(22), px(7) + 10)
R(px(26) + 6, px(4) + 10, px(26) + 14, px(4) + 18, P["red"]); R(px(26) + 8, px(4) + 8, px(26) + 12, px(4) + 20, P["red"])   # voyant d'appel
put("shelf", px(17) + 2, px(9) - 18); block(17, 9, 2, 1)
put_plant(27, 1); put_plant(27, 9); put("clock", px(24) + 2, px(0) + 4)
nameplate(px(23), px(12) + 10, "LOUIS")

# --- Redwane
rug(32, 3, 9, 6, P["w2"], P["blue2"], P["w4"])
screen_wall(32, 0, 8, "MES RDV · APPELS")
desk(33, 4, 4, 2, accent=P["blue2"]); chair_at(px(35), px(7) + 10)
R(px(39) + 6, px(4) + 10, px(39) + 14, px(4) + 18, P["green"]); R(px(39) + 8, px(4) + 8, px(39) + 12, px(4) + 20, P["green"])
put("shelf", px(30) + 2, px(9) - 18); block(30, 9, 2, 1)
put_plant(41, 1); put_plant(41, 9); put("paint", px(40) - 6, px(0) + 6)
nameplate(px(36), px(12) + 10, "REDWANE")

# --- hall
x0, y0, x1, y1 = px(15), px(13), px(29), px(17)
box(x0, y0, x1, y1, P["n1"], P["n0"]); box(x0 + 4, y0 + 4, x1 - 4, y1 - 4, P["n2"], P["blue"])
label((x0 + x1) // 2, y0 + 30, "SÉSAME", P["w0"], 4)
label((x0 + x1) // 2, y0 + 70, "B2B SALES PARTNER", P["cyan"], 2)
R(x0 + 40, y0 + 64, x1 - 40, y0 + 65, P["blue"])
# mur des scores
sx0, sy0 = px(2) + 4, px(12) + 22
box(sx0, sy0, sx0 + px(8) - 8, sy0 + px(4) + 8, P["n1"], P["n0"])
R(sx0 + 2, sy0 + 2, sx0 + px(8) - 10, sy0 + 3, P["n4"])
F.draw(img, sx0 + 8, sy0 + 8, "MUR DES SCORES", P["w0"])
R(sx0 + px(8) - 22, sy0 + 8, sx0 + px(8) - 16, sy0 + 14, P["green"])
for k, (nm, v, c) in enumerate([("RDV JOUR", .7, "blue"), ("APPELS", .85, "green"), ("OBJECTIF", .55, "amber")]):
    yy = sy0 + 26 + k * 22
    F.draw(img, sx0 + 8, yy, nm, P["blue3"])
    R(sx0 + 74, yy - 1, sx0 + 74 + 160, yy + 8, P["n3"]); R(sx0 + 74, yy - 1, sx0 + 74 + int(160 * v), yy + 8, P[c])
    R(sx0 + 74, yy - 1, sx0 + 74 + int(160 * v), yy, P["w0"])
block(2, 13, 8, 4)
beanbag(12, 13, P["blue"], P["n3"]); beanbag(12, 16, P["amber"], (190, 120, 30, 255))
beanbag(31, 13, P["green"], (20, 130, 80, 255)); beanbag(31, 16, P["pink"], (200, 80, 140, 255))
put_plant(34, 13); put_plant(41, 13); put_plant(34, 16); put_plant(41, 16)
sofa("arm_b", 36, 13); sofa("arm_b", 38, 13)
hightable(37, 16); hightable(38, 16)

# --- salle de call
x0, y0, x1, y1 = px(6), px(22), px(16), px(26)
shadow(x0 + 4, y1 - 6, x1 + 4, y1 + 4)
box(x0, y0, x1, y1 - 6, P["w0"], P["w5"]); R(x0 + 1, y1 - 7, x1 - 1, y1 - 1, P["w3"]); R(x0 + 1, y1 - 1, x1 - 1, y1, P["w5"])
R(x0 + 8, y0 + 8, x1 - 8, y0 + 10, P["blue"])
for k in range(4): monitor(x0 + 20 + k * 78, y0 + 30, P["blue"], 20)
block(6, 22, 10, 4)
for k in range(5):
    chair_at(px(7) + k * 64 + 16, px(22) + 4)
    chair_at(px(7) + k * 64 + 16, px(27) + 12)
screen_wall(5, 18, 11, "SALLE DE CALL · PARTAGE D'ÉCRAN")
put_plant(1, 19); put_plant(19, 19); put_plant(1, 27); put_plant(19, 27)
label(px(11), px(28) + 10, "SALLE DE CALL", P["n3"])

# --- coin pause
rug(24, 21, 12, 7, (235, 214, 196, 255), (214, 186, 162, 255), (190, 160, 136, 255))
sofa("sofa_b", 25, 20); sofa("sofa_b", 29, 20)
sofa("sofa_b", 25, 25, flip=True); sofa("sofa_b", 29, 25, flip=True)
x0, y0 = px(27) + 8, px(23) + 10
box(x0, y0, x0 + px(4) - 16, y0 + 26, P["w0"], P["w5"]); R(x0 + 1, y0 + 22, x0 + px(4) - 17, y0 + 25, P["w3"])
put("vase", x0 + 50, y0 + 2); block(27, 23, 4, 1)
put("tv", px(26) + 10, px(18) + 2)
# comptoir café
x0, y0 = px(37), px(19) + 4
box(x0, y0, x0 + px(5), y0 + 44, P["n2"], P["n0"]); R(x0 + 1, y0 + 34, x0 + px(5) - 1, y0 + 43, P["n1"])
R(x0 + 1, y0 + 33, x0 + px(5) - 1, y0 + 34, P["blue"])
box(x0 + 10, y0 + 6, x0 + 34, y0 + 30, P["w2"], P["n0"]); R(x0 + 18, y0 + 12, x0 + 26, y0 + 18, P["n1"]); R(x0 + 20, y0 + 22, x0 + 24, y0 + 28, P["amber"])
for k in range(4): R(x0 + 50 + k * 14, y0 + 16, x0 + 58 + k * 14, y0 + 26, P["w0"]); R(x0 + 51 + k * 14, y0 + 17, x0 + 57 + k * 14, y0 + 20, (120, 70, 40, 255))
F.draw(img, x0 + 100, y0 + 16, "CAFÉ", P["amber"], 2)
block(37, 19, 5, 2)
for (a, b) in [(37, 23), (40, 23), (37, 26), (40, 26)]: hightable(a, b)
beanbag(34, 22, P["blue"], P["n3"]); beanbag(34, 25, P["amber"], (190, 120, 30, 255))
put_plant(23, 19); put_plant(23, 27); put_plant(42 - 1, 27)
label(px(30), px(28) + 10, "COIN PAUSE", (150, 100, 70, 255))

# ============================================================ export
img.save(os.path.join(OUT, "map.png")); above.save(os.path.join(OUT, "above.png"))
full = img.copy(); full.alpha_composite(above); full.save(os.path.join(OUT, "map_full.png"))
full.resize((full.width * 2, full.height * 2), Image.NEAREST).save(os.path.join(OUT, "preview@2x.png"))

uniq, index = [], {}
def slice_(im, keep_empty=False):
    data = []
    for j in range(H):
        for i in range(W):
            tile = im.crop((i * T, j * T, (i + 1) * T, (j + 1) * T))
            if not keep_empty and tile.getbbox() is None: data.append(0); continue
            h = hashlib.md5(tile.tobytes()).hexdigest()
            if h not in index: index[h] = len(uniq); uniq.append(tile)
            data.append(index[h] + 1)
    return data
d_sol = slice_(img, True); d_above = slice_(above)
cols = 32; rows = (len(uniq) + cols - 1) // cols
ts = Image.new("RGBA", (cols * T, rows * T), (0, 0, 0, 0))
for k, tile in enumerate(uniq): ts.paste(tile, ((k % cols) * T, (k // cols) * T))
ts.save(os.path.join(OUT, "sesame-tiles.png"), optimize=True)
Image.new("RGBA", (T, T), (255, 0, 0, 0)).save(os.path.join(OUT, "collide.png"))
n = len(uniq); cgid = rows * cols + 1
start = [0] * (W * H)
for i in range(18, 26):
    for j in range(17, 18): start[j * W + i] = cgid
coll = [cgid if collide[j][i] else 0 for j in range(H) for i in range(W)]
def area(oid, name, tx, ty, tw, th, props):
    return {"id": oid, "name": name, "type": "area", "class": "area", "visible": True, "rotation": 0,
            "x": px(tx), "y": px(ty), "width": px(tw), "height": px(th),
            "properties": [{"name": k, "type": t, "value": v} for (k, t, v) in props]}
def tl(i, name, data, vis=True):
    return {"id": i, "name": name, "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0, "opacity": 1, "visible": vis, "data": data}
tmj = {
    "compressionlevel": -1, "infinite": False, "orientation": "orthogonal", "renderorder": "right-down",
    "tiledversion": "1.10.2", "type": "map", "version": "1.10",
    "width": W, "height": H, "tilewidth": T, "tileheight": T, "nextlayerid": 7, "nextobjectid": 10,
    "properties": [
        {"name": "mapName", "type": "string", "value": "Bureau Sésame"},
        {"name": "mapDescription", "type": "string", "value": "Le bureau virtuel de l'équipe Sésame"},
        {"name": "mapCopyright", "type": "string", "value": "Sésame Agency. Mobilier : House Interior Tileset 32x32 par Graduation Cat (itch.io, version gratuite)"},
    ],
    "layers": [
        tl(1, "start", start), tl(2, "sol", d_sol), tl(3, "collisions", coll),
        {"id": 4, "name": "floorLayer", "type": "objectgroup", "draworder": "topdown", "x": 0, "y": 0,
         "opacity": 1, "visible": True, "objects": [
             area(1, "Bureau Chahid et Rachid", 1, 2, 15, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(2, "Bureau Louis", 17, 2, 12, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(3, "Bureau Redwane", 30, 2, 13, 9, [("focusable", "bool", True), ("zoom_margin", "float", 0.3)]),
             area(4, "Salle de call", 1, 19, 20, 10, [("focusable", "bool", True), ("zoom_margin", "float", 0.2)]),
             area(5, "Coin pause", 23, 19, 20, 10, []),
         ]},
        tl(5, "dessus", d_above),
    ],
    "tilesets": [
        {"firstgid": 1, "name": "sesame-tiles", "image": "sesame-tiles.png",
         "imagewidth": cols * T, "imageheight": rows * T, "tilewidth": T, "tileheight": T,
         "tilecount": rows * cols, "columns": cols, "margin": 0, "spacing": 0},
        {"firstgid": cgid, "name": "collide", "image": "collide.png", "imagewidth": T, "imageheight": T,
         "tilewidth": T, "tileheight": T, "tilecount": 1, "columns": 1, "margin": 0, "spacing": 0,
         "tiles": [{"id": 0, "properties": [{"name": "collides", "type": "bool", "value": True}]}]},
    ],
}
json.dump(tmj, open(os.path.join(OUT, "sesame.tmj"), "w"), ensure_ascii=False)
print("tuiles:", n, "tileset", ts.size, "collisions", sum(1 for v in coll if v))
