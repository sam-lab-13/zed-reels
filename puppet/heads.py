import numpy as np, glob
from PIL import Image, ImageFilter
from scipy import ndimage
def key(path):
    im=np.array(Image.open(path).convert('RGB')).astype(int)
    r,g,b=im[...,0],im[...,1],im[...,2]
    m=~((g>150)&(g>r+60)&(g>b+60))
    lab,n=ndimage.label(m); sizes=ndimage.sum(m,lab,range(1,n+1)); m=lab==(np.argmax(sizes)+1)
    m=ndimage.binary_fill_holes(m)
    spill=im[...,1]>np.maximum(im[...,0],im[...,2]); im[...,1]=np.where(spill,np.maximum(im[...,0],im[...,2]),im[...,1])
    a=np.dstack([im,m*255]).astype(np.uint8); ys,xs=np.where(m)
    return Image.fromarray(a[ys.min():ys.max()+1,xs.min():xs.max()+1])
base=Image.open(glob.glob('parts1/part_1_*')[0]).convert('RGBA'); W,H=base.size
out={'head':base}
for v in ['talk','shock','blink']:
    k=key(f'art/heads/head_{v}.png').resize((W,H),Image.LANCZOS); out[v]=k
B=np.array(base).astype(float)
def patch(var,y0,y1,x0,x1):
    V=np.array(out[var]).astype(float); m=np.zeros((H,W)); m[int(y0*H):int(y1*H),int(x0*W):int(x1*W)]=1
    m=ndimage.gaussian_filter(m,6)[...,None]; res=B*(1-m)+V*m; res[...,3]=B[...,3]
    return Image.fromarray(res.astype(np.uint8))
out['talk']=patch('talk',.62,.86,.22,.78)
out['blink']=patch('blink',.38,.55,.12,.88)
for k,v in out.items(): v.save(f'parts1/head_{k}.png' if k!='head' else 'parts1/head_base.png')
s=Image.new('RGBA',(W*4,H),(230,230,230,255))
for i,k in enumerate(['head','talk','shock','blink']): s.alpha_composite(out[k],(i*W,0))
s.convert('RGB').save('/tmp/heads2.jpg')
