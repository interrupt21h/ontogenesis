"""Assemble verified generation videos, preserving each source's playback duration."""
import json, re, subprocess, zipfile, tempfile, hashlib
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
def source(gen,artifact):
    name=f"video-{gen}-{artifact}.mp4"
    p=OUT/name
    if not p.exists():
        result=subprocess.run(["gh","release","download","atlas-media","--repo",REPO,"-p",name,"-D",str(OUT)],capture_output=True)
        if result.returncode:
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
    run("ffmpeg","-v","error","-y",*args,"-an","-c:v","libx264","-preset","medium","-crf","21","-pix_fmt","yuv420p","-r","24","-movflags","+faststart",str(p))
def card(lines,p,seconds):
    filters=[]
    for i,line in enumerate(lines):
        t=OUT/f"title-{i}.txt";t.write_text(line)
        filters.append(f"drawtext=fontfile={FONT}:textfile={t}:expansion=none:fontcolor=0xe5eff5:fontsize={48 if i==0 else 26}:x=(w-tw)/2:y={280+i*85}")
    encode(["-f","lavfi","-i",f"color=c=0x101c29:s=1280x720:r=24:d={seconds}","-vf",",".join(filters)],p)
def main():
    segments=[]; records=[]
    intro=OUT/"intro.mp4"
    card(["ONTOGENESIS","A computational evolution","Independent experiments in chronological order"],intro,5)
    segments.append(intro)
    for gen,artifact in sorted(manifest.items()):
        p,info=source(gen,artifact)
        title=OUT/f"chapter-{gen}.mp4"; clip=OUT/f"clip-{gen}.mp4"
        card([f"GENERATION {gen}",titles.get(gen,""),"Independent numerical experiment"],title,2.5)
        encode(["-i",str(p),"-vf","fps=24,scale=1280:720:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x101c29,setsar=1"],clip)
        segments.extend([title,clip])
        records.append(dict(generation=gen,artifact=artifact,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_duration=float(info["format"]["duration"]),normalized_duration=float(probe(clip)["format"]["duration"]),source=p.name))
    end=OUT/"end.mp4";card(["ONTOGENESIS","End of verified video sequence","See the scientific monograph for methods and limitations"],end,5);segments.append(end)
    concat=OUT/"concat.txt";concat.write_text("".join(f"file '{p.name}'\n" for p in segments))
    film=OUT/"ontogenesis-evolution.mp4"
    run("ffmpeg","-v","error","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(film))
    (OUT/"film-provenance.json").write_text(json.dumps(dict(generations=records,missing=[f"{i:04d}" for i in range(1,max(map(int,manifest))+1) if f"{i:04d}" not in manifest],film=probe(film)["format"]),indent=2))
if __name__=="__main__":main()
