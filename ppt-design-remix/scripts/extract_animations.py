"""Reverse-engineer every transition and animation in a .pptx.

Usage:
  python3 extract_animations.py deck.pptx [--json spec.json] [--md report.md]

Prints a readable report (per slide: transition, Morph object pairs, click groups,
each effect with trigger / delay / duration / target) and optionally writes a JSON
"animation spec" that apply_animations.py can replay on another deck.
"""
import sys, json, argparse, zipfile, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx_anim_common import *

TRIG = {"clickEffect": "On Click", "withEffect": "With Previous", "afterEffect": "After Previous"}


def parse_timing(root, shapes):
    by_id = {s["id"]: s for s in shapes}
    role_rank = {}
    counter = {}
    for s in shapes:
        counter[s["role"]] = counter.get(s["role"], 0) + 1
        role_rank[s["id"]] = counter[s["role"]]
    timing = root.find(q("p:timing"))
    result = {"click_groups": [], "interactive": [], "build": {}}
    if timing is None:
        return result
    for b in timing.iter(q("p:bldP"), q("p:bldGraphic"), q("p:bldOleChart"), q("p:bldDgm")):
        result["build"][b.get("spid")] = to_str(b)
    for seq in timing.iter(q("p:seq")):
        top = seq.find(q("p:cTn"))
        kind = top.get("nodeType")
        groups_parent = top.find(q("p:childTnLst"))
        if groups_parent is None:
            continue
        for cg in groups_parent.findall(q("p:par")):
            cg_ctn = cg.find(q("p:cTn"))
            st = cg_ctn.find(q("p:stCondLst"))
            group = {"cond": to_str(st) if st is not None else "", "offsets": []}
            for og in cg_ctn.find(q("p:childTnLst")).findall(q("p:par")):
                og_ctn = og.find(q("p:cTn"))
                off = {"delay": first_delay(og_ctn) or 0, "effects": []}
                for ep in og_ctn.find(q("p:childTnLst")).findall(q("p:par")):
                    e = ep.find(q("p:cTn"))
                    sp = e.find(".//" + q("p:spTgt"))
                    spid = sp.get("spid") if sp is not None else None
                    prg = e.find(".//" + q("p:pRg"))
                    cls, pid, sub = e.get("presetClass"), num(e.get("presetID")), num(e.get("presetSubtype"))
                    tgt = by_id.get(spid, {})
                    it = e.find(q("p:iterate"))
                    off["effects"].append({
                        "trigger": TRIG.get(e.get("nodeType"), e.get("nodeType")),
                        "class": cls, "preset_id": pid, "subtype": sub,
                        "name": PRESETS.get((cls, pid), f"{cls} preset {pid}"),
                        "direction": DIRS.get(sub, "") if sub else "",
                        "delay_ms": off["delay"] + (first_delay(e) or 0),
                        "duration_ms": effect_duration(e),
                        "repeat": e.get("repeatCount"), "auto_reverse": e.get("autoRev") == "1",
                        "iterate": it.get("type") if it is not None else None,
                        "behaviours": behaviours(e),
                        "paragraph": int(prg.get("st")) if prg is not None else None,
                        "target": {"spid": spid, "name": tgt.get("name"), "role": tgt.get("role"),
                                   "role_rank": role_rank.get(spid), "text": tgt.get("text")},
                        "xml": to_str(ep),
                    })
                group["offsets"].append(off)
            if kind == "interactiveSeq":
                trig = seq.find(".//" + q("p:nextCondLst"))
                group["trigger_shape"] = None
                c = top.find(q("p:stCondLst") + "//" + q("p:spTgt"))
                if c is not None:
                    group["trigger_shape"] = by_id.get(c.get("spid"), {}).get("name")
                result["interactive"].append(group)
            else:
                result["click_groups"].append(group)
    return result


def morph_pairs(prev, cur):
    """Explain what a Morph transition animates between two slides."""
    pairs, used = [], set()
    def key_name(s):
        return s["name"][2:] if s["name"].startswith("!!") else s["name"]
    for c in cur:
        if c["role"] == "footer" or not c["top"]:
            continue
        match = None
        for p in prev:
            if p["id"] in used or not p["top"]:
                continue
            if key_name(p) == key_name(c) and (c["name"].startswith("!!") or p["kind"] == c["kind"]):
                if c["media"] and p["media"] and c["media"] != p["media"] and not c["name"].startswith("!!"):
                    continue
                match = p; break
        if match is None and c["media"]:
            match = next((p for p in prev if p["id"] not in used and p["media"] == c["media"]), None)
        if match is None and c["text"]:
            match = next((p for p in prev if p["id"] not in used and p["text"] == c["text"] and p["kind"] == c["kind"]), None)
        if match is None:
            pairs.append({"shape": c["name"], "id": c["id"], "change": "fades in (new on this slide)"})
            continue
        used.add(match["id"])
        ch = []
        if match["box"] and c["box"]:
            dx, dy = c["box"][0] - match["box"][0], c["box"][1] - match["box"][1]
            sx = c["box"][2] / match["box"][2] if match["box"][2] else 1
            sy = c["box"][3] / match["box"][3] if match["box"][3] else 1
            if abs(dx) > 0.05 or abs(dy) > 0.05:
                ch.append(f"moves {dx:+.2f}in, {dy:+.2f}in")
            if abs(sx - 1) > 0.03 or abs(sy - 1) > 0.03:
                ch.append(f"resizes x{sx:.2f} / y{sy:.2f}")
        if match["fill"] != c["fill"]:
            ch.append(f"recolours {match['fill']}→{c['fill']}")
        if match["text"] != c["text"]:
            ch.append("text changes")
        pairs.append({"shape": c["name"], "id": c["id"], "from": match["name"], "from_id": match["id"], "change": ", ".join(ch) or "stays"})
    for p in prev:
        if p["id"] not in used and p["top"] and p["role"] != "footer":
            pairs.append({"shape": p["name"], "change": "fades out (gone on this slide)"})
    return pairs


def extract(path):
    z = zipfile.ZipFile(path)
    spec = {"source": os.path.basename(path), "slides": []}
    prev_shapes = None
    for i, part in enumerate(slide_names(z), 1):
        root = etree.fromstring(z.read(part))
        ids = [nv.get("id") for nv in root.iter(q("p:cNvPr"))]
        dup = sorted({i for i in ids if ids.count(i) > 1})
        shapes = shape_info(root, z, part)
        wrap, tr = find_transition(root)
        t = describe_transition(wrap, tr)
        s = {"index": i, "part": part, "layout": layout_name(z, part), "transition": t,
             "transition_xml": to_str(wrap) if wrap is not None else None,
             "duplicate_ids": dup,
             "shapes": [{k: v for k, v in sh.items() if k in ("id", "name", "role", "kind", "paras", "text")} for sh in shapes]}
        s.update(parse_timing(root, shapes))
        if t and "morph" in t["effect"] and prev_shapes is not None:
            s["morph"] = morph_pairs(prev_shapes, shapes)
        spec["slides"].append(s)
        prev_shapes = shapes
    return spec


def report(spec):
    L = [f"# Animation report: {spec['source']}", ""]
    n_tr = sum(1 for s in spec["slides"] if s["transition"])
    n_fx = sum(len(e["effects"]) for s in spec["slides"] for g in s["click_groups"] for e in g["offsets"])
    L.append(f"{len(spec['slides'])} slides · {n_tr} with transitions · {n_fx} animation effects\n")
    for s in spec["slides"]:
        t = s["transition"]
        tdesc = "none"
        if t:
            tdesc = t["effect"] + (f" {t['options']}" if t["options"] else "") + f", speed {t['speed'] or 'default'}"
            if t.get("duration_ms"): tdesc += f", {t['duration_ms']} ms"
            if t.get("fallback"): tdesc += f" (fallback: {t['fallback']}, needs {t.get('requires')})"
            if t.get("auto_advance_ms"): tdesc += f", auto-advance {t['auto_advance_ms']} ms"
        L.append(f"## Slide {s['index']}  ·  layout: {s['layout']}")
        L.append(f"- **Transition:** {tdesc}")
        if s.get("duplicate_ids"):
            L.append(f"- ⚠️ **Duplicate shape ids {s['duplicate_ids']}**: PowerPoint may repair this file and animations can hit the wrong shape. apply_animations.py fixes ids in the target.")
        if s.get("morph"):
            L.append("- **Morph pairs:**")
            for m in s["morph"]:
                L.append(f"  - {m['shape']}" + (f" ← {m['from']}" if m.get("from") else "") + f": {m['change']}")
        for gi, g in enumerate(s["click_groups"], 1):
            auto = "onBegin" in g["cond"]
            L.append(f"- **Step {gi}** ({'starts automatically' if auto else 'on click'}):")
            for o in g["offsets"]:
                for e in o["effects"]:
                    tg = e["target"]
                    who = f"{tg['name']} [{tg['role']}]" + (f" ¶{e['paragraph']}" if e["paragraph"] is not None else "")
                    extra = f" {e['direction']}" if e["direction"] else ""
                    if e["iterate"]: extra += f", by {e['iterate']}"
                    if e["repeat"]: extra += f", repeat {e['repeat']}"
                    L.append(f"  - {e['class']}: **{e['name']}**{extra} → {who} · {e['trigger']} · start {e['delay_ms']} ms · {e['duration_ms']} ms · {', '.join(e['behaviours'])}")
        for g in s["interactive"]:
            L.append(f"- **Trigger animation** on click of {g.get('trigger_shape')}: {sum(len(o['effects']) for o in g['offsets'])} effects")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx"); ap.add_argument("--json"); ap.add_argument("--md")
    a = ap.parse_args()
    spec = extract(a.pptx)
    md = report(spec)
    if a.json:
        json.dump(spec, open(a.json, "w"), indent=1, ensure_ascii=False)
    if a.md:
        open(a.md, "w").write(md)
    print(md)
