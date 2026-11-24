"""Shared helpers for reading/writing PowerPoint transitions and animations."""
import re, zipfile, posixpath, copy
from lxml import etree

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
    "p15": "http://schemas.microsoft.com/office/powerpoint/2012/main",
    "p159": "http://schemas.microsoft.com/office/powerpoint/2015/09/main",
}
P = "{%s}" % NS["p"]
EMU = 914400.0

# Common preset names (presetClass, presetID). Unknown IDs fall back to behaviour-based descriptions.
PRESETS = {
    ("entr", 1): "Appear", ("entr", 2): "Fly In", ("entr", 3): "Blinds", ("entr", 4): "Box",
    ("entr", 5): "Checkerboard", ("entr", 6): "Circle", ("entr", 8): "Diamond", ("entr", 9): "Dissolve In",
    ("entr", 10): "Fade", ("entr", 12): "Peek In", ("entr", 14): "Random Bars", ("entr", 16): "Split",
    ("entr", 17): "Stretch", ("entr", 18): "Strips", ("entr", 21): "Wheel", ("entr", 22): "Wipe",
    ("entr", 23): "Zoom", ("entr", 26): "Bounce", ("entr", 37): "Rise Up", ("entr", 42): "Float In (Ascend)",
    ("entr", 47): "Float In (Descend)", ("entr", 53): "Fade + Zoom", ("entr", 55): "Expand",
    ("emph", 6): "Grow/Shrink", ("emph", 8): "Spin", ("emph", 9): "Transparency",
    ("exit", 1): "Disappear", ("exit", 2): "Fly Out", ("exit", 10): "Fade", ("exit", 22): "Wipe",
    ("exit", 42): "Float Out", ("exit", 53): "Fade + Zoom",
}
DIRS = {1: "from top", 2: "from right", 4: "from bottom", 8: "from left", 16: "in/center", 32: "out"}


def q(tag):
    pre, local = tag.split(":")
    return "{%s}%s" % (NS[pre], local)


def localname(el):
    return etree.QName(el).localname


def prefix_of(el):
    uri = etree.QName(el).namespace
    for k, v in NS.items():
        if v == uri:
            return k
    return "?"


def slide_names(z):
    """Slide part names in presentation order."""
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    rels = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for sid in pres.find(q("p:sldIdLst")):
        tgt = rmap[sid.get(q("r:id"))]
        out.append(posixpath.normpath(posixpath.join("ppt", tgt)))
    return out


def rels_of(z, part):
    d, f = posixpath.split(part)
    rp = posixpath.join(d, "_rels", f + ".rels")
    if rp not in z.namelist():
        return {}
    rels = etree.fromstring(z.read(rp))
    return {r.get("Id"): posixpath.normpath(posixpath.join(d, r.get("Target"))) for r in rels}


def layout_name(z, slide_part):
    for tgt in rels_of(z, slide_part).values():
        if "slideLayouts/" in tgt:
            lx = etree.fromstring(z.read(tgt))
            c = lx.find(q("p:cSld"))
            return c.get("name") or posixpath.basename(tgt)
    return ""


def shape_info(root, z=None, part=None):
    """Return ordered list of dicts for every addressable shape on the slide."""
    rel = rels_of(z, part) if z is not None else {}
    shapes = []
    tree = root.find(q("p:cSld")).find(q("p:spTree"))
    for el in tree.iter(q("p:sp"), q("p:pic"), q("p:graphicFrame"), q("p:grpSp"), q("p:cxnSp")):
        nv = el.find("./*/" + q("p:cNvPr"))
        if nv is None:
            continue
        kind = localname(el)
        ph = el.find("./*/" + q("p:nvPr") + "/" + q("p:ph"))
        phtype = ph.get("type", "body") if ph is not None else None
        text = " ".join(t.text or "" for t in el.iter(q("a:t"))).strip()
        paras = len(el.findall(".//" + q("a:p"))) if kind == "sp" else 0
        off = el.find(".//" + q("a:off"))
        ext = el.find(".//" + q("a:ext"))
        box = None
        if off is not None and ext is not None and ext.get("cx"):
            box = [int(off.get("x")) / EMU, int(off.get("y")) / EMU, int(ext.get("cx")) / EMU, int(ext.get("cy")) / EMU]
        media = None
        blip = el.find(".//" + q("a:blip"))
        if blip is not None:
            media = rel.get(blip.get(q("r:embed")))
        fill = el.find("./" + q("p:spPr") + "/" + q("a:solidFill") + "/*")
        fillv = fill.get("val") if fill is not None else None
        gf = el.find(".//" + q("a:graphicData"))
        if phtype in ("title", "ctrTitle"):
            role = "title"
        elif phtype == "subTitle":
            role = "subtitle"
        elif phtype in ("sldNum", "dt", "ftr", "hdr"):
            role = "footer"
        elif kind == "pic":
            role = "picture"
        elif kind == "graphicFrame":
            uri = gf.get("uri") if gf is not None else ""
            role = "table" if uri.endswith("/table") else "chart" if "chart" in uri else "object"
        elif kind == "grpSp":
            role = "group"
        elif kind == "cxnSp":
            role = "line"
        elif text:
            role = "text"
        else:
            role = "shape"
        shapes.append(dict(id=nv.get("id"), name=nv.get("name", ""), kind=kind, role=role, text=text[:60],
                           paras=paras, box=box, media=media, fill=fillv, placeholder=phtype,
                           top=el.getparent() is tree))
    return shapes


def find_transition(root):
    """Return (element_to_copy, transition_element) — element_to_copy may be mc:AlternateContent."""
    for ch in root:
        if ch.tag == q("p:transition"):
            return ch, ch
        if ch.tag == q("mc:AlternateContent"):
            tr = ch.find(".//" + q("p:transition"))
            if tr is not None:
                return ch, tr
    return None, None


def describe_transition(wrapper, tr):
    if tr is None:
        return None
    eff = [c for c in tr if localname(c) not in ("sndAc", "extLst")]
    e = eff[0] if eff else None
    d = {
        "effect": f"{prefix_of(e)}:{localname(e)}" if e is not None else "none",
        "options": dict(e.attrib) if e is not None else {},
        "speed": tr.get("spd"),
        "duration_ms": tr.get(q("p14:dur")),
        "advance_on_click": tr.get("advClick", "1") != "0",
        "auto_advance_ms": tr.get("advTm"),
    }
    if wrapper is not None and wrapper.tag == q("mc:AlternateContent"):
        fb = wrapper.find(".//" + q("mc:Fallback") + "/" + q("p:transition"))
        if fb is not None:
            fe = [c for c in fb if localname(c) not in ("sndAc", "extLst")]
            d["fallback"] = localname(fe[0]) if fe else "none"
        ch = wrapper.find(q("mc:Choice"))
        d["requires"] = ch.get("Requires") if ch is not None else None
    return d


def to_str(el):
    return etree.tostring(el, encoding="unicode")


def num(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def behaviours(eff_cTn):
    """Human-readable list of what an effect does, from its behaviour elements."""
    out = []
    for b in eff_cTn.iter():
        ln = localname(b) if isinstance(b.tag, str) else ""
        if ln == "animEffect":
            out.append(f"{b.get('transition', '')} {b.get('filter', '')}".strip())
        elif ln == "animScale":
            by = b.find(q("p:by"))
            out.append("scale" + (f" x{num(by.get('x'))/1000:.0f}%/y{num(by.get('y'))/1000:.0f}%" if by is not None else ""))
        elif ln == "animRot":
            out.append(f"rotate {num(b.get('by'))/60000:.0f}°")
        elif ln == "animMotion":
            out.append(f"motion path {b.get('path', '')[:40]}")
        elif ln == "animClr":
            out.append("colour change")
        elif ln == "anim":
            names = [n.text for n in b.iter(q("p:attrName"))]
            out.append("animate " + "/".join(names))
    return sorted(set(out))


def effect_duration(eff_cTn):
    end = 0
    for c in eff_cTn.iter(q("p:cTn")):
        if c is eff_cTn:
            continue
        d = c.get("dur")
        if d and d.isdigit():
            delay = 0
            cond = c.find(q("p:stCondLst") + "/" + q("p:cond"))
            if cond is not None:
                delay = num(cond.get("delay"))
            end = max(end, delay + int(d))
    return end


def first_delay(cTn):
    cond = cTn.find(q("p:stCondLst") + "/" + q("p:cond"))
    if cond is None:
        return 0
    v = cond.get("delay")
    return None if v == "indefinite" else num(v)


def dedupe_ids(root):
    """Give every duplicated p:cNvPr id a fresh number (later occurrences change). Returns count fixed.
    Duplicate shape ids (a known pptxgenjs issue on slides with many objects) make PowerPoint
    repair the file and make animations hit the wrong shape."""
    seen, dups, mx = set(), [], 0
    for nv in root.iter(q("p:cNvPr")):
        i = int(nv.get("id")); mx = max(mx, i)
        if i in seen: dups.append(nv)
        seen.add(i)
    for nv in dups:
        mx += 1; nv.set("id", str(mx))
    return len(dups)
