"""Reader-facing vector atlas. Models and recorded endpoints are kept separate."""
from pathlib import Path
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch, FancyBboxPatch
from itertools import product
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"report/build/atlas"
OUT.mkdir(parents=True,exist_ok=True)
INK="#19334a"; TEAL="#24856b"; GOLD="#c58035"; BLUE="#375a91"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"text.color":INK,"axes.labelcolor":INK,"axes.spines.top":False,"axes.spines.right":False,"svg.fonttype":"path"})
def save(fig,name):
    fig.savefig(OUT/(name+".pdf"),bbox_inches="tight",pad_inches=.18)
    fig.savefig(OUT/(name+".svg"),bbox_inches="tight",pad_inches=.18)
    plt.close(fig)
def arrow(ax,a,b,color=TEAL,rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=13,color=color,linewidth=1.5,connectionstyle=f"arc3,rad={rad}"))
def box(ax,x,y,w,h,txt,color=TEAL):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=.04",facecolor=color+"12",edgecolor=color))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",fontsize=10)
# Fourth-coordinate stack of schematic three-dimensional cubes.
fig,ax=plt.subplots(figsize=(9,4.5)); ax.set(xlim=(0,12),ylim=(0,6)); ax.axis("off")
for j in range(6):
    x=.55+j*1.55; y=2.1
    c=GOLD if j==1 else TEAL if j==4 else "#9aaab6"
    for pts in [[(0,0),(1,0),(1,1.15),(0,1.15)],[(0,1.15),(.35,1.5),(1.35,1.5),(1,1.15)],[(1,0),(1.35,.35),(1.35,1.5),(1,1.15)]]:
        ax.add_patch(Polygon(np.array(pts)+[x,y],closed=True,facecolor=c+"25",edgecolor=c,lw=1.4))
    ax.text(x+.65,y-.3,["0","4","8","12","16","20"][j],ha="center")
arrow(ax,(.6,1.2),(10.2,1.2)); ax.text(5.4,.8,"Fourth spatial coordinate (periodic, 24 cells)",ha="center")
arrow(ax,(9.65,3.8),(.7,3.8),BLUE,.38)
ax.text(5.25,5.3,"Periodic identification",ha="center",color=BLUE)
ax.text(2.75,4.1,"Chemistry section",ha="center",color=GOLD)
ax.text(7.4,4.1,"Identity section",ha="center",color=TEAL)
ax.text(5.4,.18,"Illustrative positions 4 and 16; scalar interpolation occurs between adjacent sections.",ha="center",fontsize=9)
save(fig,"spatial-sections")
# Hypercube drawn as two 3-bit cubes; each edge flips exactly one locus.
fig,ax=plt.subplots(figsize=(9,5)); ax.axis("off"); ax.set(xlim=(-.6,9.5),ylim=(-1.1,4.8))
pos={}
for c,k,s,b in product(range(2),repeat=4):
    g=c+2*k+4*s+8*b
    pos[g]=(b*5+c*2+s*.65,k*2+s*.65+.6)
for g in range(16):
    for j in range(4):
        q=g^(1<<j)
        if q>g:
            a,z=pos[g],pos[q]
            ax.plot([a[0],z[0]],[a[1],z[1]],color=[TEAL,BLUE,"#8897a5",GOLD][j],lw=1.25,alpha=.85,ls="--" if j==3 else "-")
for g,(x,y) in pos.items():
    ax.scatter(x,y,s=530,c="white",edgecolors=GOLD if g&8 else TEAL,zorder=3)
    ax.text(x,y,"".join(str((g>>j)&1) for j in range(4)),ha="center",va="center",fontsize=8,zorder=4)
ax.text(1.3,4.1,"B = 0  /  non-builder",ha="center",weight="bold")
ax.text(6.3,4.1,"B = 1  /  builder",ha="center",weight="bold")
ax.text(3.8,-.55,"C: catalysis    K: economy    S: signal response    B: construction",ha="center")
ax.text(3.8,-.9,"Each edge flips one locus; the two groups are linked by construction mutations.",ha="center",fontsize=9)
save(fig,"genetic-architecture")
# Research genealogy: model succession, not biological lineage.
history=(ROOT/"docs/HISTORY.md").read_text()
records=re.findall(r"^## Generation (\d{4}) — (.+)$",history,re.M)
assert len(records)>=24
# Dedicated heading band and equal-size cards; all connectors occupy gutters.
fig,ax=plt.subplots(figsize=(8,9.3))
fig.subplots_adjust(left=.025,right=.975,bottom=.035,top=.985)
ax.axis("off"); ax.set(xlim=(0,12),ylim=(0,15.2))
phases=[(1,3,"Pattern formation"),(4,7,"Transport and volume"),(8,11,"Environmental feedback"),(12,14,"Observation"),(15,17,"Heredity and ecology"),(18,20,"Structure and topology"),(21,24,"Construction and controls")]
short={3:"Symmetry\\nbreaking",6:"Volumetric\\nemergence",9:"Organization",10:"Communication",19:"Compartment\\nformation",20:"Topological\\ncomplexity",21:"Multiscale topology\\npersistence",22:"Structural\\nheredity",23:"Factorial niche\\nconstruction controls",24:"Independent construction\\nspecialization"}
import textwrap
for i,(lo,hi,theme) in enumerate(phases):
    y=14.85-i*2.03
    ax.text(.12,y,f"{i+1:02d}  /  {theme.upper()}",weight="bold",fontsize=10,va="top",color=INK)
    for j,g in enumerate(range(lo,hi+1)):
        x=.15+j*3.0
        color=GOLD if g in (13,14,19,20,21,23) else TEAL
        bottom=y-1.63
        ax.add_patch(FancyBboxPatch((x,bottom),2.65,1.19,boxstyle="round,pad=.015,rounding_size=.07",facecolor=color+"10",edgecolor=color,lw=.9))
        ax.text(x+.13,bottom+.93,f"{g:04d}",fontsize=9,weight="bold",color=color,va="center")
        title=short.get(g,textwrap.fill(records[g-1][1],22,break_long_words=False))
        ax.text(x+1.325,bottom+.43,title,ha="center",va="center",fontsize=8.5,linespacing=1.12)
        if j: 
            ax.add_patch(FancyArrowPatch((x-.30,bottom+.59),(x-.06,bottom+.59),arrowstyle="-|>",mutation_scale=9,color=TEAL,lw=1,shrinkA=0,shrinkB=0))
    if i<6: ax.plot([.12,11.8],[y-1.83]*2,color="#dce4e8",lw=.65)
ax.text(.15,.48,"MODEL REVISION",color=TEAL,weight="bold",fontsize=9)
ax.text(4.1,.48,"OBSERVATION / CONTROL",color=GOLD,weight="bold",fontsize=9)
ax.text(.15,.10,"Read left to right, then top to bottom. Labels are abbreviated where necessary.",fontsize=8)
save(fig,"research-genealogy")
# Exact recorded endpoint values, with no inferred missing data.
fig,axes=plt.subplots(2,1,figsize=(9,6.7),gridspec_kw={"height_ratios":[1,1.2]})
g=["0016","0017","0018","0019","0021","0022"]
m=[100,100/331776,10.504075,10.503774,10.504,0]
ax=axes[0]
ax.bar(g,m,color=TEAL,width=.58); ax.set(ylabel="Matrix coverage (%)",ylim=(0,116),title="A  /  Historical endpoints (different models and durations)")
for i,v in enumerate(m): ax.text(i,v+3, f"{v:.4g}%",ha="center",fontsize=9)
ax=axes[1]
arms=["Baseline","Cost","Maintenance","Combined"]
vals=np.array([[10.5038,0,34.4627,0],[3.6121,50.4865,.7246,65.0499],[68.2795,10.0279,79.2975,21.7159]])
x=np.arange(4)
for i,(label,col) in enumerate(zip(["Matrix","V active","W active"],[TEAL,GOLD,BLUE])):
    ax.bar(x+(i-1)*.24,vals[i],width=.23,label=label,color=col)
ax.set(xticks=x,xticklabels=arms,ylabel="Active coverage (%)",ylim=(0,100),title="B  /  G0023 matched-seed factorial comparison")
ax.legend(frameon=False,ncol=3,loc="upper center")
fig.tight_layout(h_pad=2)
save(fig,"comparative-endpoints")
fig,ax=plt.subplots(figsize=(8,3.7))
t=np.array([.10,.15,.20,.25,.30])
ax.plot(t,[5,-19,0,0,0],"o-",color=GOLD,label="Euler characteristic")
ax.axhline(0,color="#aab4bd",lw=.7)
ax.set(xlabel="Matrix concentration threshold",ylabel="Euler characteristic",xticks=t)
b=ax.twinx(); b.spines["right"].set_visible(True)
b.plot(t,[83.978,50.171,10.504,0,0],"s--",color=TEAL,label="Coverage")
b.set(ylabel="Matrix coverage (%)",ylim=(-5,100))
ax.legend(ax.lines[:1]+b.lines,[ "Euler characteristic","Coverage"],frameon=False,loc="lower right")
save(fig,"threshold-profile")
