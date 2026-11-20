"""Deterministic abstract cover artwork, not simulation evidence."""
from pathlib import Path
import numpy as np
from PIL import Image
w,h=1800,2546
y,x=np.ogrid[-1:1:complex(h),-1:1:complex(w)]
r=np.sqrt((x*.85)**2+(y-.04)**2)
a=np.arctan2(y-.04,x*.85)
warp=r+.065*np.sin(9*a+15*r)+.035*np.sin(22*a-12*r)
phase=75*warp+4*np.sin(5*a+9*r)
filament=np.exp(-8*np.sin(phase)**2)
envelope=np.exp(-((r-.48)/.29)**2)*np.exp(-((y-.05)/.62)**6)
glow=envelope*(.25+.75*filament)
mix=(1+np.sin(5*a+10*r))/2
rgb=np.stack([8+glow*(35+170*mix),19+glow*(145-60*mix),31+glow*(175-110*mix)],axis=-1)
Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(Path(__file__).parent/"build"/"cover.png")
