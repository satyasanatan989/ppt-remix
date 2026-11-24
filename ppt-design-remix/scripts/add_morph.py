"""Add (or restore) Morph transitions and force the right object pairs.

Usage: python3 add_morph.py in.pptx out.pptx [--dur 2000] [--from-slide 2] [--no-names]

1. Puts a Morph (byObject) transition, with a Fade fallback for old PowerPoint, on every slide from --from-slide.
2. Works out which object on slide N continues an object on slide N-1 (same name, same image file or same text)
   and renames each chain to a shared '!!m<k>' name, so PowerPoint pairs exactly those objects.
   Use --no-names to leave the names alone.
"""
import sys, os, argparse, zipfile, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_anim_common import *
from extract_animations import morph_pairs

MORPH = ('<mc:AlternateContent xmlns:mc="{mc}"><mc:Choice xmlns:p159="{p159}" Requires="p159">'
         '<p:transition xmlns:p="{p}" xmlns:p14="{p14}" spd="slow" p14:dur="{dur}"><p159:morph option="byObject"/></p:transition>'
         '</mc:Choice><mc:Fallback><p:transition xmlns:p="{p}" spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--dur", type=int, default=2000); ap.add_argument("--from-slide", type=int, default=2)
ap.add_argument("--no-names", action="store_true")
o = ap.parse_args()
z = zipfile.ZipFile(o.src); tmp = tempfile.mkdtemp(); z.extractall(tmp)
parts = slide_names(z); roots = []
for part in parts:
    r = etree.parse(os.path.join(tmp, part)).getroot(); dedupe_ids(r); roots.append(r)
chains = 0; renamed = 0
if not o.no_names:
    token = {}  # (slide_index, shape_id) -> chain name
    prev = None
    for i, (part, r) in enumerate(zip(parts, roots)):
        cur = shape_info(r, z, part)
        if prev is not None and i + 1 >= o.from_slide:
            for pr in morph_pairs(prev, cur):
                if pr.get("from_id"):
                    t = token.get((i - 1, pr["from_id"]))
                    if t is None:
                        chains += 1; t = f"!!m{chains}"; token[(i - 1, pr["from_id"])] = t
                    token[(i, pr["id"])] = t
        prev = cur
    for (i, sid), t in token.items():
        for nv in roots[i].iter(q("p:cNvPr")):
            if nv.get("id") == sid:
                nv.set("name", t); renamed += 1
for i, (part, r) in enumerate(zip(parts, roots), 1):
    for ch in list(r):
        if ch.tag == q("p:transition") or (ch.tag == q("mc:AlternateContent") and ch.find(".//" + q("p:transition")) is not None):
            r.remove(ch)
    if i >= o.from_slide:
        a = r.find(q("p:clrMapOvr"))
        if a is None: a = r.find(q("p:cSld"))
        r.insert(list(r).index(a) + 1, etree.fromstring(MORPH.format(dur=o.dur, **NS)))
    etree.ElementTree(r).write(os.path.join(tmp, part), xml_declaration=True, encoding="UTF-8", standalone=True)
names = sorted(z.namelist(), key=lambda n: n != "[Content_Types].xml")
with zipfile.ZipFile(o.out, "w", zipfile.ZIP_DEFLATED) as zo:
    for n in names:
        if not n.endswith("/"): zo.write(os.path.join(tmp, n), n)
shutil.rmtree(tmp)
print(f"Morph on slides {o.from_slide}-{len(parts)}; {chains} object chains, {renamed} shapes renamed to !!m<k>.")
