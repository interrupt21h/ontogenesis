"""G0028 video from measured, native 2D sections. No interpolated frames."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import numpy as np

def build(input_file,movie,plate,fps=12,hold=3):
    data=json.loads(Path(input_file).read_text())
    ctrl=data["arms"]["control"]["frames"]
    pert=data["arms"]["shock"]["frames"]
    times=[r["step"] for r in ctrl]
    assert times==[r["step"] for r in pert] and len(times)>2
    keys=("matrix_section","energy_section")
    left=[np.array([f[k] for f in ctrl]) for k in keys]
    right=[np.array([f[k] for f in pert]) for k in keys]
    differences=[b-a for a,b in zip(left,right)]
    fig,axs=plt.subplots(2,3,figsize=(14,9),facecolor="#f6f9fb")
    # Reserve dedicated footer space: never overlay metadata on data panels.
    fig.subplots_adjust(left=.065,right=.95,bottom=.18,top=.86,wspace=.38,hspace=.40)
    fig.suptitle("ONTOGENESIS  /  0028  ·  ENVIRONMENTAL DISTURBANCE",
                 color="#12344a",weight="bold",fontsize=19,y=.963)
    pictures=[]
    for row in range(2):
        a,b,d=left[row],right[row],differences[row]
        maximum=max(float(a.max()),float(b.max()),1e-6)
        extent=max(float(np.abs(d).max()),1e-6)
        for col,values in enumerate((a,b,d)):
            ax=axs[row,col]
            im=ax.imshow(values[0],origin="lower",interpolation="nearest",
                         cmap="RdBu_r" if col==2 else ("viridis" if row==0 else "magma"),
                         vmin=-extent if col==2 else 0,
                         vmax=extent if col==2 else maximum)
            ax.set_title(("Matrix M  /  " if row==0 else "Energy E  /  ")+
                         ("Control","Disturbed","Disturbed − control")[col],
                         color="#12344a",fontsize=12)
            ax.set_xlabel("x (cells)")
            ax.set_ylabel("y (cells)")
            fig.colorbar(im,ax=ax,shrink=.75,pad=.02)
            pictures.append((im,values))
    state=fig.text(.5,.085,"",ha="center",color="#12344a",fontsize=11,linespacing=1.8)
    def draw(i):
        for im,values in pictures: im.set_data(values[i])
        step=times[i]
        phase="pre-event" if step<data["event_step"] else ("event" if step==data["event_step"] else "post-event")
        state.set_text(
            f"Measured sections ω=z={data['section']['omega']}  ·  step {step}/{data['steps']}  "
            f"·  shock at {data['event_step']}  ·  {phase}\n"
            "Fixed field and difference color limits  /  native 2D slices, not projections")
    draw(times.index(data["event_step"]))
    Path(plate).parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(plate,dpi=150,facecolor=fig.get_facecolor())
    Path(movie).parent.mkdir(parents=True,exist_ok=True)
    writer=FFMpegWriter(fps=fps,codec="libx264",bitrate=2800,
                       extra_args=["-pix_fmt","yuv420p"])
    with writer.saving(fig,str(movie),dpi=110):
        for i in range(len(times)):
            draw(i)
            for _ in range(hold):
                writer.grab_frame()
    plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--movie",type=Path,required=True)
    p.add_argument("--plate",type=Path,required=True)
    p.add_argument("--fps",type=int,default=12)
    p.add_argument("--hold",type=int,default=3,help="Repeat recorded samples for legibility; never interpolate fields")
    args=p.parse_args()
    if args.fps<1 or args.hold<1: p.error("fps and hold must be positive")
    build(args.input,args.movie,args.plate,args.fps,args.hold)
