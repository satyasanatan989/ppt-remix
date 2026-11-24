"""Add slide transitions + entrance animations to an unzipped .pptx.

Usage:
  mkdir ux && cd ux && unzip ../deck.pptx && cd ..
  python3 animate.py ux
  cd ux && zip -qXrD ../deck_animated.pptx '[Content_Types].xml' _rels docProps ppt

Shapes are grouped by their objectName prefix (set via pptxgenjs objectName):
  group leaders: card, bullets, diagram, table, note, doodle, videoBtn, timeline, dot, ...
  followers (animate WITH the previous leader): icon, cardHead, cardBody, secNum, ...
'bullets' and 'videoList' text boxes animate paragraph by paragraph.
Title / slide-number placeholders are skipped (they appear with the slide).
Section slides (big 0N number, no contents circles) get a Push-up transition; others Fade.
"""
import re, sys, glob, os

D = sys.argv[1]
FOLLOW = ("icon", "cardHead", "cardBody", "secNum", "secName", "evoHead", "evoBody",
          "foodIcon", "foodLabel", "cNumT", "cText")
SKIP = re.compile(r"^(|Text \d+|Slide Number.*)$")

class Ids:
    def __init__(self): self.n = 2
    def next(self):
        self.n += 1; return self.n

def tgt(spid, para=None):
    if para is None:
        return f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
    return f'<p:tgtEl><p:spTgt spid="{spid}"><p:txEl><p:pRg st="{para}" end="{para}"/></p:txEl></p:spTgt></p:tgtEl>'

def vis(ids, spid, para):
    return (f'<p:set><p:cBhvr><p:cTn id="{ids.next()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'{tgt(spid, para)}<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>')

def fadefx(ids, spid, para, dur):
    return (f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{ids.next()}" dur="{dur}"/>'
            f'{tgt(spid, para)}</p:cBhvr></p:animEffect>')

def move(ids, spid, para, attr, frm, to, dur):
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="{ids.next()}" dur="{dur}" fill="hold"/>'
            f'{tgt(spid, para)}<p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{frm}"/></p:val></p:tav>'
            f'<p:tav tm="100000"><p:val><p:strVal val="{to}"/></p:val></p:tav></p:tavLst></p:anim>')

def wipefx(ids, spid, para, dur, d="left"):
    return (f'<p:animEffect transition="in" filter="wipe({d})"><p:cBhvr><p:cTn id="{ids.next()}" dur="{dur}"/>'
            f'{tgt(spid, para)}</p:cBhvr></p:animEffect>')

def effect(ids, kind, spid, node, para=None, dur=500):
    cid = ids.next()
    if kind == "fade":
        preset, sub, body = 10, 0, fadefx(ids, spid, para, dur)
    elif kind == "float":  # Float In (up)
        preset, sub = 42, 0
        body = (fadefx(ids, spid, para, dur) + move(ids, spid, para, "ppt_x", "#ppt_x", "#ppt_x", dur)
                + move(ids, spid, para, "ppt_y", "#ppt_y+.1", "#ppt_y", dur))
    elif kind == "wipe":
        preset, sub, body = 22, 8, wipefx(ids, spid, para, dur)
    elif kind == "zoom":  # Fade + grow
        preset, sub = 53, 16
        body = (move(ids, spid, para, "ppt_w", "0", "#ppt_w", dur) + move(ids, spid, para, "ppt_h", "0", "#ppt_h", dur)
                + fadefx(ids, spid, para, dur))
    grp = ' grpId="0"'
    return (f'<p:par><p:cTn id="{cid}" presetID="{preset}" presetClass="entr" presetSubtype="{sub}" fill="hold"{grp} nodeType="{node}">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{vis(ids, spid, para)}{body}</p:childTnLst></p:cTn></p:par>')

def kind_for(name):
    base = name.rsplit("_", 1)[0]
    return {
        "diagram": ("fade", 800), "doodle": ("zoom", 600), "bullets": ("float", 450), "card": ("float", 500),
        "table": ("fade", 700), "note": ("fade", 600), "videoBtn": ("fade", 500), "timeline": ("wipe", 900),
        "dot": ("zoom", 400), "secCircle": ("zoom", 450), "foodCircle": ("zoom", 450), "cNum": ("float", 450),
        "kicker": ("fade", 600), "deckTitle": ("float", 800), "deckSubtitle": ("fade", 600), "presenter": ("fade", 600),
        "thanks": ("zoom", 800), "qna": ("fade", 600), "formula": ("fade", 600), "limits": ("float", 600),
        "videoList": ("float", 350), "refs": ("fade", 700),
    }.get(base, ("fade", 500))

PARA_SPLIT = {"bullets", "videoList"}

def build(xml):
    shapes = re.findall(r'<p:(sp|pic|graphicFrame)>.*?<p:cNvPr id="(\d+)" name="([^"]*)"', xml)
    # paragraph counts per shape id
    groups = []
    for tag, spid, name in shapes:
        if SKIP.match(name): continue
        base = name.rsplit("_", 1)[0]
        if base in FOLLOW and groups:
            groups[-1]["members"].append((spid, name, tag))
        else:
            groups.append({"members": [(spid, name, tag)]})
    if not groups: return None
    ids = Ids(); t = 200; pars = []; bld = []
    for g in groups:
        lead_spid, lead_name, lead_tag = g["members"][0]
        k, dur = kind_for(lead_name)
        base = lead_name.rsplit("_", 1)[0]
        if base in PARA_SPLIT:
            m = re.search(rf'<p:cNvPr id="{lead_spid}" name="{re.escape(lead_name)}".*?</p:sp>', xml, re.S)
            n = len(re.findall(r"<a:p>|<a:p ", m.group(0)))
            for i in range(n):
                fx = effect(ids, k, lead_spid, "afterEffect", para=i, dur=dur)
                pars.append(f'<p:par><p:cTn id="{ids.next()}" fill="hold"><p:stCondLst><p:cond delay="{t}"/></p:stCondLst><p:childTnLst>{fx}</p:childTnLst></p:cTn></p:par>')
                t += int(dur * 0.75)
            bld.append(f'<p:bldP spid="{lead_spid}" grpId="0" build="p"/>')
            continue
        fxs = []
        for j, (spid, name, tag) in enumerate(g["members"]):
            kk, dd = (k, dur) if j == 0 else ("fade", dur)
            fxs.append(effect(ids, kk, spid, "afterEffect" if j == 0 else "withEffect", dur=dd))
            if tag == "sp":
                fill = ' animBg="1"'
                bld.append(f'<p:bldP spid="{spid}" grpId="0"{fill}/>')
        pars.append(f'<p:par><p:cTn id="{ids.next()}" fill="hold"><p:stCondLst><p:cond delay="{t}"/></p:stCondLst><p:childTnLst>{"".join(fxs)}</p:childTnLst></p:cTn></p:par>')
        t += int(dur * 0.7)
    inner = "".join(pars)
    timing = (
        '<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
        '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
        f'<p:par><p:cTn id="{ids.next()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
        '<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst>'
        f'<p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par>'
        '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
        '</p:childTnLst></p:cTn></p:par></p:tnLst>'
        + (f'<p:bldLst>{"".join(bld)}</p:bldLst>' if bld else "") + '</p:timing>')
    return timing

files = sorted(glob.glob(os.path.join(D, "ppt/slides/slide*.xml")), key=lambda p: int(re.findall(r"\d+", os.path.basename(p))[0]))
for f in files:
    xml = open(f, encoding="utf8").read()
    xml = re.sub(r"<p:transition.*?</p:transition>|<p:transition[^>]*/>", "", xml, flags=re.S)
    xml = re.sub(r"<p:timing>.*?</p:timing>", "", xml, flags=re.S)
    trans = '<p:transition spd="slow"><p:fade/></p:transition>'
    # section slides use the section layout; detect via the section placeholder text pattern (two-digit number)
    if re.search(r"<a:t>0\d</a:t>", xml) and "secCircle" not in xml:
        trans = '<p:transition spd="slow"><p:push dir="u"/></p:transition>'
    timing = build(xml) or ""
    xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + trans + timing, 1)
    open(f, "w", encoding="utf8").write(xml)
    print(os.path.basename(f), "push" if "push" in trans else "fade", xml.count('presetClass="entr"'))
