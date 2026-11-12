# Adds the head variants as layers at the head's place (front rig), writes layers/order2.json
import json
from PIL import Image
place={'head': tuple(json.load(open('layers/place.json'))['head'])}
order=json.load(open('layers/order.json')); W,H=1000,1600
for v in ['talk','shock','blink']:
    L=Image.new('RGBA',(W,H),(0,0,0,0)); L.alpha_composite(Image.open(f'parts1/head_{v}.png'),place['head']); L.save(f'layers/head_{v}.png'); order.append(f'head_{v}')
json.dump(order,open('layers/order2.json','w'))
