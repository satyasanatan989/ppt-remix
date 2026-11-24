import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFilter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle, Rectangle, FancyBboxPatch, Polygon, FancyArrowPatch

OUT = "./img/"
PX = 144  # px per inch
W, H = int(13.333 * PX), int(7.5 * PX)
random.seed(3); np.random.seed(3)

CH = "#F3F1EA"; YEL = "#F3E28F"; MINT = "#7FDCC4"; ORG = "#F4A259"; COR = "#EE8E8E"; BLU = "#A9C8F0"
BOARD = (34, 48, 43)

def I(x): return int(round(x * PX))

# ---------------- backgrounds ----------------
def stripes(c1, c2, sw=22):
    im = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(im)
    for x in range(0, W, sw * 2):
        d.rectangle([x, 0, x + sw - 1, H], fill=c2)
    return im

def board_texture(w, h, base):
    arr = np.ones((h, w, 3)) * np.array(base, float)
    arr += np.random.normal(0, 2.2, (h, w, 1))
    im = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    # faint chalk smudges
    sm = Image.new("L", (w, h), 0); ds = ImageDraw.Draw(sm)
    for _ in range(14):
        x, y = random.randint(0, w), random.randint(0, h)
        rx, ry = random.randint(120, 380), random.randint(25, 70)
        ds.ellipse([x - rx, y - ry, x + rx, y + ry], fill=random.randint(6, 12))
    sm = sm.filter(ImageFilter.GaussianBlur(40))
    white = Image.new("RGB", (w, h), (235, 235, 225))
    return Image.composite(white, im, sm)

def wood(d, box, col=(138, 90, 59), dark=(104, 66, 42)):
    d.rectangle(box, fill=col)
    x0, y0, x1, y1 = box
    for _ in range(int((x1 - x0) * (y1 - y0) / 4000) + 3):
        yy = random.randint(y0, y1); xx = random.randint(x0, x1)
        d.line([xx, yy, min(x1, xx + random.randint(40, 200)), yy], fill=dark, width=1)

def chalk_sticks(d, x, y):
    cols = [(243, 241, 234), (243, 226, 143), (127, 220, 196)]
    for i, c in enumerate(cols):
        d.rounded_rectangle([x + i * I(0.42), y, x + i * I(0.42) + I(0.32), y + I(0.08)], radius=5, fill=c)
    ex = x + I(1.45)
    d.rectangle([ex, y - I(0.06), ex + I(0.75), y + I(0.1)], fill=(214, 190, 150))
    d.rectangle([ex, y - I(0.06), ex + I(0.75), y - I(0.0)], fill=(90, 70, 55))

def content_bg():
    im = stripes((195, 211, 200), (183, 200, 188))
    d = ImageDraw.Draw(im)
    fx0, fy0, fx1, fy1 = I(0.30), I(0.25), I(13.03), I(6.90)
    d.rectangle([fx0 + 8, fy0 + 10, fx1 + 8, fy1 + 10], fill=(150, 165, 155))  # shadow
    wood(d, [fx0, fy0, fx1, fy1])
    bx0, by0, bx1, by1 = I(0.46), I(0.41), I(12.87), I(6.74)
    im.paste(board_texture(bx1 - bx0, by1 - by0, BOARD), (bx0, by0))
    d = ImageDraw.Draw(im)
    wood(d, [I(0.15), I(6.84), I(13.18), I(7.08)], (122, 78, 51), (95, 60, 38))
    d.rectangle([I(0.15), I(6.84), I(13.18), I(6.87)], fill=(160, 112, 78))
    chalk_sticks(d, I(10.1), I(6.76))
    im.save(OUT + "bg_content.png")

def section_bg():
    im = stripes((43, 56, 51), (38, 50, 46))
    d = ImageDraw.Draw(im)
    # floor
    wood(d, [0, I(6.55), W, H], (138, 90, 59), (104, 66, 42))
    d.rectangle([0, I(6.55), W, I(6.6)], fill=(170, 120, 85))
    # easel stand
    d.rectangle([I(4.6), I(5.35), I(4.85), I(6.6)], fill=(122, 78, 51))
    d.rectangle([I(8.48), I(5.35), I(8.73), I(6.6)], fill=(122, 78, 51))
    wood(d, [I(3.6), I(5.15), I(9.73), I(5.42)], (138, 90, 59), (104, 66, 42))
    # board with yellow frame
    x0, y0, x1, y1 = I(3.35), I(0.85), I(9.98), I(5.15)
    d.rounded_rectangle([x0 + 10, y0 + 12, x1 + 10, y1 + 12], radius=26, fill=(25, 33, 30))
    d.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=(239, 217, 138))
    bi = board_texture(x1 - x0 - I(0.4), y1 - y0 - I(0.4), (76, 103, 91))
    im.paste(bi, (x0 + I(0.2), y0 + I(0.2)))
    im.save(OUT + "bg_section.png")

# ---------------- matplotlib helpers ----------------
plt.rcParams.update({"font.family": "Liberation Serif", "path.sketch": (1.0, 70, 2.0),
                     "savefig.transparent": True})

def fig(w, h):
    f = plt.figure(figsize=(w, h), dpi=200)
    ax = f.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    ax.set_aspect("equal")
    return f, ax

def save(f, name):
    f.savefig(OUT + name, transparent=True); plt.close(f)

def T(ax, x, y, s, c=CH, size=14, **k):
    ax.text(x, y, s, color=c, fontsize=size, ha=k.pop("ha", "center"), va=k.pop("va", "center"), **k)

def arrow(ax, p, q, c=CH, lw=2, rad=0.0, ms=16):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, color=c, lw=lw,
                                 connectionstyle=f"arc3,rad={rad}"))

# ---------------- doodles ----------------
def doodles():
    # hexagon molecule chain
    f, ax = fig(3, 2)
    def hexa(cx, cy, r, c):
        pts = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
        ax.add_patch(Polygon(pts, closed=True, fill=False, ec=c, lw=3))
        return pts
    p1 = hexa(0.9, 1.0, 0.45, MINT); p2 = hexa(0.9 + 0.78, 1.45, 0.45, MINT)
    ax.plot([2.1, 2.55], [1.7, 1.95], color=MINT, lw=3); ax.add_patch(Circle((2.65, 2.0) if False else (2.6, 1.95), 0.1, color=MINT))
    ax.plot([0.9, 0.9], [0.55, 0.2], color=MINT, lw=3); ax.add_patch(Circle((0.9, 0.15), 0.09, color=MINT))
    save(f, "d_molecule.png")
    # nanoparticle cluster
    f, ax = fig(2.4, 2.4)
    for _ in range(16):
        x, y, r = random.uniform(0.4, 2.0), random.uniform(0.4, 2.0), random.uniform(0.12, 0.28)
        ax.add_patch(Circle((x, y), r, fill=False, ec=YEL, lw=2.5))
        ax.add_patch(Circle((x - r * 0.3, y + r * 0.3), r * 0.18, color=YEL))
    save(f, "d_np.png")
    # leaf
    f, ax = fig(2, 2.4)
    t = np.linspace(0, math.pi, 60)
    ax.fill_between(1 + 0.6 * np.sin(t) * 0, 0, 0, color="none")
    xs = 1 + 0.65 * np.sin(t); ys = 0.4 + 1.7 * (t / math.pi)
    ax.plot(xs, ys, color=ORG, lw=3); ax.plot(2 - xs, ys, color=ORG, lw=3)
    ax.plot([1, 1], [0.1, 2.1], color=ORG, lw=3)
    for k in np.linspace(0.7, 1.7, 5):
        ax.plot([1, 1.45], [k, k + 0.25], color=ORG, lw=2); ax.plot([1, 0.55], [k, k + 0.25], color=ORG, lw=2)
    save(f, "d_leaf.png")
    # squiggle
    f, ax = fig(2.5, 1)
    x = np.linspace(0.2, 2.3, 200); ax.plot(x, 0.5 + 0.22 * np.sin(x * 9), color=COR, lw=3.5)
    save(f, "d_squiggle.png")
    # package box with nano dots
    f, ax = fig(3.2, 3.2)
    ax.add_patch(Polygon([(0.4, 0.4), (2.2, 0.4), (2.2, 2.0), (0.4, 2.0)], fill=False, ec=CH, lw=3))
    ax.add_patch(Polygon([(0.4, 2.0), (1.0, 2.6), (2.8, 2.6), (2.2, 2.0)], fill=False, ec=CH, lw=3))
    ax.add_patch(Polygon([(2.2, 0.4), (2.8, 1.0), (2.8, 2.6), (2.2, 2.0)], fill=False, ec=CH, lw=3))
    for _ in range(22):
        ax.add_patch(Circle((random.uniform(0.6, 2.0), random.uniform(0.6, 1.8)), random.uniform(0.04, 0.09), color=random.choice([MINT, YEL, ORG])))
    T(ax, 1.3, 1.2, "", size=10)
    save(f, "d_box.png")

# ---------------- diagrams ----------------
def nano_scale():
    f, ax = fig(7, 3.3)
    ax.plot([0.4, 6.6], [1.2, 1.2], color=CH, lw=3)
    items = [(-1, "Apple\n~10 cm", ORG), (-4.1, "Human hair\n~80 µm", CH), (-6, "Bacterium\n~1 µm", MINT),
             (-7, "Virus\n~100 nm", COR), (-7.9, "Nanoparticle\n1–100 nm", YEL), (-8.7, "DNA width\n~2 nm", BLU),
             (-10, "Atom\n~0.1 nm", CH)]
    for n, (e, lab, c) in enumerate(items):
        x = 0.4 + (e + 1) / (-9) * 6.2
        ax.plot([x, x], [1.05, 1.35], color=c, lw=3)
        ax.add_patch(Circle((x, 1.95), 0.08 + 0.03 * (10 + e) / 2.2, fill=False, ec=c, lw=2.5))
        T(ax, x, 0.62 if n % 2 == 0 else 2.75, lab, c, 13)
    x1 = 0.4 + 6 / 9 * 6.2; x2 = 0.4 + 7.95 / 9 * 6.2
    ax.add_patch(FancyBboxPatch((x1 - 0.05, 1.0), x2 - x1 + 0.1, 0.5, boxstyle="round,pad=0.04", fill=False, ec=YEL, lw=1.8, ls="--"))
    T(ax, 1.2, 2.75, "log scale  →  smaller", CH, 12, style="italic")
    save(f, "nano_scale.png")

def sav():
    f, ax = fig(6.4, 3.4)
    def cube(x, y, s, c):
        o = s * 0.35
        ax.add_patch(Polygon([(x, y), (x + s, y), (x + s, y + s), (x, y + s)], fill=False, ec=c, lw=2.5))
        ax.add_patch(Polygon([(x, y + s), (x + o, y + s + o), (x + s + o, y + s + o), (x + s, y + s)], fill=False, ec=c, lw=2.5))
        ax.add_patch(Polygon([(x + s, y), (x + s + o, y + o), (x + s + o, y + s + o), (x + s, y + s)], fill=False, ec=c, lw=2.5))
    cube(0.4, 1.0, 1.4, CH)
    T(ax, 1.25, 0.55, "1 cube, side = a\nSA:V = 6/a", CH, 14)
    arrow(ax, (2.55, 1.75), (3.35, 1.75), YEL, 2.5)
    T(ax, 2.95, 2.15, "divide", YEL, 13)
    for i in range(3):
        for j in range(3):
            cube(3.6 + i * 0.6, 0.95 + j * 0.6, 0.42, MINT)
    T(ax, 4.75, 0.5, "27 cubes, side = a/3\nSA:V = 18/a  (3× higher)", MINT, 14)
    save(f, "sav.png")

def tortuous():
    f, ax = fig(7.6, 3.6)
    for k, (x0, title) in enumerate([(0.2, "Neat polymer film"), (4.0, "Polymer + nanoclay platelets")]):
        ax.add_patch(Rectangle((x0, 0.5), 3.4, 2.4, fill=False, ec=CH, lw=2.5))
        T(ax, x0 + 1.7, 3.25, title, YEL if k else CH, 15, weight="bold")
    # straight path
    arrow(ax, (1.9, 3.0), (1.9, 0.35), MINT, 2.5)
    T(ax, 1.9, 0.12, "short, direct path", MINT, 12)
    # platelets
    plates = [(4.3, 2.4), (5.6, 2.4), (4.9, 1.85), (6.3, 1.85), (4.3, 1.3), (5.6, 1.3), (5.0, 0.8), (6.25, 0.8)]
    for x, y in plates:
        ax.plot([x, x + 0.95], [y, y], color=ORG, lw=5, solid_capstyle="round")
    path = [(5.4, 3.0), (5.4, 2.6), (5.0, 2.6), (4.2, 2.6) if False else (5.35, 2.6), (5.4, 2.13), (6.15, 2.13), (6.15, 1.6), (5.45, 1.6), (5.45, 1.05), (6.05, 1.05), (6.05, 0.35)]
    xs, ys = zip(*path); ax.plot(xs[:-1], ys[:-1], color=MINT, lw=2.5)
    arrow(ax, path[-2], path[-1], MINT, 2.5)
    T(ax, 5.7, 0.12, "long, tortuous path", MINT, 12)
    ax.add_patch(Circle((5.4, 3.05), 0.08, color=MINT)); ax.add_patch(Circle((1.9, 3.05), 0.08, color=MINT))
    T(ax, 7.0, 3.0, "O₂ / H₂O", MINT, 12) ; T(ax, 3.1, 3.0, "", MINT, 12)
    save(f, "tortuous.png")

def antimicrobial():
    f, ax = fig(7, 4.2)
    ax.add_patch(Ellipse((3.5, 2.1), 3.6, 2.0, fill=False, ec=MINT, lw=3.5))
    ax.add_patch(Ellipse((3.5, 2.1), 3.3, 1.72, fill=False, ec=MINT, lw=1.5, ls="--"))
    t = np.linspace(0, 4 * math.pi, 120); ax.plot(3.1 + 0.6 * np.cos(t) * np.linspace(0.3, 1, 120), 2.1 + 0.3 * np.sin(t) * np.linspace(0.3, 1, 120), color=BLU, lw=2)
    T(ax, 3.2, 1.55, "DNA", BLU, 12)
    # Ag ions
    for x, y in [(0.6, 3.6), (1.0, 3.2), (0.4, 2.8), (6.3, 3.7), (6.6, 3.2)]:
        ax.add_patch(Circle((x, y), 0.14, fill=False, ec=YEL, lw=2)); T(ax, x, y, "+", YEL, 11)
    T(ax, 0.75, 3.95, "Ag$^{+}$ ions", YEL, 13, weight="bold")
    arrow(ax, (1.1, 3.05), (2.0, 2.6), YEL)
    # ROS
    for x, y in [(6.0, 0.7), (6.4, 1.0), (6.6, 0.5)]:
        T(ax, x, y, "•OH", COR, 12, weight="bold")
    T(ax, 6.2, 1.45, "ROS from ZnO / TiO₂", COR, 12)
    arrow(ax, (5.7, 0.9), (4.9, 1.45), COR)
    # membrane damage
    ax.plot([1.85, 1.6, 1.9, 1.65], [1.4, 1.2, 1.05, 0.85], color=ORG, lw=3)
    T(ax, 1.0, 0.55, "membrane damage\n& leakage", ORG, 12)
    T(ax, 4.45, 2.55, "protein / enzyme\ninactivation (–SH)", CH, 11)
    T(ax, 3.5, 3.6, "Bacterial cell", MINT, 14, weight="bold")
    save(f, "antimicrobial.png")

def structures():
    f, ax = fig(9, 3.3)
    titles = ["Phase-separated\n(microcomposite)", "Intercalated", "Exfoliated"]
    cols = [CH, YEL, MINT]
    for k in range(3):
        x0 = 0.2 + k * 3.0
        ax.add_patch(Rectangle((x0, 0.9), 2.6, 1.9, fill=False, ec=CH, lw=2))
        T(ax, x0 + 1.3, 0.4, titles[k], cols[k], 14, weight="bold")
        # polymer chains
        for _ in range(5):
            xs = np.linspace(x0 + 0.1, x0 + 2.5, 40); ys = random.uniform(1.0, 2.7) + 0.07 * np.sin(xs * 8 + random.random() * 6)
            ax.plot(xs, ys, color="#6F8A80", lw=1.2)
    # k=0 tight stack
    for i in range(6): ax.plot([0.9, 1.9], [1.45 + i * 0.09, 1.45 + i * 0.09], color=ORG, lw=3.5)
    # k=1 expanded stack
    for i in range(5):
        ax.plot([3.85, 4.95], [1.2 + i * 0.32, 1.2 + i * 0.32], color=ORG, lw=3.5)
        if i < 4:
            xs = np.linspace(3.85, 4.95, 30); ax.plot(xs, 1.36 + i * 0.32 + 0.04 * np.sin(xs * 20), color=YEL, lw=1.3)
    # k=2 scattered
    for _ in range(9):
        cx, cy, a = random.uniform(6.6, 8.3), random.uniform(1.15, 2.55), random.uniform(-0.6, 0.6)
        ax.plot([cx - 0.3 * math.cos(a), cx + 0.3 * math.cos(a)], [cy - 0.3 * math.sin(a), cy + 0.3 * math.sin(a)], color=ORG, lw=3.5)
    save(f, "structures.png")

def electrospin():
    f, ax = fig(7.6, 3.6)
    ax.add_patch(Rectangle((0.3, 1.9), 1.5, 0.55, fill=False, ec=CH, lw=2.5))
    ax.plot([0.05, 0.3], [2.17, 2.17], color=CH, lw=2.5); ax.plot([0.05, 0.05], [1.95, 2.4], color=CH, lw=2.5)
    ax.plot([1.8, 2.3], [2.17, 2.17], color=CH, lw=2.5)
    T(ax, 1.05, 2.75, "Syringe pump\n(polymer solution)", CH, 12)
    ax.add_patch(Polygon([(2.3, 2.05), (2.3, 2.29), (2.6, 2.17)], fill=False, ec=YEL, lw=2))
    T(ax, 3.15, 1.7, "Taylor cone", YEL, 12)
    xs = np.linspace(2.6, 5.6, 300); ys = 2.17 + np.where(xs > 3.3, 0.5 * np.sin((xs - 3.3) * 9) * (xs - 3.3) / 2.3, 0)
    ax.plot(xs, ys, color=MINT, lw=1.6)
    T(ax, 4.2, 3.15, "whipping jet → solvent evaporates", MINT, 12)
    ax.add_patch(Rectangle((5.7, 0.8), 0.25, 2.8, fill=False, ec=ORG, lw=3))
    T(ax, 6.85, 3.0, "Grounded\ncollector", ORG, 12)
    ax.plot([2.3, 2.3, 6.6, 6.6, 5.95], [2.0, 0.35, 0.35, 1.6, 1.6], color=COR, lw=1.8)
    ax.add_patch(Circle((4.3, 0.35), 0.28, fill=False, ec=COR, lw=2)); T(ax, 4.3, 0.36, "HV", COR, 11, weight="bold")
    T(ax, 4.3, 0.85, "10–30 kV", COR, 12)
    save(f, "electrospin.png")

def scavenger():
    f, ax = fig(6, 3.6)
    ax.add_patch(FancyBboxPatch((0.4, 0.5), 5.2, 2.6, boxstyle="round,pad=0.05", fill=False, ec=CH, lw=3))
    ax.add_patch(Rectangle((0.5, 2.75), 5.0, 0.22, fill=False, ec=YEL, lw=2, hatch="///"))
    T(ax, 3.0, 3.35, "Scavenger layer: nano-Fe / TiO₂ / Pd", YEL, 13, weight="bold")
    ax.add_patch(Ellipse((3.0, 1.05), 3.2, 0.7, fill=False, ec=ORG, lw=2.5)); T(ax, 3.0, 1.05, "Food", ORG, 14)
    for x, y in [(1.0, 1.9), (1.8, 2.2), (2.7, 1.8), (3.6, 2.25), (4.6, 1.85), (5.1, 2.3)]:
        T(ax, x, y, "O₂", MINT, 13, weight="bold")
        arrow(ax, (x, y + 0.15), (x, 2.68), MINT, 1.5, ms=11)
    T(ax, 3.0, 0.2, "Headspace O₂ / ethylene trapped → slower oxidation & ripening", CH, 12)
    save(f, "scavenger.png")

def sensor():
    f, ax = fig(7.6, 3.2)
    ax.add_patch(Ellipse((1.1, 1.4), 1.6, 0.9, fill=False, ec=ORG, lw=3)); T(ax, 1.1, 1.4, "Food", ORG, 14)
    for i, g in enumerate(["NH₃ / amines", "H₂S", "CO₂", "pH shift"]):
        T(ax, 2.8, 2.95 - i * 0.33, g, CH, 12)
    arrow(ax, (1.95, 1.4), (3.65, 1.4), CH, 2)
    ax.add_patch(FancyBboxPatch((3.8, 1.0), 1.4, 1.2, boxstyle="round,pad=0.05", fill=False, ec=YEL, lw=2.5))
    T(ax, 4.5, 1.6, "Nano-\nsensor", YEL, 14, weight="bold")
    T(ax, 4.5, 0.6, "AuNPs · CNTs · dyes", YEL, 11)
    arrow(ax, (5.35, 1.6), (6.0, 1.6), CH, 2)
    ax.add_patch(Circle((6.4, 2.15), 0.3, color=MINT)); T(ax, 7.15, 2.15, "Fresh", MINT, 13)
    ax.add_patch(Circle((6.4, 1.45), 0.3, color=YEL)); T(ax, 7.15, 1.45, "Use soon", YEL, 13)
    ax.add_patch(Circle((6.4, 0.75), 0.3, color=COR)); T(ax, 7.15, 0.75, "Spoiled", COR, 13)
    save(f, "sensor.png")

def migration():
    f, ax = fig(7, 3.4)
    ax.add_patch(Rectangle((0.4, 0.5), 1.6, 2.6, fill=False, ec=CH, lw=3)); T(ax, 1.2, 3.3, "Package film", CH, 13, weight="bold")
    for _ in range(18):
        ax.add_patch(Circle((random.uniform(0.6, 1.8), random.uniform(0.7, 2.9)), 0.06, color=YEL))
    ax.add_patch(Rectangle((2.6, 0.5), 2.0, 2.6, fill=False, ec=ORG, lw=3)); T(ax, 3.6, 3.3, "Food", ORG, 13, weight="bold")
    for y in [1.0, 1.8, 2.6]:
        arrow(ax, (1.9, y), (3.0, y), MINT, 2)
        ax.add_patch(Circle((3.25, y), 0.06, color=YEL))
    T(ax, 2.3, 0.2, "diffusion · ion release · abrasion", MINT, 12)
    fs = ["Particle size & dose", "Temperature", "Contact time", "Fatty / acidic food", "Polymer type"]
    T(ax, 5.85, 3.0, "Depends on:", YEL, 13, weight="bold")
    for i, s in enumerate(fs):
        T(ax, 5.0, 2.5 - i * 0.45, "• " + s, CH, 12, ha="left")
    save(f, "migration.png")

def coating():
    f, ax = fig(5.6, 3.6)
    ax.add_patch(Circle((2.4, 1.7), 1.25, fill=False, ec=COR, lw=3.5)); T(ax, 2.4, 1.7, "Fruit", COR, 15)
    ax.add_patch(Circle((2.4, 1.7), 1.45, fill=False, ec=MINT, lw=2.5, ls="--"))
    ax.plot([2.4, 2.5], [2.95, 3.35], color=ORG, lw=3)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        ax.add_patch(Circle((2.4 + 1.45 * math.cos(a), 1.7 + 1.45 * math.sin(a)), 0.07, color=YEL))
    T(ax, 4.7, 3.0, "Edible\nnano-coating", MINT, 13, weight="bold")
    T(ax, 4.7, 1.5, "nano-droplets of\nessential oil /\nantioxidant", YEL, 12)
    T(ax, 4.7, 0.35, "↓ O₂, ↓ moisture loss", CH, 12)
    save(f, "coating.png")

if __name__ == "__main__":
    content_bg(); section_bg(); doodles()
    nano_scale(); sav(); tortuous(); antimicrobial(); structures(); electrospin()
    scavenger(); sensor(); migration(); coating()
    print("done")
