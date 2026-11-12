import json, math, subprocess, numpy as np, wave, os, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=1080,1920,24
bg=Image.open('../assets/frames/2026-11-13/s1bg_A.png').convert('RGBA').resize((W,H),Image.LANCZOS)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',62)
FEET_Y=1790
def bubble(d,text,cx,cy,tail):
    tw=d.textbbox((0,0),text,font=font); w,h=tw[2]-tw[0]+70,tw[3]-tw[1]+56; x0,y0=cx-w//2,cy-h//2
    d.polygon([(x0+w*0.25,y0+h-4),(x0+w*0.4,y0+h-4),tail],fill='white',outline='black')
    d.rounded_rectangle([x0,y0,x0+w,y0+h],radius=34,fill='white',outline='black',width=6)
    d.polygon([(x0+w*0.25+6,y0+h-8),(x0+w*0.4-6,y0+h-8),(tail[0],tail[1]-10)],fill='white')
    d.text((x0+35,y0+22),text,font=font,fill='black')
def shadow(im,cx,w=150):
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).ellipse([cx-w,FEET_Y-22,cx+w,FEET_Y+18],fill=(0,0,0,90)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
shutil.rmtree('/tmp/cf2',ignore_errors=True); os.makedirs('/tmp/cf2')
ms=json.load(open('motion_side.json')); v=ms['v']*0.75
side=sorted(os.listdir('frs/side_w')); f0=Image.open('frs/side_w/'+side[0]); fw,fh=f0.size
# feet bottom in frame (max over frames of bbox bottom ~ planted)
fb=max(Image.open('frs/side_w/'+f).getbbox()[3] for f in side[::6])
n=0; x0=-fw*0.55
for i,fn in enumerate(side):
    t=i/FPS; im=bg.copy(); x=int(x0+v*t); shadow(im,x+fw//2,120)
    im.alpha_composite(Image.open('frs/side_w/'+fn),(x,FEET_Y-fb)); im.convert('RGB').save(f'/tmp/cf2/{n:04d}.jpg',quality=92); n+=1
T1=n/FPS
front=sorted(os.listdir('fr/mgr2'))[72:]; F0=Image.open('fr/mgr2/'+front[0]); bw,bh=F0.size; bb=F0.getbbox()[3]
for i,fn in enumerate(front):
    t=3.0+i/FPS; im=bg.copy(); x=W//2-bw//2; shadow(im,W//2)
    im.alpha_composite(Image.open('fr/mgr2/'+fn),(x,FEET_Y-bb)); d=ImageDraw.Draw(im)
    if 3.4<=t<5.5: bubble(d,'Morning lads!',730,690,(610,890))
    if t>=5.75: bubble(d,'WHAT?!',600,680,(560,880))
    if 5.6<=t<5.9: im=im.transform(im.size,Image.AFFINE,(1,0,int(14*math.sin(t*90)),0,1,0))
    im.convert('RGB').save(f'/tmp/cf2/{n:04d}.jpg',quality=92); n+=1
sr=48000; a=np.zeros(int(sr*(n/FPS+1)))
def add(sig,t,g=1.0):
    s=int(t*sr); a[s:s+len(sig)]+=g*sig[:len(a)-s]
tt=np.arange(int(0.12*sr))/sr; rng=np.random.default_rng(1)
step=np.sin(2*np.pi*85*tt)*np.exp(-tt*45)+0.35*rng.standard_normal(len(tt))*np.exp(-tt*90)
k=0.0
while k<T1: add(step,k,0.55); k+=0.5
def wav(p):
    w=wave.open(p); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    if w.getframerate()!=sr: x=np.interp(np.arange(0,len(x),w.getframerate()/sr),np.arange(len(x)),x)
    return x
add(wav('../assets/sfx/surprised.wav'),T1+2.6,0.8)
a=np.clip(a/max(1,np.abs(a).max()/0.9),-1,1)
w=wave.open('/tmp/cf2/a.wav','w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a*32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i','/tmp/cf2/%04d.jpg','-i','/tmp/cf2/a.wav','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-c:a','aac','-shortest','../out/puppet_test.mp4'],check=True)
print('frames',n,'T1',T1)
