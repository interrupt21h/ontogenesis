"""Extract deterministic, provenance-labelled frame samples from verified artifacts."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/build/frames"
OUT.mkdir(parents=True, exist_ok=True)
REPO = "interrupt21h/ontogenesis"
manifest = json.loads((ROOT / "report/videos.json").read_text())
for gen, artifact in sorted(manifest.items()):
    target = OUT / f"{gen}-{artifact}"
    metadata = target / "frames.json"
    if gen!="0024" and metadata.exists() and json.loads(metadata.read_text()).get("native_resolution") and all((target / f"{i}.jpg").is_file() for i in range(3)):
        continue
    target.mkdir(exist_ok=True)
    archival = f"frames-{gen}-{artifact}.zip"
    with tempfile.TemporaryDirectory() as cache:
        result = subprocess.run(["gh","release","download","atlas-media","--repo",REPO,"--pattern",archival,"--dir",cache],capture_output=True)
        if result.returncode == 0 and gen!="0024":
            with zipfile.ZipFile(Path(cache)/archival) as z:
                for name in ("0.jpg","1.jpg","2.jpg","frames.json"):
                    (target/name).write_bytes(z.read(name))
            if json.loads(metadata.read_text()).get("native_resolution"):
                continue
    try:
        with tempfile.TemporaryDirectory() as tmp:
            payload = Path(tmp) / "artifact"
            with payload.open("wb") as f:
                subprocess.run(["gh", "api", f"repos/{REPO}/actions/artifacts/{artifact}/zip"], stdout=f, check=True)
            video = payload
            if zipfile.is_zipfile(payload):
                with zipfile.ZipFile(payload) as z:
                    names = [n for n in z.namelist() if n.lower().endswith(".mp4")]
                    if len(names) != 1:
                        raise ValueError("Expected exactly one MP4")
                    video = Path(tmp) / "video.mp4"
                    video.write_bytes(z.read(names[0]))
            info = json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-count_frames","-show_entries","stream=nb_read_frames,avg_frame_rate","-of","json",str(video)]))
            count = int(info["streams"][0]["nb_read_frames"])
            if count < 1:
                raise ValueError("Empty video")
            indices = [0,152,count-1] if gen=="0024" and count==1201 else [round((count-1)*p) for p in (0,.5,1)]
            for i, index in enumerate(indices):
                subprocess.run(["ffmpeg","-v","error","-y","-i",str(video),"-vf",f"select=eq(n\\,{index}),null","-frames:v","1","-q:v","2",str(target / f"{i}.jpg")],check=True)
                if not (target / f"{i}.jpg").is_file():
                    raise ValueError("Missing extracted frame")
            metadata.write_text(json.dumps({"native_resolution":True,"artifact":artifact,"count":count,"indices":indices,"rate":info["streams"][0]["avg_frame_rate"]}))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"::warning::Generation {gen}: frames unavailable: {exc}")
