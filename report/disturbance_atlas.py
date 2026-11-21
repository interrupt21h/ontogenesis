"""G0028 matched interventions: measured pilot and full-domain fields, never decoded video."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def render(src,out):
    data=json.loads(Path(src).read_text())
    control=data["arms"]["control"]["frames"]
    shocked=data["arms"]["shock"]["frames"]
    steps=np.array([r["step"] for r in control])
    assert steps.tolist()==[r["step"] for r in shocked]
    assert data["generation"]=="0028" and data["seed"]==42
    assert (data["n"],data["steps"],data["event_step"]) in ((12,240,120),(24,4800,2400))
    assert steps[0]==0 and data["event_step"] in steps and steps[-1]==data["steps"]
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                         "axes.spines.top":False,"axes.spines.right":False})
    fig,axs=plt.subplots(2,2,figsize=(11,7.7),facecolor="#f8fafc")
    fig.subplots_adjust(top=.82,bottom=.14,left=.095,right=.96,hspace=.43,wspace=.27)
    fig.suptitle("ONTOGENESIS / G0028  ·  LOCALIZED DISTURBANCE",
                 color="#173b55",fontsize=17,fontweight="bold",y=.965)
    fig.text(.5,.903,f"Paired, recorded numerical measurements · {data['n']}⁴ periodic lattice · seed 42",
             ha="center",fontsize=11,color="#526b7b")
    fig.text(.5,.865,("Full-domain paired comparison — not proof of organismal recovery" if data["n"]==24 else "Small-domain pilot — not a mature-ecology recovery study"),
             ha="center",fontsize=10,color="#a26b2d")
    for col,(key,title) in enumerate((("local_energy","Energy in perturbation core"),
                                       ("local_matrix","Structural matrix in perturbation core"))):
        a=np.array([r[key] for r in control]);b=np.array([r[key] for r in shocked])
        top=axs[0,col]
        top.plot(steps,a,color="#285678",lw=2,label="Unperturbed control")
        top.plot(steps,b,color="#d18b3a",lw=2,label="Localized shock")
        top.set_title(title,fontsize=12,fontweight="bold",color="#173b55",pad=9)
        top.set_ylabel("Regional mean concentration")
        top.legend(loc="best",fontsize=8,frameon=False)
        bottom=axs[1,col]
        bottom.plot(steps,b-a,color="#137e79",lw=2.4)
        bottom.axhline(0,color="#627888",lw=1,alpha=.65)
        bottom.set_title("Matched difference · shocked minus control",
                         fontsize=11,color="#173b55",pad=8)
        bottom.set_xlabel("Integration step")
        bottom.set_ylabel("Difference in regional mean")
        for ax in (top,bottom):
            ax.axvline(data["event_step"],color="#ab5c42",ls="--",lw=1.3,alpha=.85)
            ax.set_xlim(0,data["steps"])
            ax.grid(color="#dce6eb",alpha=.65)
    c=data["comparisons"]
    fig.text(.5,.065,
             f"At step {data['steps']}: |ΔE| attenuation {100*c['local_energy']['deviation_attenuation']:.2f}%"
             f"   ·   |ΔM| attenuation {100*c['local_matrix']['deviation_attenuation']:.2f}%",
             ha="center",color="#173b55",fontsize=10,fontweight="bold")
    fig.text(.5,.03,
             (f"Source: verified G0028 {'full artifact 14682932255' if data['n']==24 else 'pilot artifact 14670709650'}"
              f" · measured core means · dashed line: shock at step {data['event_step']}"),
             ha="center",color="#526b7b",fontsize=8.5)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,facecolor=fig.get_facecolor())
    plt.close(fig)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path)
    p.add_argument("output",type=Path)
    x=p.parse_args()
    render(x.input,x.output)
