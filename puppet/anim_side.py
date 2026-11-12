# Side-view walk cycle (facing +x) -> Rigby2D batch_edit. Keys on twos (12 fps), played at 24.
import json, math
FPS=12; C=1.0; S=250; BETA=0.6; DUR=4.5
Ls=2*S*BETA; v=2*S/C
def foot(p):
    p%=1
    if p<BETA: return Ls/2 - Ls*(p/BETA), 0.0          # planted: slides back in local = fixed in world
    u=(p-BETA)/(1-BETA); e=u*u*(3-2*u)
    return -Ls/2 + Ls*e, 62*math.sin(math.pi*u)**1.2*(1-0.35*u)
ops=[{'op':'add_animation','name':'walk'}]
def key(b,ch,t,**kw): ops.append(dict(op='set_bone_key',animation='walk',bone=b,channel=ch,time=round(t,4),curve='stepped',**kw))
for i in range(int(DUR*FPS)+1):
    t=i/FPS; pl=t/C; pr=pl+0.5
    bob=-22+12*math.cos(2*math.pi*2*(pl-0.3))
    for s,p in (('l',pl),('r',pr)):
        x,y=foot(p); key(f'ik_foot_{s}','translate',t,x=x,y=y)
    key('hip','translate',t,x=0,y=bob)
    key('hip','rotate',t,value=2*math.sin(2*math.pi*pl))
    key('chest','rotate',t,value=-5+1.5*math.cos(2*math.pi*2*(pl-0.3)))
    key('head','rotate',t,value=3-1.5*math.cos(2*math.pi*2*(pl-0.3)))
    for s,p in (('l',pl),('r',pr)):
        sw=-math.cos(2*math.pi*p)       # opposite to same-side leg
        key(f'ik_hand_{s}','translate',t,x=75*sw+10,y=bob+18*abs(sw)+8)
json.dump({'path':'side_w.rigby','operations':ops},open('ops_side.json','w'))
json.dump({'v':v,'dur':DUR},open('motion_side.json','w')); print(len(ops),'v',v)
