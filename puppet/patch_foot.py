# Foot bones keep world orientation (noRotationOrReflection) so feet stay flat when the leg swings.
import sys, json, zipfile, shutil, math
p=sys.argv[1]; z=zipfile.ZipFile(p); files={n:z.read(n) for n in z.namelist()}; z.close()
d=json.loads(files['project.json']); B=d['bones']
def world_rot(i):
    r=0
    while i is not None: r+=B[i]['rotation']; i=B[i].get('parent')
    return r
for i,b in enumerate(B):
    if b['name'].startswith('foot_'):
        w=world_rot(i); b['inherit']='noRotationOrReflection'; b['rotation']=w; print(b['name'],'world',round(w,1))
files['project.json']=json.dumps(d).encode()
with zipfile.ZipFile(p+'.tmp','w',zipfile.ZIP_DEFLATED) as o:
    for n,v in files.items(): o.writestr(n,v)
shutil.move(p+'.tmp',p)
