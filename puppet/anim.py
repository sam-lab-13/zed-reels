# Procedural choreography -> Rigby2D batch_edit ops (keys on twos, 12 fps, stepped)
import json, math, random
random.seed(3)
FPS=12; DUR=8.0
S=70; T=0.42            # stride px, step time s
WALK_END=2.94           # 7 steps
v=S/T
def root_x(t): return v*min(t,WALK_END) - v*WALK_END   # ends at 0 (compositor uses this)
def sstep(u): u=max(0,min(1,u)); return u*u*(3-2*u)
# foot world x (relative to final root), planted logic
def feet(t):
    n=int(min(t,WALK_END-1e-6)//T); u=(min(t,WALK_END)-n*T)/T
    # initial world positions: each foot at setup offset + root_x(0)
    pos={'r':root_x(0),'l':root_x(0)}
    lift={'r':0,'l':0}
    for k in range(n):
        f='r' if k%2==0 else 'l'; pos[f]+= (S if k==0 else 2*S)
    if t<WALK_END:
        f='r' if n%2==0 else 'l'; adv=(S if n==0 else 2*S)
        if n==int(WALK_END/T)-1: adv=S if n>0 else adv
        pos[f]+=adv*sstep(u); lift[f]=38*math.sin(math.pi*u)
        return pos,lift,u,f
    return pos,lift,1,None
# fix: last step lands foot so both feet end under body
steps=int(round(WALK_END/T))
ops=[{'op':'add_animation','name':'test'}]
def key(bone,ch,t,**kw): ops.append(dict(op='set_bone_key',animation='test',bone=bone,channel=ch,time=round(t,4),curve='stepped',**kw))
def att(slot,t,show): ops.append(dict(op='set_attachment_key',animation='test',slot=slot,time=round(t,4),**({'attachment':slot} if show else {'hide':True})))
N=int(DUR*FPS)+1
# expression timeline
SHOCK=5.6; WAVE0,WAVE1=3.3,5.4
for i in range(N):
    t=i/FPS; rx=root_x(t)
    if t<WALK_END:
        pos,lift,u,sw=feet(t)
        for f in 'rl':
            key(f'ik_foot_{f}','translate',t,x=pos[f]-rx,y=lift[f])
        bob=10*math.sin(math.pi*u); sway=3*(1 if sw=='r' else -1)*math.sin(math.pi*u)
        key('hip','translate',t,x=0,y=bob-6)
        key('hip','rotate',t,value=sway)
        key('head','rotate',t,value=-sway*0.8)
        sgn=1 if sw=='r' else -1
        key('ik_hand_r','translate',t,x=-8+14*sgn*math.sin(math.pi*u),y=bob+6*math.sin(math.pi*u))
        key('ik_hand_l','translate',t,x=8+14*sgn*math.sin(math.pi*u),y=bob-6*math.sin(math.pi*u))
    elif t<SHOCK:
        settle=max(0,1-(t-WALK_END)/0.3)
        for f in 'rl': key(f'ik_foot_{f}','translate',t,x=0,y=0)
        breathe=3*math.sin(2*math.pi*(t-WALK_END)/1.6)
        key('hip','translate',t,x=0,y=-6*settle+breathe*0.5)
        key('hip','rotate',t,value=0)
        key('ik_hand_r','translate',t,x=-4,y=breathe)
        if WAVE0<=t<WAVE1:
            up=sstep((t-WAVE0)/0.25)*sstep((WAVE1-t)/0.25)
            w=math.sin(2*math.pi*3.0*(t-WAVE0))
            key('ik_hand_l','translate',t,x=(210+30*w)*up,y=470*up+ (10*abs(w))*up)
            key('head','rotate',t,value=4*up+1.5*math.sin(2*math.pi*0.8*t))
            key('chest','rotate',t,value=3*up)
        else:
            key('ik_hand_l','translate',t,x=4,y=breathe)
            key('head','rotate',t,value=1.5*math.sin(2*math.pi*0.8*t))
            key('chest','rotate',t,value=0)
    else:
        a=sstep((t-SHOCK)/0.17); jolt=30*math.exp(-(t-SHOCK)*6)*math.sin(min(1,(t-SHOCK)/0.17)*math.pi/2+0.0)
        tr=3*math.sin(2*math.pi*7*t)*(t>SHOCK+0.3)
        for f in 'rl': key(f'ik_foot_{f}','translate',t,x=0,y=0)
        key('hip','translate',t,x=tr,y=jolt)
        key('hip','rotate',t,value=0)
        key('chest','rotate',t,value=-2*a)
        key('head','rotate',t,value=tr*0.6)
        key('head','scale',t,x=1+0.06*a,y=1+0.06*a)
        key('ik_hand_r','translate',t,x=-20*a,y=500*a)
        key('ik_hand_l','translate',t,x=20*a,y=500*a)
# face: talk during wave (random mouth flaps on twos), blinks, shock
for s in ['head_talk','head_shock','head_blink']: att(s,0,False)
blinks=[1.2,4.6]
for b in blinks: att('head_blink',b,True); att('head_blink',b+0.125,False)
t=WAVE0+0.1; open_=False
while t<WAVE1+0.2:
    open_=not open_ if random.random()<0.75 else open_
    att('head_talk',t,open_); t+=1/FPS*random.choice([1,1,2])
att('head_talk',WAVE1+0.25,False)
att('head_shock',SHOCK,True)
json.dump({'path':'mgr2.rigby','operations':ops},open('ops.json','w'))
json.dump({'fps':FPS,'root_x':[root_x(i/24) for i in range(int(DUR*24))]},open('motion.json','w'))
print(len(ops))
