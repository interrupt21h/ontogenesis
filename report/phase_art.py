"""Deterministic editorial artwork, not simulation measurements."""
from pathlib import Path
import numpy as np
from PIL import Image
from PIL import ImageFilter
OUT=Path(__file__).resolve().parent/"build"/"phase_art"
OUT.mkdir(parents=True,exist_ok=True)
x,y=np.meshgrid(np.linspace(-1.65,1.65,1500),np.linspace(-1,1,900))
r=np.hypot(x,y); a=np.arctan2(y,x)
palettes=[((38,196,215),(244,104,81)),((69,147,245),(112,224,205)),((66,211,157),(234,191,92)),((175,138,244),(74,213,224)),((234,119,112),(239,192,107)),((238,173,74),(114,199,222)),((75,190,209),(199,135,242))]
palettes.append(((57,207,221),(236,119,105)))
palettes.append(((74,182,204),(232,159,96)))
palettes.append(((100,174,236),(226,182,92)))
for i,(c1,c2) in enumerate(palettes,1):
    if i==1:
        f=np.sin(9*x+3*np.sin(5*y))+np.cos(10*y+3*np.sin(4*x))
    elif i==2:
        f=10*r+4*np.sin(3*a+4*r)+2*np.cos(6*a-3*r)
    elif i==3:
        f=15*r+2*np.sin(7*a)+3*np.cos(5*x-4*y)
    elif i==4:
        f=12*np.sin(2*x+1.3*y)+8*np.cos(3*y-1.5*x)+5*np.sin(3*r)
    elif i==5:
        f=13*y+4*np.sin(7*x)+2*np.sin(9*y+5*x)
    elif i==6:
        f=7*(np.cos(4*x)+np.cos(5*y)+np.sin(4*x+5*y))
    elif i==9:
        f=9*np.sqrt((x+.22*np.sin(3*y))**2+2*y*y)+2*np.sin(6*a+3*r)+1.5*np.cos(5*x-4*y)
    elif i==8:
        f=15*r+3*np.sin(5*a-4*r)+2*np.cos(9*a+7*r)+1.4*np.sin(12*x*y)
    else:
        f=10*r+5*np.sin(5*a+3*r)+3*np.cos(9*a-5*r)
    phase=f* (3 if i==1 else 1)
    ridge=np.exp(-((np.sin(phase))/.13)**2)
    mix=.5+.5*np.sin(3*x-2*y+i)
    envelope=np.exp(-.55*(x*x+y*y))*np.clip((1.65-np.abs(x))*6,0,1)*np.clip((1-np.abs(y))*8,0,1)
    glow=np.asarray(Image.fromarray(np.uint8(ridge*255)).filter(ImageFilter.GaussianBlur(5)))/255.
    rgb=np.broadcast_to(np.array([16.,30.,45.]),(*x.shape,3)).copy()
    tint=mix[...,None]*np.array(c1)+(1-mix[...,None])*np.array(c2)
    rgb+=tint*(envelope*(.72*ridge+.65*glow))[...,None]
    Image.fromarray(np.uint8(np.clip(rgb,0,255))).save(OUT/f"{i}.png")
