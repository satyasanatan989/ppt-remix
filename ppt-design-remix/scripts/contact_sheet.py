import sys,glob
from PIL import Image
pre,out=sys.argv[1],sys.argv[2]
fs=sorted(glob.glob(pre+'*.png'))
ims=[Image.open(f) for f in fs]
w,h=ims[0].size;c=4;r=(len(ims)+c-1)//c
S=Image.new('RGB',(c*w,r*h),'white')
for i,im in enumerate(ims): S.paste(im,((i%c)*w,(i//c)*h))
S.save(out);print(out,S.size)
