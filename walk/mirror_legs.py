# Makes the opposite-foot drawing: mirrors only the legs band below the jacket hem (k1.png -> k1m.png).
import numpy as np
from PIL import Image
a=np.array(Image.open('art/k1.png')); c,x0,x1,y0=158,84,232,594
b=a.copy(); b[y0:,x0:x1+1]=a[y0:,2*c-x1:2*c-x0+1][:,::-1]; Image.fromarray(b).save('art/k1m.png')
