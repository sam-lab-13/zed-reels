import numpy as np, sys
from PIL import Image
from scipy import ndimage
src=sys.argv[1]; out=sys.argv[2]
im=np.array(Image.open(src).convert('RGB')).astype(int)
r,g,b=im[...,0],im[...,1],im[...,2]
green=(g>150)&(g>r+60)&(g>b+60)
fg=~green
fg=ndimage.binary_opening(fg,iterations=1)
lab,n=ndimage.label(fg)
objs=ndimage.find_objects(lab)
import os; os.makedirs(out,exist_ok=True)
res=[]
for i,sl in enumerate(objs):
    area=(lab[sl]==i+1).sum()
    if area<2000: continue
    res.append((sl,i+1,area))
for sl,idx,area in res:
    y0,y1=sl[0].start,sl[0].stop; x0,x1=sl[1].start,sl[1].stop
    print(idx,area,'x',x0,x1,'y',y0,y1)
    m=(lab==idx)
    m=ndimage.binary_fill_holes(m)
    # soft alpha + despill
    rgba=np.zeros(im.shape[:2]+(4,),np.uint8)
    c=im.copy()
    spill=c[...,1]>np.maximum(c[...,0],c[...,2])
    c[...,1]=np.where(spill,np.maximum(c[...,0],c[...,2]),c[...,1])
    rgba[...,:3]=c; rgba[...,3]=(m*255)
    Image.fromarray(rgba[y0:y1,x0:x1]).save(f'{out}/part_{idx}_{x0}_{y0}.png')
