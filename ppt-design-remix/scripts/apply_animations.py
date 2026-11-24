"""Replay an animation spec (from extract_animations.py) onto another .pptx.

Usage:
  python3 apply_animations.py target.pptx spec.json out.pptx [options]

Slide mapping (which source slide's animations go on which target slide):
  --map index           target slide N gets source slide N (default; extra target slides use --recipe if given)
  --map layout          match by layout name, else --recipe
  --recipe N            use source slide N's animations as a recipe for every unmatched slide
                        (or for every slide with --map recipe)
  --map recipe          every target slide uses --recipe
  --map style           learn the source deck's STYLE (effect per element role, step gap, auto/click,
                        most common transition) and apply it to every slide of any deck, whatever its layout
Shape mapping inside a slide (source effect target -> target shape):
  1. same shape name, 2. next unused shape with the same role (title/text/picture/table/shape/group...),
  3. with --loose, any unused animatable shape.
Other options:
  --transitions-only / --animations-only
  --transition-from N   use source slide N's transition on every target slide
  --skip-title          never animate title placeholders (keeps titles static, like most pro decks)
"""
import sys, os, json, re, argparse, zipfile, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_anim_common import *

NSDECL = " ".join(f'xmlns:{k}="{v}"' for k, v in NS.items())


def parse_frag(xml):
    """Parse an XML fragment that may use any of our namespace prefixes."""
    wrapped = f"<root {NSDECL}>{xml}</root>"
    return etree.fromstring(wrapped)[0]


def renumber(el, counter):
    for c in el.iter(q("p:cTn")):
        counter[0] += 1
        c.set("id", str(counter[0]))


def build_timing(groups, counter):
    """groups: list of {cond, offsets:[{delay, effects:[xml...]}]} -> p:timing element (no bldLst)."""
    tm = etree.SubElement(etree.Element("x"), q("p:timing"))
    tn = etree.SubElement(tm, q("p:tnLst"))
    par = etree.SubElement(tn, q("p:par"))
    root = etree.SubElement(par, q("p:cTn"), id="1", dur="indefinite", restart="never", nodeType="tmRoot")
    rc = etree.SubElement(root, q("p:childTnLst"))
    seq = etree.SubElement(rc, q("p:seq"), concurrent="1", nextAc="seek")
    main = etree.SubElement(seq, q("p:cTn"), id="2", dur="indefinite", nodeType="mainSeq")
    mc = etree.SubElement(main, q("p:childTnLst"))
    counter[0] = 2
    for g in groups:
        gp = etree.SubElement(mc, q("p:par"))
        counter[0] += 1
        gc = etree.SubElement(gp, q("p:cTn"), id=str(counter[0]), fill="hold")
        if g["cond"]:
            gc.append(parse_frag(g["cond"]))
        else:
            sl = etree.SubElement(gc, q("p:stCondLst")); etree.SubElement(sl, q("p:cond"), delay="indefinite")
        gl = etree.SubElement(gc, q("p:childTnLst"))
        for o in g["offsets"]:
            op = etree.SubElement(gl, q("p:par"))
            counter[0] += 1
            oc = etree.SubElement(op, q("p:cTn"), id=str(counter[0]), fill="hold")
            sl = etree.SubElement(oc, q("p:stCondLst")); etree.SubElement(sl, q("p:cond"), delay=str(o["delay"]))
            ol = etree.SubElement(oc, q("p:childTnLst"))
            for ex in o["effects"]:
                ol.append(ex)
    prev = etree.SubElement(seq, q("p:prevCondLst"))
    c = etree.SubElement(prev, q("p:cond"), evt="onPrev", delay="0"); t = etree.SubElement(c, q("p:tgtEl")); etree.SubElement(t, q("p:sldTgt"))
    nxt = etree.SubElement(seq, q("p:nextCondLst"))
    c = etree.SubElement(nxt, q("p:cond"), evt="onNext", delay="0"); t = etree.SubElement(c, q("p:tgtEl")); etree.SubElement(t, q("p:sldTgt"))
    return tm


def map_shapes(src_slide, tgt_shapes, loose, skip_title):
    src_by_id = {s["id"]: s for s in src_slide["shapes"]}
    used, mapping = set(), {}
    animatable = [s for s in tgt_shapes if s["role"] != "footer" and not (skip_title and s["role"] == "title")]
    needed = []
    for g in src_slide["click_groups"]:
        for o in g["offsets"]:
            for e in o["effects"]:
                sid = e["target"]["spid"]
                if sid and sid not in needed:
                    needed.append(sid)
    for sid in needed:  # pass 1: exact name
        s = src_by_id.get(sid)
        if not s: continue
        m = next((t for t in animatable if t["id"] not in used and t["name"] == s["name"] and t["role"] == s["role"]), None)
        if m: mapping[sid] = m; used.add(m["id"])
    for sid in needed:  # pass 2: role order
        if sid in mapping: continue
        s = src_by_id.get(sid)
        if not s: continue
        m = next((t for t in animatable if t["id"] not in used and t["role"] == s["role"]), None)
        if m is None and s["role"] in ("text", "shape") :
            alt = "shape" if s["role"] == "text" else "text"
            m = next((t for t in animatable if t["id"] not in used and t["role"] == alt), None)
        if m is None and loose:
            m = next((t for t in animatable if t["id"] not in used), None)
        if m: mapping[sid] = m; used.add(m["id"])
    return mapping


def retarget(effect_xml, old, new):
    el = parse_frag(effect_xml)
    for sp in el.iter(q("p:spTgt")):
        if sp.get("spid") == old:
            sp.set("spid", new)
    return el


def apply_slide(root, src, tgt_shapes, opts, stats, trans_src):
    # --- remove existing transition / timing
    for ch in list(root):
        if ch.tag in (q("p:transition"), q("p:timing")):
            root.remove(ch)
        elif ch.tag == q("mc:AlternateContent") and ch.find(".//" + q("p:transition")) is not None:
            root.remove(ch)
    anchor = root.find(q("p:clrMapOvr"))
    if anchor is None:
        anchor = root.find(q("p:cSld"))
    pos = list(root).index(anchor) + 1
    # --- transition
    if not opts.animations_only and trans_src and trans_src.get("transition_xml"):
        root.insert(pos, parse_frag(trans_src["transition_xml"])); pos += 1
        stats["transitions"] += 1
    if opts.transitions_only or not src or not src["click_groups"]:
        return
    mapping = map_shapes(src, tgt_shapes, opts.loose, opts.skip_title)
    tparas = {s["id"]: s["paras"] for s in tgt_shapes}
    groups = []
    bld = {}
    for g in src["click_groups"]:
        ng = {"cond": g["cond"], "offsets": []}
        for o in g["offsets"]:
            effs = []
            for e in o["effects"]:
                sid = e["target"]["spid"]
                if sid not in mapping:
                    stats["skipped"] += 1; continue
                t = mapping[sid]
                if e["paragraph"] is not None and e["paragraph"] >= max(tparas.get(t["id"], 0), 1):
                    stats["skipped"] += 1; continue
                effs.append(retarget(e["xml"], sid, t["id"]))
                stats["effects"] += 1
                if t["kind"] in ("sp",):
                    b = src.get("build", {}).get(sid)
                    if b:
                        be = parse_frag(b); be.set("spid", t["id"]); bld[t["id"]] = be
                    elif t["id"] not in bld:
                        be = etree.Element(q("p:bldP"), spid=t["id"], grpId="0"); bld[t["id"]] = be
            if effs:
                ng["offsets"].append({"delay": o["delay"], "effects": effs})
        if ng["offsets"]:
            groups.append(ng)
    if not groups:
        return
    # first group: if source started automatically keep it; make sure the chain is valid
    counter = [0]
    tm = build_timing(groups, counter)
    # renumber every effect cTn after the fixed root/mainSeq ids
    n = [2]
    for c in tm.iter(q("p:cTn")):
        if c.get("nodeType") in ("tmRoot", "mainSeq"):
            continue
        n[0] += 1; c.set("id", str(n[0]))
    # grpId: keep the source's but ensure the bldP grpId matches the effect grpIds used per shape
    if bld:
        bl = etree.SubElement(tm, q("p:bldLst"))
        for spid, be in bld.items():
            gids = {e.getparent().getparent().get("grpId") for e in tm.iter(q("p:spTgt")) if e.get("spid") == spid}
            gids.discard(None)
            if gids:
                be.set("grpId", sorted(gids)[0])
            bl.append(be)
    root.insert(pos, tm)
    stats["slides_animated"] += 1


def learn_style(spec):
    """Summarise a deck's animation style: per role -> example effect, gap between steps, auto/click, transition."""
    from collections import Counter, defaultdict
    ex, cnt, para_roles, gaps, autos, trans = {}, defaultdict(Counter), Counter(), [], Counter(), Counter()
    for s in spec["slides"]:
        if s.get("transition_xml"):
            trans[s["transition_xml"]] += 1
        for g in s["click_groups"]:
            autos["auto" if "onBegin" in g["cond"] else "click"] += 1
            ds = [o["delay"] for o in g["offsets"]]
            gaps += [b - a for a, b in zip(ds, ds[1:]) if b > a]
            for o in g["offsets"]:
                for e in o["effects"]:
                    if e["trigger"] == "With Previous" or e["class"] != "entr":
                        continue
                    role = e["target"]["role"] or "shape"
                    k = (e["class"], e["preset_id"], e["subtype"], e["paragraph"] is not None)
                    cnt[role][k] += 1
                    ex.setdefault((role, k), e)
                    if e["paragraph"] is not None:
                        para_roles[role] += 1
    style = {"roles": {}, "gap": sorted(gaps)[len(gaps) // 2] if gaps else 400,
             "auto": autos["auto"] >= autos["click"],
             "transition_xml": trans.most_common(1)[0][0] if trans else None}
    for role, c in cnt.items():
        k = c.most_common(1)[0][0]
        style["roles"][role] = ex[(role, k)]
    return style


def style_slide(root, shapes, style, opts, stats, slide_area=None):
    for ch in list(root):
        if ch.tag in (q("p:transition"), q("p:timing")) or (ch.tag == q("mc:AlternateContent") and ch.find(".//" + q("p:transition")) is not None):
            root.remove(ch)
    anchor = root.find(q("p:clrMapOvr"))
    if anchor is None:
        anchor = root.find(q("p:cSld"))
    pos = list(root).index(anchor) + 1
    if not opts.animations_only and style["transition_xml"]:
        root.insert(pos, parse_frag(style["transition_xml"])); pos += 1; stats["transitions"] += 1
    if opts.transitions_only:
        return
    fallback = style["roles"].get("text") or style["roles"].get("shape") or next(iter(style["roles"].values()), None)
    if fallback is None:
        return
    offsets, bld, t = [], {}, 200
    for sh in shapes:
        if slide_area and sh["box"] and sh["box"][2] * sh["box"][3] >= 0.5 * slide_area:
            continue  # backgrounds / full-bleed frames stay static
        if not sh["top"] or sh["role"] == "footer" or (opts.skip_title and sh["role"] in ("title", "subtitle") and sh["placeholder"]):
            continue
        ex = style["roles"].get(sh["role"]) or (fallback if opts.loose or sh["role"] in ("text", "shape", "picture", "group", "table", "chart") else None)
        if ex is None:
            continue
        old = ex["target"]["spid"]
        paras = range(sh["paras"]) if (ex["paragraph"] is not None and sh["paras"] > 1) else [None]
        for pi in paras:
            el = retarget(ex["xml"], old, sh["id"])
            for prg in el.iter(q("p:pRg")):
                if pi is None:
                    tx = prg.getparent(); tx.getparent().remove(tx)
                else:
                    prg.set("st", str(pi)); prg.set("end", str(pi))
            if pi is not None and el.find(".//" + q("p:pRg")) is None:
                for sp in el.iter(q("p:spTgt")):
                    tx = etree.SubElement(sp, q("p:txEl")); etree.SubElement(tx, q("p:pRg"), st=str(pi), end=str(pi))
            c = el.find(q("p:cTn")); c.set("nodeType", "afterEffect")
            offsets.append({"delay": t, "effects": [el]}); t += style["gap"]
            stats["effects"] += 1
        if sh["kind"] == "sp":
            be = etree.Element(q("p:bldP"), spid=sh["id"], grpId="0")
            if paras != [None]: be.set("build", "p")
            bld[sh["id"]] = be
    if not offsets:
        return
    cond = ('<p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst>'
            if style["auto"] else '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>')
    tm = build_timing([{"cond": cond, "offsets": offsets}], [0])
    n = 2
    for c in tm.iter(q("p:cTn")):
        if c.get("nodeType") in ("tmRoot", "mainSeq"): continue
        n += 1; c.set("id", str(n))
    for c in tm.iter(q("p:cTn")):
        if c.get("presetClass"): c.set("grpId", "0")
    if bld:
        bl = etree.SubElement(tm, q("p:bldLst"))
        for be in bld.values(): bl.append(be)
    root.insert(pos, tm); stats["slides_animated"] += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target"); ap.add_argument("spec"); ap.add_argument("out")
    ap.add_argument("--map", default="index", choices=["index", "layout", "recipe", "style"])
    ap.add_argument("--recipe", type=int)
    ap.add_argument("--transition-from", type=int)
    ap.add_argument("--transitions-only", action="store_true")
    ap.add_argument("--animations-only", action="store_true")
    ap.add_argument("--loose", action="store_true")
    ap.add_argument("--skip-title", action="store_true")
    o = ap.parse_args()
    spec = json.load(open(o.spec))
    src = {s["index"]: s for s in spec["slides"]}
    by_layout = {}
    for s in spec["slides"]:
        by_layout.setdefault(s["layout"], s)
    recipe = src.get(o.recipe) if o.recipe else None
    tfrom = src.get(o.transition_from) if o.transition_from else None

    style = learn_style(spec) if o.map == "style" else None
    if style:
        print("Learned style:", {r: f"{e['name']} {e['direction']}".strip() + (" (by paragraph)" if e['paragraph'] is not None else "") for r, e in style["roles"].items()},
              f"gap {style['gap']} ms,", "auto-play" if style["auto"] else "on click")
    tmp = tempfile.mkdtemp()
    zin = zipfile.ZipFile(o.target)
    sz = etree.fromstring(zin.read("ppt/presentation.xml")).find(q("p:sldSz"))
    slide_area = int(sz.get("cx")) / EMU * int(sz.get("cy")) / EMU
    zin.extractall(tmp)
    stats = dict(transitions=0, effects=0, skipped=0, slides_animated=0)
    lines = []
    for i, part in enumerate(slide_names(zin), 1):
        p = os.path.join(tmp, part)
        root = etree.parse(p).getroot()
        fixed = dedupe_ids(root)
        if fixed:
            stats["ids_fixed"] = stats.get("ids_fixed", 0) + fixed
        shapes = shape_info(root, zin, part)
        if style:
            before = stats["effects"]
            style_slide(root, shapes, style, o, stats, slide_area)
            lines.append(f"slide {i}: style · {stats['effects'] - before} effects")
            etree.ElementTree(root).write(p, xml_declaration=True, encoding="UTF-8", standalone=True)
            continue
        if o.map == "index":
            s = src.get(i) or recipe
        elif o.map == "layout":
            s = by_layout.get(layout_name(zin, part)) or recipe
        else:
            s = recipe
        before = stats["effects"]
        apply_slide(root, s, shapes, o, stats, tfrom or s)
        lines.append(f"slide {i}: from source slide {s['index'] if s else '-'} · {stats['effects'] - before} effects")
        etree.ElementTree(root).write(p, xml_declaration=True, encoding="UTF-8", standalone=True)
    # repack (no directory entries; [Content_Types].xml first)
    if os.path.exists(o.out): os.remove(o.out)
    with zipfile.ZipFile(o.out, "w", zipfile.ZIP_DEFLATED) as zout:
        names = zin.namelist()
        names.sort(key=lambda n: n != "[Content_Types].xml")
        for n in names:
            if n.endswith("/"): continue
            zout.write(os.path.join(tmp, n), n)
    shutil.rmtree(tmp)
    print("\n".join(lines))
    if stats.get("ids_fixed"):
        print(f"Fixed {stats['ids_fixed']} duplicate shape ids in the target (would otherwise trigger PowerPoint repair).")
    print(f"\nDone: {stats['transitions']} transitions, {stats['effects']} effects applied on {stats['slides_animated']} slides, {stats['skipped']} effects skipped (no matching shape).")


if __name__ == "__main__":
    main()
