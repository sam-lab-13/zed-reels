# Drawn walk toward camera: 2 AI drawings (A + leg-mirrored A'), perspective scale-up, bob, sway, real CC0 footsteps.
import numpy as np, math, os, shutil, subprocess, wave
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W,H,FPS=1080,1920,24
FR='../assets/frames/2026-11-13/'
bg=Image.open(FR+'s1bg_A.png').convert('RGBA').resize((W,H),Image.LANCZOS)
A=Image.open('art/k1.png'); B=Image.open('art/k1m.png'); h0=A.height
HOR, FEET_END, H_END = 1075, 1835, 1300
Z0, Z1, DUR, STEP = 2.5, 1.0, 3.3, 0.42
out='/tmp/wt'; shutil.rmtree(out,ignore_errors=True); os.makedirs(out)
n=0; steps=[]
N=int(DUR*FPS)
for i in range(N):
    t=i/FPS; u=t/DUR; z=Z0+(Z1-Z0)*(1-(1-u)**1.2)   # slight ease-out as he arrives
    hh=H_END/z; feet=HOR+(FEET_END-HOR)/z
    k=int(t/STEP); ph=(t/STEP)%1
    if not steps or steps[-1][0]!=k: steps.append((k,t,1/z))
    fig=A if k%2==0 else B
    bob=-0.028*hh*math.sin(math.pi*ph)            # high at passing, low at contact
    sway=0.012*hh*(1 if k%2==0 else -1)*math.sin(math.pi*ph)
    s=hh/h0; im=fig.resize((max(1,int(fig.width*s)),int(hh)),Image.LANCZOS)
    frame=bg.copy(); cx=W//2+int(sway)
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sw=int(0.17*hh)
    ImageDraw.Draw(sh).ellipse([cx-sw,feet-0.018*hh,cx+sw,feet+0.012*hh],fill=(0,0,0,70)); frame.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    frame.alpha_composite(im,(cx-im.width//2,int(feet-hh+bob)))
    frame.convert('RGB').save(f'{out}/{n:04d}.jpg',quality=92); n+=1
T1=n/FPS
# cut: the standing shot, slow push-in + bubble
s1=Image.open(FR+'s1_A.png').convert('RGBA').resize((W,H),Image.LANCZOS)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',64)
for i in range(int(2.2*FPS)):
    t=i/FPS; zf=1+0.04*t/2.2; cw,ch=int(W/zf),int(H/zf)
    f=s1.crop(((W-cw)//2,(H-ch)//3,(W-cw)//2+cw,(H-ch)//3+ch)).resize((W,H),Image.LANCZOS); d=ImageDraw.Draw(f)
    if t>=0.3:
        txt='Morning lads!'; bb=d.textbbox((0,0),txt,font=font); w,h=bb[2]-bb[0]+70,bb[3]-bb[1]+56; x0,y0=540-w//2,220
        d.polygon([(x0+w*.55,y0+h-4),(x0+w*.7,y0+h-4),(620,y0+h+90)],fill='white',outline='black')
        d.rounded_rectangle([x0,y0,x0+w,y0+h],radius=34,fill='white',outline='black',width=6)
        d.polygon([(x0+w*.55+6,y0+h-8),(x0+w*.7-6,y0+h-8),(618,y0+h+80)],fill='white')
        d.text((x0+35,y0+22),txt,font=font,fill='black')
    f.convert('RGB').save(f'{out}/{n:04d}.jpg',quality=92); n+=1
sr=48000; a=np.zeros(int(sr*(n/FPS+0.5))); hits=np.load('art/hits.npy'); rng=np.random.default_rng(3)
for k,t,inv in steps:
    hsig=hits[rng.integers(len(hits))]; g=0.25+0.55*(inv-1/Z0)/(1-1/Z0)
    s=int(t*sr); a[s:s+len(hsig)]+=g*hsig[:len(a)-s]
a=np.clip(a,-1,1)*0.9
wv=wave.open(f'{out}/a.wav','w'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((a*32767).astype(np.int16).tobytes()); wv.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',f'{out}/%04d.jpg','-i',f'{out}/a.wav','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-c:a','aac','-shortest','../out/walk_toward_test.mp4'],check=True)
print('frames',n,'walk',T1,'steps',len(steps))
