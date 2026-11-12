import zipfile, json, sys, shutil
src=sys.argv[1]; flips=dict(a.split('=') for a in sys.argv[2:])
z=zipfile.ZipFile(src); items={n:z.read(n) for n in z.namelist()}; z.close()
d=json.loads(items['project.json'])
for c in d['ik']:
    if c['name'] in flips: c['bendPositive']=flips[c['name']]=='1'
items['project.json']=json.dumps(d).encode()
with zipfile.ZipFile(src,'w',zipfile.ZIP_STORED) as z:
    for n,b in items.items(): z.writestr(n,b)
print([ (c['name'],c['bendPositive']) for c in d['ik']])
