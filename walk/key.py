import numpy as np, sys
from PIL import Image
from scipy import ndimage
for i in (1,2,3,4):
    a=np.array(Image.open(f'wk{i}.png').convert('RGB')).astype(int)
    r,g,b=a[...,0],a[...,1],a[...,2]
    green=(g>150)&(g>r+60)&(g>b+60)
    m=~green; lab,n=ndimage.label(m); sizes=ndimage.sum(m,lab,range(1,n+1)); keep=np.isin(lab,1+np.where(sizes>500)[0])
    keep=ndimage.binary_fill_holes(keep)|keep
    # despill
    rgb=a.copy(); spill=(g>np.maximum(r,b)); rgb[...,1]=np.where(spill&keep,np.maximum(r,b),g)
    alpha=ndimage.uniform_filter(keep.astype(float),3)*255
    im=np.dstack([rgb,alpha]).astype(np.uint8); ys,xs=np.where(keep)
    y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    Image.fromarray(im[y0:y1+1,x0:x1+1]).save(f'k{i}.png')
    # feet: bottom 12% of figure, left/right of centre
    h=y1-y0; cx=(x0+x1)/2; zone=keep.copy(); zone[:int(y1-0.14*h)]=0
    L=np.where(zone[:, :int(cx)].any(1))[0]; R=np.where(zone[:, int(cx):].any(1))[0]
    print(i,'h',h,'w',x1-x0,'left foot y',L.max() if len(L) else None,'right foot y',R.max() if len(R) else None,'head top',y0)
