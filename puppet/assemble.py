import numpy as np, json, os
from PIL import Image
P='parts1'; W,H=1000,1600
f={n:Image.open(f'{P}/'+[x for x in os.listdir(P) if x.startswith(f'part_{i}_')][0]).convert('RGBA') for n,i in
   dict(head=1,torso=2,arm_r=3,arm_l=4,pelvis=5,leg_r=6,leg_l=7).items()}
def a(im): return np.array(im)[...,3]>0
def topcenter(im,rows=12):
    m=a(im); ys=np.where(m.any(1))[0]; y=ys[0]+rows; xs=np.where(m[y])[0]; return (xs[0]+xs[-1])/2
# recolor skin shoulder ball on arms -> jacket colour (top 22%)
for k in ['arm_r','arm_l']:
    ar=np.array(f[k]).astype(int); h=ar.shape[0]; top=ar[:int(h*.2)]
    skin=(top[...,0]>150)&(top[...,0]>top[...,2]+30)&(top[...,3]>0)
    # jacket colour sample
    jac=np.median(ar[int(h*.4):int(h*.5)][ar[int(h*.4):int(h*.5),...,3]>0][:,:3],axis=0)
    top[skin,:3]=jac; ar[:int(h*.2)]=top; f[k]=Image.fromarray(ar.astype(np.uint8))
T=f['torso']; tw,th=T.size
tx,ty=(W-tw)//2,520
place={'torso':(tx,ty)}
# shoulders: arm top centre sits ~18px inside torso edge, 25px below torso top
for k,sx in [('arm_r',tx+22),('arm_l',tx+tw-22)]:
    im=f[k]; c=topcenter(im); place[k]=(int(sx-c),ty+18)
Pv=f['pelvis']; pw,ph=Pv.size; place['pelvis']=((W-pw)//2,ty+th-40)
py=place['pelvis'][1]
for k,fx in [('leg_r',W/2-pw*0.25),('leg_l',W/2+pw*0.25)]:
    im=f[k]; c=topcenter(im); place[k]=(int(fx-c),py+ph-95)
Hd=f['head']; hw,hh=Hd.size; place['head']=((W-hw)//2,ty-hh+40)
order=['arm_r','arm_l','leg_r','leg_l','pelvis','torso','head']  # back to front
os.makedirs('layers',exist_ok=True)
comp=Image.new('RGBA',(W,H),(0,0,0,0)); meta=[]
for k in order:
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(f[k],place[k]); L.save(f'layers/{k}.png')
    comp.alpha_composite(L); meta.append(k)
json.dump(meta,open('layers/order.json','w')); json.dump(place,open('layers/place.json','w'))
bg=Image.new('RGBA',(W,H),(235,235,235,255)); bg.alpha_composite(comp); bg.convert('RGB').resize((500,800)).save('/tmp/assembled.jpg')
print(place)
