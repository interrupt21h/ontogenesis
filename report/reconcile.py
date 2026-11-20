"""Reconcile a successful main-branch experiment with publication indexes."""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)

run_id=sys.argv[1]
repo=os.environ["GITHUB_REPOSITORY"]
run=json.loads(gh("api",f"repos/{repo}/actions/runs/{run_id}"))
match=re.fullmatch(r"Generation (\d{4})",run["name"])
if not match or run["conclusion"]!="success" or run["head_branch"]!="main" or run["head_repository"]["full_name"]!=repo:
    sys.exit("Not a successful trusted main experiment")
gen=match[1]
artifacts=json.loads(gh("api",f"repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"))["artifacts"]
def artifact(name):
    matches=[a for a in artifacts if a["name"]==name and not a["expired"]]
    if len(matches)!=1: raise RuntimeError(f"Expected one artifact {name}")
    return matches[0]
video=artifact("evolution.mp4")
diag=artifact("generation-"+gen+("-combined" if gen=="0023" else ""))
base=f"https://github.com/{repo}/actions/runs/{run_id}"
url=f"{base}/artifacts/{video['id']}"
manifest=Path("report/videos.json")
videos=json.loads(manifest.read_text())
# Do not regress a generation to an older rerun.
if int(videos.get(gen,0))>=video["id"]: sys.exit(0)
with tempfile.TemporaryDirectory() as tmp:
    gh("run","download",run_id,"-n",diag["name"],"-D",tmp)
    files=list(Path(tmp).rglob("metrics.json"))
    if len(files)!=1: raise RuntimeError("Expected one metrics file")
    data=json.loads(files[0].read_text())
    final=data[-1] if isinstance(data,list) else data
    if not isinstance(final,dict) or final.get("step")!=4800: raise RuntimeError("Missing final step")
    metrics={k:v for k,v in final.items() if isinstance(v,(int,float)) and not isinstance(v,bool)}
    if not metrics: raise RuntimeError("No scalar metrics")
    lines=["","<!-- AUTO-CI-BEGIN -->","","### Automated CI verification","",f"[Successful run]({base}) · [Standalone MP4]({url}) · [Diagnostics]({base}/artifacts/{diag['id']}). Source revision: `{run['head_sha']}`.","", "| Final metric | Value |","|---|---:|"]
    lines += [f"| {k.replace('_',' ')} | {v:.9g} |" for k,v in metrics.items()]
    lines += ["","<!-- AUTO-CI-END -->",""]
    block="\n".join(lines)
def update_record(s):
    s=re.sub(r"(?im)^Status:.*pending.*$","Status: CI verified — successful execution.",s)
    s=re.sub(r"(?i)\b(?:Results pending|Pending execution|Pending CI)\.", "Verified CI results are recorded below.",s)
    s=re.sub(r"(?s)<!-- AUTO-CI-BEGIN -->.*?<!-- AUTO-CI-END -->\n?","",s)
    return s.rstrip()+"\n"+block+"\n"
doc=Path(f"docs/generations/{gen}.md")
history=Path("docs/HISTORY.md")
h=history.read_text()
pattern=rf"(?ms)^## Generation {gen}[^\n]*\n.*?(?=^## |\Z)"
m=re.search(pattern,h)
if not m or not doc.exists(): raise RuntimeError("Missing generation documentation")
doc.write_text(update_record(doc.read_text()))
history.write_text(h[:m.start()]+update_record(m[0])+"\n"+h[m.end():])
videos[gen]=video["id"]
manifest.write_text(json.dumps(videos,indent=2,sort_keys=True)+"\n")
readme=Path("README.md")
s=readme.read_text()
s=re.sub(rf"(\| {gen} \|[^\n]*?)Pending verification",r"\1Verified",s)
if gen==max(videos):
    row=next(x for x in s.splitlines() if x.startswith(f"| {gen} |"))
    workflow=re.search(r"\[Runs\]\(([^)]+)\)",row)[1]
    title=doc.read_text().splitlines()[0].removeprefix("# ")
    s=re.sub(r"## Latest verified animation[^\n]*\n\n[^\n]*",lambda _:f"## Latest verified animation — {title}\n\n[Download standalone MP4]({url}) ({video['size_in_bytes']/1048576:.2f} MiB) · [Workflow](https://github.com/{repo}/actions/workflows/{Path(workflow).name})",s)
readme.write_text(s)
