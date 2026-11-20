"""Build the living monograph from canonical repository records."""
from pathlib import Path
import re
import subprocess
import os
import json

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
out = ROOT / "report" / "build"
out.mkdir(parents=True, exist_ok=True)
history = (ROOT / "docs/HISTORY.md").read_text()
records = re.findall(r"^## Generation (\d{4}) — (.+?)\n(.*?)(?=^## Generation |^## Research priorities|\Z)", history, re.M|re.S)
assert records and [int(n) for n,_,_ in records] == list(range(1,len(records)+1)), "Missing or unordered generations"
assert all((ROOT / f"docs/generations/{n}.md").exists() for n,_,_ in records)
groups = {1:"Chemical differentiation",4:"Transport and volumetric dynamics",8:"Energy, organization and signaling",12:"Higher-dimensional geometry and identity",15:"Heredity and ecology",18:"Morphogenesis and topology",21:"Topology and evolutionary niche construction"}
base = "https://github.com/interrupt21h/ontogenesis/blob/main/"
def convert(text):
    text = re.sub(r"```math\n(.*?)\n```", lambda m: "$$\n"+m[1]+"\n$$", text, flags=re.S)
    text = re.sub(r"\]\(\.\./([^\s)]+)\)", lambda m: "]("+base+m[1]+")", text)
    return text

revision = subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
intro = (ROOT / "report/introduction.md").read_text()
method = (ROOT / "docs/METHODOLOGY.md").read_text()
method = method.replace("# Experimental methodology and documentation policy","## Repository methodology",1)
method = method.replace("](HISTORY.md)","]("+base+"docs/HISTORY.md)").replace("](GENERATION_TEMPLATE.md)","]("+base+"docs/GENERATION_TEMPLATE.md)")
def frame_section(n):
    manifest = json.loads((ROOT / "report/videos.json").read_text())
    artifact = manifest.get(n)
    if artifact is None:
        return "## Simulation frames\n\nNo verified MP4 is indexed for this generation."
    folder = out / "frames" / f"{n}-{artifact}"
    if not (folder / "frames.json").exists():
        return "## Simulation frames\n\nVerified video indexed, but frame extraction was unavailable during this build."
    meta = json.loads((folder / "frames.json").read_text())
    result = ["## Simulation frames", r"\begin{center}\begin{minipage}{\linewidth}\centering"]
    for i, label in enumerate(("Early development", "Intermediate development", "Final development")):
        path = f"frames/{n}-{artifact}/{i}.jpg"
        result.append(r"\begin{minipage}[t]{.32\linewidth}\centering\includegraphics[width=\linewidth,height=.23\textheight,keepaspectratio]{"+path+r"}\par\small "+label+r"\\ Frame "+str(meta['indices'][i]+1)+" / "+str(meta['count'])+r"\end{minipage}"+(r"\hfill" if i<2 else "")+"%")
    result.append(r"\end{minipage}\end{center}")
    result.append(f"[Source animation artifact {artifact}](https://github.com/interrupt21h/ontogenesis/actions/artifacts/{artifact}). Frames are sampled by playback index, not inferred integration step.")
    return "\n\n".join(result[:1]+["\n".join(result[1:-1])]+result[-1:])

subprocess.run([os.sys.executable, str(ROOT / 'report/atlas.py')],check=True)
body = [intro.replace("# Project overview","# Project overview {.unnumbered}",1),convert(method)]
for n,title,record in records:
    if int(n) in groups:
        body.append("\\part{"+groups[int(n)]+"}")
    body.append("\\setcounter{chapter}{"+str(int(n)-1)+"}\n\n# Generation "+n+" — "+title+"\n\n"+convert(re.sub(r"^### ","## ",record,flags=re.M)))
    figure=ROOT / 'docs' / 'figures' / f'{n}.svg'
    if figure.exists() and "CONCEPTUAL MECHANISM" not in figure.read_text().upper():
        target=out / "mechanisms"
        target.mkdir(exist_ok=True)
        subprocess.run(["rsvg-convert","-f","pdf","-o",str(target / f"{n}.pdf"),str(figure)],check=True)
        body.append('## Mechanism illustration\n\n'+r'\begin{center}\includegraphics[width=.92\linewidth]{mechanisms/'+n+r'.pdf}\end{center}')
    plot=ROOT / "report" / "plots" / f"{n}.tex"
    if plot.exists():
        body.append("## Quantitative atlas\n\n"+plot.read_text())
    atlas=out / "atlas" / f"{n}-atlas.svg"
    if atlas.exists():
        subprocess.run(["rsvg-convert","-f","pdf","-o",str(atlas.with_suffix(".pdf")),str(atlas)],check=True)
        body.append("## Analytical plate\n\n"+r"\begin{center}\includegraphics[width=.98\linewidth]{atlas/"+n+r"-atlas.pdf}\end{center}")
    body.append(frame_section(n))
body.append("# Research agenda\n\n"+history.split("## Research priorities",1)[-1])
body.append("# Provenance\n\nSource revision: `"+revision+"`. Historical records may contain original pending statements followed by verified outcomes; later verified outcomes supersede those statements. Source code remains normative. The illustrations are analytical or illustrative unless identified as measured data.")
(out/"report.md").write_text("\n\n".join(body))
subprocess.run(["pandoc",str(out/"report.md"),"--standalone","--toc","--toc-depth=1","--number-sections","--top-level-division=chapter","--metadata","documentclass=report","--metadata","title=Ontogenesis: Computational Emergence","--metadata","subtitle=Living scientific and engineering monograph","--metadata","author=Scott Muller — Ontogenesis Project","--variable","geometry:margin=25mm","--variable","fontsize=11pt","--include-in-header=report/preamble.tex","-o",str(out/"ontogenesis.tex")],check=True)
subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","ontogenesis.tex"],cwd=out,check=True)
