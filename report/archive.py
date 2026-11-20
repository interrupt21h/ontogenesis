"""Store native frame samples as durable release assets."""
from pathlib import Path
import json
import subprocess
import tempfile
import zipfile
root=Path(__file__).resolve().parent
for gen,artifact in json.loads((root/"videos.json").read_text()).items():
    folder=root/"build"/"frames"/f"{gen}-{artifact}"
    meta=folder/"frames.json"
    if not meta.exists() or not json.loads(meta.read_text()).get("native_resolution"):
        continue
    with tempfile.TemporaryDirectory() as tmp:
        asset=Path(tmp)/f"frames-{gen}-{artifact}.zip"
        with zipfile.ZipFile(asset,"w",zipfile.ZIP_DEFLATED) as z:
            for name in ("0.jpg","1.jpg","2.jpg","frames.json"):
                z.write(folder/name,name)
        subprocess.run(["gh","release","upload","atlas-media",str(asset),"--clobber"],check=True)
