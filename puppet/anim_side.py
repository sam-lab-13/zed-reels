# Side-view walk cycle (facing +x) -> Rigby2D batch_edit. Smooth 24 fps keys.
# Feet: world-oriented foot bones (patch_foot.py): heel strike, flat stance, heel-off roll, toe-up before contact.
import json, math
FPS=24; C=1.0; S=250; BETA=0.6; DUR=4.5; FOOT0=-35.3
Ls=2*S*BETA; v=2*S/C
ss=lambda u: u*u*(3-2*u)
def foot(p):
    p%=1
    if p<BETA:
        x=Ls/2-Ls*(p/BETA); y=0.0
        if p<0.08: rot=12*(1-ss(p/0.08))
        elif p<0.42: rot=0
        else: u=ss((p-0.42)/(BETA-0.42)); rot=-30*u; y=40*u
        return x,y,rot
    u=(p-BETA)/(1-BETA); e=ss(u)
    x=-Ls/2+Ls*e; y=40*(1-ss(min(1,u/0.25)))*(u<0.25)+70*math.sin(math.pi*u)**1.3*(1-0.4*u)
    rot=-30+42*ss(u)
    return x,y,rot
ops=[{'op':'add_animation','name':'walk'}]
def key(b,ch,t,**kw): ops.append(dict(op='set_bone_key',animation='walk',bone=b,channel=ch,time=round(t,4),**kw))
for i in range(int(DUR*FPS)+1):
    t=i/FPS; pl=t/C
    bob=-14+9*math.cos(2*math.pi*2*(pl-0.3))
    for s,p in (('l',pl),('r',pl+0.5)):
        x,y,rot=foot(p); key(f'ik_foot_{s}','translate',t,x=x,y=y); key(f'foot_{s}','rotate',t,value=rot)
    key('hip','translate',t,x=0,y=bob)
    key('hip','rotate',t,value=2.5*math.sin(2*math.pi*pl))
    key('chest','rotate',t,value=-3+1.2*math.cos(2*math.pi*2*(pl-0.38))-1.5*math.sin(2*math.pi*(pl-0.08)))
    key('head','rotate',t,value=1.0*math.cos(2*math.pi*2*(pl-0.45)))
    for s,p in (('l',pl),('r',pl+0.5)):
        sw=-math.cos(2*math.pi*(p-0.07))
        key(f'ik_hand_{s}','translate',t,x=80*sw+12,y=bob+14*abs(sw)+30*max(sw,0)+6)
json.dump({'path':'side_w.rigby','operations':ops},open('ops_side.json','w'))
json.dump({'v':v,'dur':DUR},open('motion_side.json','w')); print(len(ops),'v',v)
