import numpy as np, json, os, glob
from PIL import Image, ImageEnhance
P='side1'; W,H=1000,1600; O='layers_side'
def g(i): return Image.open(glob.glob(f'{P}/part_{i}_*')[0]).convert('RGBA')
head,torso,armA,armB,legA,legB=[g(i) for i in (1,2,3,4,5,6)]
def recolor_top(im,frac=.2):
    ar=np.array(im).astype(int); h=ar.shape[0]; top=ar[:int(h*frac)]
    skin=(top[...,0]>150)&(top[...,0]>top[...,2]+30)&(top[...,3]>0)
    band=ar[int(h*.35):int(h*.45)]; jac=np.median(band[band[...,3]>0][:,:3],axis=0)
    top[skin,:3]=jac; ar[:int(h*frac)]=top; return Image.fromarray(ar.astype(np.uint8))
armA,armB=recolor_top(armA),recolor_top(armB)
def dark(im,f=.72):
    rgb=ImageEnhance.Brightness(im.convert('RGB')).enhance(f).convert('RGBA'); rgb.putalpha(im.split()[3]); return rgb
def topc(im,rows=14):
    m=np.array(im)[...,3]>0; ys=np.where(m.any(1))[0]; xs=np.where(m[ys[0]+rows])[0]; return (xs[0]+xs[-1])/2
tw,th=torso.size; tx,ty=(W-tw)//2,560
sh=(tx+int(.36*tw), ty+int(.24*th))          # shoulder joint
hp=(tx+int(.47*tw), ty+int(.80*th))          # hip joint
pl={}
pl['torso']=(tx,ty)
pl['arm_l']=(int(sh[0]-topc(armA)),sh[1]-45); pl['arm_r']=(pl['arm_l'][0]-8,pl['arm_l'][1]); armB=armA.copy()
for k,im in [('leg_r',legB),('leg_l',legA)]: pl[k]=(int(hp[0]-topc(im)),hp[1]-40)
hw,hh=head.size
# neck: find bottom row centre of head mask
m=np.array(head)[...,3]>0; xs=np.where(m[-6])[0]; nc=(xs[0]+xs[-1])/2
pl['head']=(int(tx+.50*tw-nc), ty-hh+70)
ims={'arm_r':dark(armA),'leg_r':dark(legB),'torso':torso,'leg_l':legA,'head':head,'arm_l':armA}
order=['arm_r','leg_r','leg_l','torso','head','arm_l']
os.makedirs(O,exist_ok=True); comp=Image.new('RGBA',(W,H),(235,235,235,255))
for k in order:
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(ims[k],pl[k]); L.save(f'{O}/{k}.png'); comp.alpha_composite(L)
json.dump(order,open(f'{O}/order.json','w'))
comp.convert('RGB').resize((500,800)).save('/tmp/side_asm.jpg'); print(pl)
