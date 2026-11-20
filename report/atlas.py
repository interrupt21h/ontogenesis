"""Generate analytical vector plates shared by GitHub and the monograph."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"report/build/atlas"
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":"#19334a","text.color":"#19334a","axes.titleweight":"bold","svg.fonttype":"path","figure.facecolor":"white"})
def save(fig,n,title,note):
    fig.suptitle(f"ONTOGENESIS / {n:04d}   |   {title}",x=.06,ha="left",fontsize=15,fontweight="bold")
    fig.text(.06,.025,note,fontsize=8,color="#526575")
    fig.tight_layout(rect=(.03,.09,.98,.88))
    fig.savefig(OUT/f"{n:04d}-atlas.svg")
    plt.close(fig)

u,v=np.meshgrid(np.linspace(0,1,81),np.linspace(0,.5,81))
f,k=.035,.062
du=-u*v*v+f*(1-u)
dv=u*v*v-(f+k)*v
fig,ax=plt.subplots(1,2,figsize=(9,4))
for a,z,title in zip(ax,(du,dv),("Substrate reaction rate","Activator reaction rate")):
    lim=np.abs(z).max()
    im=a.pcolormesh(u,v,z,cmap="RdBu_r",norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim),shading="auto",rasterized=False)
    a.contour(u,v,z,levels=[0],colors="#19334a",linewidths=1.4)
    a.set(xlabel="Substrate U",ylabel="Activator V",title=title)
    fig.colorbar(im,ax=a,shrink=.8,label="Local rate")
save(fig,1,"Reaction phase space","Analytical local reaction terms; diffusion omitted. Dark curves indicate zero reaction rate.")

x=np.linspace(0,2*np.pi,180)
xx,yy=np.meshgrid(x,x)
h=(np.sin(xx)+np.cos(yy)+.5*np.sin(2*xx-yy))/2.5
fig,ax=plt.subplots(1,2,figsize=(9,4))
for a,z,title in zip(ax,(.097+.009*h,.094-.009*h),("Species V decay","Species W decay")):
    im=a.contourf(xx,yy,z,levels=np.linspace(.085,.106,22),cmap="viridis",extend="both")
    a.set(xlabel="x (radians)",ylabel="y (radians)",title=title,aspect="equal")
    fig.colorbar(im,ax=a,shrink=.8)
save(fig,3,"Spatial symmetry breaking","Analytical decay landscapes from the prescribed spatial bias; not simulation observations.")

fig,ax=plt.subplots(figsize=(9,4))
x=np.linspace(0,2*np.pi,160); X,Y=np.meshgrid(x,x)
psi=2*(np.sin(X)*np.sin(Y)+.5*np.cos(2*X-Y))
vx=2*(np.sin(X)*np.cos(Y)+.5*np.sin(2*X-Y))
vy=-2*(np.cos(X)*np.sin(Y)-np.sin(2*X-Y))
im=ax.contourf(X,Y,psi,levels=24,cmap="RdBu_r")
ax.streamplot(x,x,vx,vy,color="#19334a",density=1.1,linewidth=.65)
ax.set(xlabel="x (radians)",ylabel="y (radians)",aspect="equal",title="Streamfunction and continuum velocity")
fig.colorbar(im,ax=ax,label="Streamfunction")
save(fig,4,"Prescribed circulation","Analytical zero-phase continuum analogue; simulation uses discrete conservative fluxes.")

m=np.linspace(0,1,200)
fig,ax=plt.subplots(figsize=(9,3.5))
ax.plot(m,1/(1+5*m),color="#177e89",lw=2.5)
ax.fill_between(m,0,1/(1+5*m),color="#177e89",alpha=.12)
ax.set(xlabel="Matrix concentration M",ylabel="Relative mobility",ylim=(0,1.05),title="Structural feedback on transport")
ax.grid(alpha=.2)
save(fig,9,"Matrix-mediated mobility","Analytical response 1/(1+5M); not measured data.")

fig,ax=plt.subplots(figsize=(9,3.5))
for k,c in [(1,"#177e89"),(4,"#375a91")]:
    ax.plot(m,np.exp(-k*m),lw=2.4,label=f"Barrier coefficient {k}",color=c)
ax.set(xlabel="Absolute matrix difference across face",ylabel="Relative permeability",ylim=(0,1.05))
ax.legend(frameon=False);ax.grid(alpha=.2)
save(fig,18,"Selective diffusion across interfaces","Analytical face permeability multipliers; actual flux also depends on concentration gradient.")
