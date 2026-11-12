import json, math, subprocess, numpy as np, wave, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS=1080,1920,24
m=json.load(open('motion.json')); rx=m['root_x']
bg=Image.open('../assets/frames/2026-11-13/s1bg_A.png').convert('RGBA').resize((W,H),Image.LANCZOS)
frames=sorted(os.listdir('fr/mgr2')); f0=Image.open('fr/mgr2/'+frames[0]); fw,fh=f0.size
FEET_Y=1790; bb=f0.getbbox(); feet_in_frame=bb[3]
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',62)
def bubble(d,text,cx,cy,tail):
    tw=d.textbbox((0,0),text,font=font); w,h=tw[2]-tw[0]+70,tw[3]-tw[1]+56
    x0,y0=cx-w//2,cy-h//2
    d.polygon([(x0+w*0.25,y0+h-4),(x0+w*0.4,y0+h-4),tail],fill='white',outline='black')
    d.rounded_rectangle([x0,y0,x0+w,y0+h],radius=34,fill='white',outline='black',width=6)
    d.polygon([(x0+w*0.25+6,y0+h-8),(x0+w*0.4-6,y0+h-8),(tail[0],tail[1]-10)],fill='white')
    d.text((x0+35,y0+22),text,font=font,fill='black')
os.makedirs('/tmp/cf',exist_ok=True)
N=len(frames)
for i,fn in enumerate(frames[:N]):
    t=i/FPS; im=bg.copy()
    x=int(W/2-fw/2+rx[min(i,len(rx)-1)]*0.75); y=FEET_Y-feet_in_frame
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).ellipse([x+fw/2-150,FEET_Y-22,x+fw/2+150,FEET_Y+18],fill=(0,0,0,90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(Image.open('fr/mgr2/'+fn),(x,y))
    d=ImageDraw.Draw(im)
    if 3.4<=t<5.5: bubble(d,'Morning lads!',730,690,(610,890))
    if t>=5.75: bubble(d,'WHAT?!',600,680,(560,880))
    # shake on shock
    if 5.6<=t<5.9:
        a=int(14*math.sin(t*90)); im=im.transform(im.size,Image.AFFINE,(1,0,a,0,1,0))
    im.convert('RGB').save(f'/tmp/cf/{i:04d}.jpg',quality=92)
# audio
sr=48000; dur=N/FPS; a=np.zeros(int(sr*dur)+sr)
def add(sig,t,g=1.0):
    s=int(t*sr); a[s:s+len(sig)]+=g*sig[:len(a)-s]
tt=np.arange(int(0.12*sr))/sr
step=np.sin(2*np.pi*90*tt)*np.exp(-tt*40)+0.3*np.random.randn(len(tt))*np.exp(-tt*80)
T=0.42
for n in range(7): add(step,n*T+0.2,0.5)
def wav(p):
    w=wave.open(p); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    if w.getframerate()!=sr: x=np.interp(np.arange(0,len(x),w.getframerate()/sr),np.arange(len(x)),x)
    return x
add(wav('../assets/sfx/surprised.wav'),5.6,0.8)
a=np.clip(a/ max(1,np.abs(a).max()/0.9),-1,1)
w=wave.open('/tmp/cf/a.wav','w'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((a*32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i','/tmp/cf/%04d.jpg','-i','/tmp/cf/a.wav','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-r','24','-c:a','aac','-shortest','../out/puppet_front.mp4'],check=True)
print('ok',N)
