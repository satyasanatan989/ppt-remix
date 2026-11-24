"""Fix duplicate shape ids in every slide of a .pptx (in place or to a new file).
Usage: python3 fix_shape_ids.py in.pptx [out.pptx]"""
import sys, os, zipfile, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_anim_common import *
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else src
z = zipfile.ZipFile(src); tmp = tempfile.mkdtemp(); z.extractall(tmp); total = 0
for part in slide_names(z):
    p = os.path.join(tmp, part); root = etree.parse(p).getroot(); n = dedupe_ids(root)
    if n:
        total += n; etree.ElementTree(root).write(p, xml_declaration=True, encoding="UTF-8", standalone=True)
names = sorted(z.namelist(), key=lambda n: n != "[Content_Types].xml"); z.close()
tmpout = out + ".tmp"
with zipfile.ZipFile(tmpout, "w", zipfile.ZIP_DEFLATED) as zo:
    for n in names:
        if not n.endswith("/"): zo.write(os.path.join(tmp, n), n)
os.replace(tmpout, out); shutil.rmtree(tmp)
print(f"fixed {total} duplicate ids -> {out}")
