"""Assemble verified generation videos, preserving each source's playback duration."""
import json, re, subprocess, zipfile, tempfile, hashlib
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO="interrupt21h/ontogenesis"
OUT=ROOT/"report/build/film"
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/"report/videos.json").read_text())
titles=dict(re.findall(r"^## Generation (\d{4}) — (.+)$",(ROOT/"docs/HISTORY.md").read_text(),re.M))
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def run(*args):
    subprocess.run(args,check=True)
def probe(p):
    return json.loads(subprocess.check_output(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)]))
def api(endpoint):
    return json.loads(subprocess.check_output(["gh","api",f"repos/{REPO}/{endpoint}"]))

def discover():
    # Re-scan successful main runs instead of relying on event ordering or a
    # concurrent README reconciliation. Never replace a known artifact with an older one.
    paths=re.findall(r"^\| (\d{4}) \|.*?\[Runs\]\(\.github/workflows/([^)]*)\)",(ROOT/"README.md").read_text(),re.M)
    paths=dict(paths); paths["0026"]="consolidation.yml"
    for gen,path in sorted(paths.items()):
        runs=api(f"actions/workflows/{path}/runs?branch=main&status=success&per_page=10")["workflow_runs"]
        for job in runs:
            if job["head_repository"]["full_name"]!=REPO: continue
            artifacts=api(f"actions/runs/{job['id']}/artifacts?per_page=100")["artifacts"]
            names={"0001":"ontogenesis-render","0026":"observer-24"}
            name=names.get(gen,"evolution.mp4")
            matching=[a for a in artifacts if a["name"]==name and not a["expired"]]
            if matching:
                manifest[gen]=max(int(manifest.get(gen,0)),max(a["id"] for a in matching))
                break
    manifest.setdefault("0001",14497996026)

def download_zip(artifact,p):
    with p.open("wb") as f:
        subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{artifact}/zip"],stdout=f,check=True)

def special_source(gen,artifact,p):
    with tempfile.TemporaryDirectory() as d:
        raw=Path(d)/"payload";download_zip(artifact,raw)
        with zipfile.ZipFile(raw) as z:
            if gen=="0001":
                names=sorted(n for n in z.namelist() if re.search(r"0001-\d+\.png$",n))
                if not names: raise ValueError("No archived G0001 stills")
                clips=[]
                for i,name in enumerate(names):
                    img=Path(d)/f"{i}.png";img.write_bytes(z.read(name))
                    clip=Path(d)/f"{i}.mp4"
                    step=re.search(r"(\d+)\.png$",name)[1]
                    encode(["-loop","1","-framerate","24","-i",str(img),"-t","2","-vf",f"scale=720:720,pad=1280:720:280:0:color=0x101c29,setsar=1,drawtext=fontfile={FONT}:text='Archived still | step {int(step)}':fontcolor=white:fontsize=24:x=15:y=20"],clip)
                    clips.append(clip)
                c=Path(d)/"concat.txt";c.write_text("".join(f"file '{x.name}'\n" for x in clips))
                run("ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(c),"-c","copy",str(p))
            else:
                names=[n for n in z.namelist() if n.endswith("result.json")]
                if len(names)!=1: raise ValueError("Expected G0026 result")
                data=json.loads(z.read(names[0]))
                if data.get("n")!=24 or data.get("steps")!=4800 or not data.get("observer_verification","").startswith("passed"): raise ValueError("Full verification missing")
                from matplotlib import pyplot as plt
                fig,axes=plt.subplots(1,2,figsize=(12.8,7.2),layout="constrained")
                m=data["final"];edges=m["histogram_edges"];counts=m["histogram"]
                axes[0].stairs(counts,edges,fill=True);axes[0].set(xlabel="Matrix concentration",ylabel="Cells",title="Final concentration distribution")
                axes[1].bar(list(m["coverage"]),[100*v for v in m["coverage"].values()]);axes[1].set(xlabel="Threshold",ylabel="Global occupancy (%)",title="Threshold sensitivity")
                fig.suptitle("G0026 | Verified headless experiment | 24^4 / 4800 steps")
                img=Path(d)/"summary.png";fig.savefig(img,dpi=100);plt.close(fig)
                encode(["-loop","1","-framerate","24","-i",str(img),"-t","8","-vf","setsar=1"],p)

def source(gen,artifact):
    name=f"video-{gen}-{artifact}.mp4"
    p=OUT/name
    if not p.exists():
        result=subprocess.run(["gh","release","download","atlas-media","--repo",REPO,"-p",name,"-D",str(OUT)],capture_output=True)
        if result.returncode and gen in ("0001","0026"):
            special_source(gen,artifact,p)
        elif result.returncode:
            with tempfile.TemporaryDirectory() as d:
                raw=Path(d)/"payload"
                with raw.open("wb") as f:
                    subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{artifact}/zip"],stdout=f,check=True)
                if zipfile.is_zipfile(raw):
                    with zipfile.ZipFile(raw) as z:
                        names=[n for n in z.namelist() if n.lower().endswith(".mp4")]
                        if len(names)!=1: raise ValueError("Expected one MP4")
                        p.write_bytes(z.read(names[0]))
                else: p.write_bytes(raw.read_bytes())
    info=probe(p)
    if not any(s["codec_type"]=="video" for s in info["streams"]): raise ValueError(f"No video: {gen}")
    return p,info
def encode(args,p):
    run("ffmpeg","-v","error","-y",*args,"-an","-c:v","libx264","-preset","medium","-crf","21","-pix_fmt","yuv420p","-r","24","-video_track_timescale","12288","-movflags","+faststart",str(p))
def card(lines,p,seconds):
    filters=[]
    for i,line in enumerate(lines):
        t=OUT/f"title-{i}.txt";t.write_text(line)
        filters.append(f"drawtext=fontfile={FONT}:textfile={t}:expansion=none:fontcolor=0xe5eff5:fontsize={48 if i==0 else 26}:x=(w-tw)/2:y={280+i*85}")
    encode(["-f","lavfi","-i",f"color=c=0x101c29:s=1280x720:r=24:d={seconds}","-vf",",".join(filters)],p)
def main():
    discover()
    segments=[]; records=[]
    intro=OUT/"intro.mp4"
    card(["ONTOGENESIS","A computational evolution","Independent experiments in chronological order"],intro,5)
    segments.append(intro)
    for gen,artifact in sorted(manifest.items()):
        p,info=source(gen,artifact)
        title=OUT/f"chapter-{gen}.mp4"; clip=OUT/f"clip-{gen}.mp4"
        subtitle=("Archived still sequence" if gen=="0001" else
                  "Measured summary, not simulation footage" if gen=="0026" else
                  "Cinematic small-domain preview / 12^4 / not mature-life evidence"
                  if gen=="0028" and artifact==14675921895 else
                  "Cinematic master / 24^4" if gen=="0028" else
                  "Independent numerical experiment")
        card([f"GENERATION {gen}",titles.get(gen,""),subtitle],title,2.5)
        encode(["-i",str(p),"-vf","fps=24,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101c29,setsar=1"],clip)
        segments.extend([title,clip])
        records.append(dict(generation=gen,artifact=artifact,kind="archived_stills" if gen=="0001" else "measured_summary" if gen=="0026" else "cinematic_preview" if gen=="0028" and artifact==14675921895 else "cinematic_master" if gen=="0028" else "original_video",source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_duration=float(info["format"]["duration"]),normalized_duration=float(probe(clip)["format"]["duration"]),source=p.name))
    end=OUT/"end.mp4";card(["ONTOGENESIS","End of verified video sequence","See the scientific monograph for methods and limitations"],end,5);segments.append(end)
    concat=OUT/"concat.txt";concat.write_text("".join(f"file '{p.name}'\n" for p in segments))
    film=OUT/"ontogenesis-evolution.mp4"
    run("ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(film))
    (OUT/"film-provenance.json").write_text(json.dumps(dict(generations=records,missing=[f"{i:04d}" for i in range(1,max(map(int,manifest))+1) if f"{i:04d}" not in manifest],film=probe(film)["format"]),indent=2))
if __name__=="__main__":main()
