import sys, zipfile, re, collections
from pptx import Presentation
from pptx.util import Emu
p=sys.argv[1]
z=zipfile.ZipFile(p)
th=[n for n in z.namelist() if re.match(r'ppt/theme/theme\d+\.xml',n)]
t=z.read(th[0]).decode('utf8','ignore')
cs=re.search(r'<a:clrScheme.*?</a:clrScheme>',t,re.S).group(0)
print("THEME COLORS:",re.findall(r'<a:(dk1|lt1|dk2|lt2|accent\d|hlink)>.*?(?:val|lastClr)="([0-9A-Fa-f]{6})"',cs,re.S))
print("THEME FONTS:",re.findall(r'<a:(major|minor)Font>\s*<a:latin typeface="([^"]*)"',t))
pr=Presentation(p)
W,H=pr.slide_width,pr.slide_height
print("SIZE in:",round(W/914400,3),round(H/914400,3),"slides:",len(pr.slides))
fonts=collections.Counter();cols=collections.Counter();sizes=collections.Counter()
for i,s in enumerate(pr.slides,1):
    xml=s._element.xml
    for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"',xml): cols[c.upper()]+=1
    kinds=collections.Counter()
    txt=[]
    for sh in s.shapes:
        kinds[sh.shape_type and str(sh.shape_type).split('.')[-1].split(' ')[0] or 'ph']+=1
        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    if r.font.name: fonts[r.font.name]+=1
                    if r.font.size: sizes[round(r.font.size.pt)]+=1
            tx=sh.text_frame.text.strip().replace('\n',' / ')
            if tx: txt.append(tx[:50])
    print(f"S{i}:",dict(kinds),"|",txt[:4])
print("FONTS:",fonts.most_common(8))
print("SIZES:",sorted(sizes.items(),key=lambda x:-x[1])[:10])
print("COLORS:",cols.most_common(12))
