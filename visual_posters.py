"""Build an auditable poster for every existing G0001–G0026 film and G0027 data.

These posters are *actual decoded source frames*, not new scientific pictures.
G0027 has no archived movie; its poster is a graph of archived measurements.
Do not replace the featured G0028/G0029 artwork or run a numerical solver.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps,ImageFont
import imageio_ffmpeg

MEDIA="https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/"
TITLE={
  1:"Differentiation",2:"Diversification",3:"Symmetry breaking",4:"Dynamics",
  5:"Feedback",6:"Volumetric emergence",7:"Circulation",8:"Energetics",
  9:"Organization",10:"Communication",11:"Adaptation",12:"Hypervolume",
  13:"Entities",14:"Observatory",15:"Evolution",16:"Genetics",
  17:"Ecosystem",18:"Morphogenesis",19:"Compartmentalization",
  20:"Topological complexity",21:"Multiscale persistence",
  22:"Structural heredity",23:"Factorial niche controls",
  24:"Construction specialization",25:"Structural maintenance",
  26:"Observer independence",27:"Structural statistics",
}
def selected_movies(manifest):
    chosen={1:"video-0001-14498676883.mp4",26:"video-0026-14651386328.mp4"}
    for number in range(2,26):
        k=f"{number:04d}"
        if k not in manifest:raise ValueError(f"Missing archived video ID for G{k}")
        chosen[number]=f"video-{k}-{manifest[k]}.mp4"
    return dict(sorted(chosen.items()))

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while chunk:=f.read(1048576):h.update(chunk)
    return h.hexdigest()

def cmd(argv):
    subprocess.run(argv,check=True)

def font(size,bold=False):
    from matplotlib import get_data_path
    filename="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(Path(get_data_path())/"fonts"/"ttf"/filename),size)

def movie_poster(number,title,source,out):
    executable=imageio_ffmpeg.get_ffmpeg_exe()
    count,duration=imageio_ffmpeg.count_frames_and_secs(str(source))
    if count<1 or duration<=0:raise ValueError(f"Unreadable video: {source}")
    frame=out.with_suffix(".source.png")
    # Decode the actual midpoint, not a guessed or synthetic frame.
    cmd([executable,"-hide_banner","-loglevel","error","-y",
         "-ss",str(max(0,duration*.5)),"-i",str(source),
         "-frames:v","1","-update","1",str(frame)])
    with Image.open(frame) as original:
        panel=ImageOps.fit(original.convert("RGB"),(960,540),method=Image.Resampling.LANCZOS)
    frame.unlink()
    base=Image.new("RGB",(960,660),"#102033")
    base.paste(panel,(0,82))
    draw=ImageDraw.Draw(base)
    draw.rectangle((0,0,960,82),fill="#173149")
    draw.text((24,18),f"ONTOGENESIS  /  G{number:04d}",font=font(22,True),fill="#63D7C4")
    draw.text((370,23),title,font=font(21,True),fill="#F1F7FB")
    draw.rectangle((0,622,960,660),fill="#173149")
    draw.text((24,630),"ACTUAL ARCHIVED VIDEO FRAME  /  ORIGINAL GENERATION CLIP",
              font=font(15),fill="#C7DAE6")
    base.save(out,optimize=True)
    if out.stat().st_size<4096:raise RuntimeError("Poster too small or damaged")
    return {"source_video":source.name,"source_sha256":sha(source),
            "frame_index_approx":count//2,"original_duration_seconds":duration,
            "source_frames":count,"poster_sha256":sha(out)}

def evidence_poster(source,out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d=json.loads(Path(source).read_text())
    rows=d.get("observations",[])
    if not isinstance(rows,list) or len(rows)<2 or "step" not in rows[0]:
        raise ValueError("G0027 measurement timeline absent")
    steps=[r["step"] for r in rows]
    if steps!=sorted(set(steps)):raise ValueError("Nonmonotonic G0027 sample times")
    if not all("matrix_mean" in r and "matrix_std" in r for r in rows):
        raise ValueError("Missing directly measured matrix moments")
    fig,ax=plt.subplots(1,2,figsize=(12,6),facecolor="#101d2c",layout="constrained")
    for a in ax:
        a.set_facecolor("#19334a")
        a.tick_params(colors="#e1eef8")
        a.xaxis.label.set_color("#c4d5e0")
        a.yaxis.label.set_color("#c4d5e0")
        a.title.set_color("#f0f6fb")
        for spine in a.spines.values():spine.set_color("#46657a")
    ax[0].plot(steps,[r["matrix_mean"] for r in rows],label="Matrix mean",color="#61d9c7",lw=2.5)
    ax[0].plot(steps,[r["matrix_std"] for r in rows],label="Matrix std dev",color="#f2aa71",lw=2.5)
    ax[0].set(title="Measured structural moments",xlabel="Numerical step",ylabel="Matrix concentration")
    ax[0].legend(facecolor="#28465c",labelcolor="white")
    final=next((r for r in reversed(rows) if "spectral_fraction" in r),None)
    if final is None:raise ValueError("Archived spectral distribution missing")
    fractions=final["spectral_fraction"]
    edges=final["spectral_edges"]
    assert len(edges)==len(fractions)+1
    centers=[(a+b)/2 for a,b in zip(edges[:-1],edges[1:])]
    ax[1].plot(centers,fractions,color="#75b6f2",lw=2.6)
    ax[1].fill_between(centers,0,fractions,color="#75b6f2",alpha=.20)
    ax[1].set(title=f"Actual spectrum at step {final['step']}",
              xlabel="Radial spatial frequency",ylabel="Fraction of measured spectral power")
    fig.suptitle("ONTOGENESIS / G0027 — STRUCTURAL STATISTICS",color="#f3f8fb",fontsize=19)
    fig.savefig(out,dpi=115,facecolor=fig.get_facecolor())
    plt.close(fig)
    if out.stat().st_size<4096:raise RuntimeError("Measured poster too small")
    return {"source_evidence":Path(source).name,"source_sha256":sha(source),
            "poster_sha256":sha(out),"measurement_count":len(rows),
            "source_step":final["step"],"type":"actual structural moments and observed spectrum, not a film"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--videos",default="report/videos.json",type=Path)
    parser.add_argument("--out",default="visual-posters",type=Path)
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    chosen=selected_movies(json.loads(a.videos.read_text()))
    release=json.loads(subprocess.check_output(
        ["gh","release","view","atlas-media","--json","assets"],text=True))
    available={i["name"] for i in release["assets"]}
    if set(chosen.values())-available:raise ValueError("Selected video archive missing from release")
    if "structural-evidence-0027.json" not in available:
        raise ValueError("Archived G0027 evidence missing")
    manifest={"description":"Actual archived video midpoint posters; G0027 measured structural-statistics plot",
              "films":{}}
    files=a.out/"source";files.mkdir(exist_ok=True)
    for n,name in chosen.items():
        path=files/name
        cmd(["gh","release","download","atlas-media","-p",name,"-D",str(files)])
        out=a.out/f"ontogenesis-atlas-{n:04d}.png"
        manifest["films"][f"{n:04d}"]=movie_poster(n,TITLE[n],path,out)
        print("Poster G",n,name,"->",out,flush=True)
    cmd(["gh","release","download","atlas-media","-p","structural-evidence-0027.json","-D",str(files)])
    manifest["films"]["0027"]=evidence_poster(
        files/"structural-evidence-0027.json",a.out/"ontogenesis-atlas-0027.png")
    (a.out/"ontogenesis-visual-poster-manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n")
    assert len(manifest["films"])==27
    print("All 27 verified early-generation posters generated",flush=True)

if __name__=="__main__":
    main()
