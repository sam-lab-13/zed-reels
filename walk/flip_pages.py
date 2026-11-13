# Builds the flipbook pages for the walk toward camera, all on one canvas, feet on the bottom row.
import numpy as np
from PIL import Image
from scipy import ndimage
def key(path):
    a=np.array(Image.open(path).convert('RGB')).astype(int); r,g,b=a[...,0],a[...,1],a[...,2]
    m=~((g>150)&(g>r+60)&(g>b+60)); lab,n=ndimage.label(m); s=ndimage.sum(m,lab,range(1,n+1))
    m=np.isin(lab,1+np.where(s>500)[0]); m=ndimage.binary_fill_holes(m)
    rgb=a.copy(); rgb[...,1]=np.where(m&(g>np.maximum(r,b)),np.maximum(r,b),g)
    al=ndimage.uniform_filter(m.astype(float),3)*255; im=np.dstack([rgb,al]).astype(np.uint8)
    ys,xs=np.where(m); return im[ys.min():ys.max()+1, xs.min():xs.max()+1]
def hem(im):  # lowest row with jacket red near the centre
    r,g,b=[im[...,i].astype(int) for i in range(3)]; red=(r>150)&(g<90)&(b<90); c=im.shape[1]//2
    rows=np.where(red[:,c-40:c+40].sum(1)>10)[0]; return rows.max()
A=np.array(Image.open('art/k1.png')); P=key('art/pass_raw.png')
s=hem(A)/hem(P); P=np.array(Image.fromarray(P).resize((round(P.shape[1]*s),round(P.shape[0]*s)),Image.LANCZOS))
def mirror_legs(im):
    h=hem(im); out=im.copy(); al=im[...,3]>128
    r,g,b=[im[...,i].astype(int) for i in range(3)]; navy=(b>r+25)&(b>g+10)&(b<150)&al
    cnt=navy[h+10:h+250].sum(0); c0=im.shape[1]//2; cols=[x for x in range(im.shape[1]) if cnt[x]>40]
    # keep the contiguous run that contains the centre
    run=[c0]; x=c0
    while x-1>=0 and cnt[x-1]>5: x-=1
    x0=x; x=c0
    while x+1<im.shape[1] and cnt[x+1]>5: x+=1
    x1=x; x0-=8; x1+=8; c=(x0+x1)//2; w=min(c-x0,x1-c); x0,x1=c-w,c+w
    out[h:,x0:x1+1]=im[h:,x0:x1+1][:,::-1]; return out
B=mirror_legs(A); Pm=mirror_legs(P)
def sq(im,f):  # vertical squash/stretch, feet stay on the bottom
    I=Image.fromarray(im); return np.array(I.resize((I.width,round(I.height*f)),Image.LANCZOS))
pages={'wk_A':A,'wk_Ad':sq(A,0.975),'wk_P':P,'wk_Pu':sq(P,1.02),'wk_B':B,'wk_Bd':sq(B,0.975),'wk_Pm':Pm,'wk_Pmu':sq(Pm,1.02)}
Wc=max(p.shape[1] for p in pages.values())+20; Hc=max(p.shape[0] for p in pages.values())+10
for k,p in pages.items():
    can=Image.new('RGBA',(Wc,Hc),(0,0,0,0)); can.alpha_composite(Image.fromarray(p),((Wc-p.shape[1])//2,Hc-p.shape[0])); can.save(f'pages/{k}.png')
print(Wc,Hc,{k:p.shape for k,p in pages.items()})
