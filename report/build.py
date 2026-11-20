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
phase_text = {1:"The initial experiments establish the visual language of the work: chemical reactions generate patterns without predefined objects. Competition and spatial bias then introduce differentiation between regions.",4:"Transport changes the question from where patterns form to how they move and reorganize. Feedback couples chemical activity to circulation, while volumetric experiments extend the spatial domain.",8:"Activity begins to modify its own conditions through energy consumption, matrix construction and excitation. Persistent organization becomes an observable property rather than a purely visual impression.",12:"An additional spatial coordinate makes direct observation incomplete. Tracking and simultaneous sections introduce instruments for distinguishing structural persistence from apparent motion.",15:"Inherited variation moves the inquiry from environmental memory toward selection. Metabolic coupling and matrix construction expose competing demands on persistence and growth.",18:"Structural saturation and collapse motivate selective permeability and topology. Connectivity, interfaces and complementary regions provide measurements beyond visual resemblance.",21:"Threshold-dependent topology and inherited construction motivate controlled experiments on how populations modify their own environments. Genetic specialization separates construction from signal response."}
base = "https://github.com/interrupt21h/ontogenesis/blob/main/"
def convert(text):
    text = re.sub(r"```math\n(.*?)\n```", lambda m: "$$\n"+m[1]+"\n$$", text, flags=re.S)
    text = re.sub(r"\]\(\.\./([^\s)]+)\)", lambda m: "]("+base+m[1]+")", text)
    return text

revision = subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
intro = (ROOT / "report/introduction.md").read_text()
def raw_latex(code):
    return "\n\n" + chr(96)*3 + "{=latex}\n" + code + "\n" + chr(96)*3 + "\n\n"

def frame_section(n):
    manifest=json.loads((ROOT/"report/videos.json").read_text())
    artifact=manifest.get(n)
    if artifact is None or n == "0013":
        return ""
    folder=out/"frames"/f"{n}-{artifact}"
    if not (folder/"frames.json").exists():
        return ""
    meta=json.loads((folder/"frames.json").read_text())
    labels=("Early development","Intermediate development","Final development")
    paths=[f"frames/{n}-{artifact}/{i}.jpg" for i in range(3)]
    def picture(path,width,height):
        return r"\includegraphics[width="+width+",height="+height+r",keepaspectratio]{"+path+"}"
    def caption(i):
        return labels[i]+" --- frame "+str(meta["indices"][i]+1)
    provenance=r"\par\smallskip{\footnotesize Source animation artifact "+str(artifact)+r". Playback indices, not integration steps. \par}"
    if int(n)<14:
        panels=[r"\begin{minipage}[t]{.48\linewidth}\centering "+picture(paths[i],r"\linewidth",r".25\textheight")+r"\par\small "+caption(i)+r"\end{minipage}" for i in (0,1)]
        block=r"\par\Needspace{.68\textheight}\AtlasPlateHeading{"+n+r"}{Development sequence}{"+str(meta["count"])+r" total}\noindent "+r"\hfill ".join(panels)+r"\par\medskip\begin{center}"+picture(paths[2],r".76\linewidth",r".32\textheight")+r"\par\small "+caption(2)+r"\end{center}"+provenance
        return raw_latex(block)
    from PIL import Image
    result=[]
    for i,path in enumerate(paths):
        block=r"\clearpage\AtlasPlateHeading{"+n+"}{"+labels[i]+"}{"+str(meta["indices"][i]+1)+" / "+str(meta["count"])+r"}\noindent "+picture(path,r"\linewidth",r".36\textheight")+r"\par\medskip "
        with Image.open(out/path) as im:
            if im.size==(1280,720):
                panels=[]
                for tag,rect,caption_text in (("chemistry",(14,110,495,575),"A. Chemistry view"),("identity",(510,110,985,575),"B. Identity view")):
                    detail=Path(path).with_name(f"{i}-{tag}.png")
                    im.crop(rect).save(out/detail)
                    panels.append(r"\begin{minipage}[t]{.48\linewidth}\centering "+picture(str(detail),r"\linewidth",r".30\textheight")+r"\par\small "+caption_text+r"\end{minipage}")
                block+=r"\noindent "+r"\hfill ".join(panels)+r"\par\smallskip{\footnotesize Detail views show distinct spatial sections; identity colors denote tracked structural components.\par}"
        result.append(raw_latex(block+provenance))
    return "\n".join(result)

subprocess.run([os.sys.executable, str(ROOT / 'report/atlas.py')],check=True)
body = [re.sub(r"(?m)^## (.+)$",r"## \1 {.unnumbered}",intro.replace("# Vision and method","# Vision and method {.unnumbered}",1))]
for n,title,record in records:
    if int(n) in groups:
        phase_end=next((k-1 for k in groups if k>int(n)),len(records))
        manifest=json.loads((ROOT/"report/videos.json").read_text())
        images=[]
        for g in range(int(n),phase_end+1):
            key=f"{g:04d}"
            p=out/"frames"/f"{key}-{manifest.get(key)}"/"2.jpg"
            if p.exists():
                images.append(r"\begin{minipage}[t]{.47\linewidth}\centering\includegraphics[width=\linewidth,height=.23\textheight,keepaspectratio]{"+str(p.relative_to(out))+r"}\par\small Generation "+key+r"\end{minipage}")
        rows=[r"\noindent"+r"\hfill".join(images[i:i+2])+r"\par\medskip" for i in range(0,min(len(images),6),2)]
        body.append(raw_latex(r"\clearpage\part{"+groups[int(n)]+"}"+r"\par{\sffamily\large Generations "+n+"--"+f"{phase_end:04d}"+r"}\par\medskip "+phase_text[int(n)]+r"\par\bigskip "+ "\n".join(rows)+r"\par{\small Final sampled frames from verified animations.\par}\clearpage"))
    record = re.sub(r"(?ms)^### Reproduction and provenance\n(.*?)(?=^### |\Z)", lambda m: "\n\n**Experiment sources:** " + " · ".join(line.strip()[2:] for line in m[1].splitlines() if line.strip().startswith("- ") and "Run from repository" not in line) + "\n\n", record)
    record = re.sub(r"(?m)^[-*] Run from repository root:.*\n?", "", record)
    # Only normalize plain prose, never existing math or code.
    pieces = re.split(r"(```[\s\S]*?```|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|`[^`\n]+`)", record)
    for i in range(0,len(pieces),2):
        pieces[i] = re.sub(r"(?<![\w$])(\d+)\^([234])(?![\w$])",lambda m: "$"+m[1]+"^{"+m[2]+"}$",pieces[i])
    record = "".join(pieces)
    if "Verified CI outcome" in record or "Verified factorial outcome" in record or "Verified outcome" in record:
        record = re.sub(r"(?im)^Status: (?:CI )?pending[^\n]*$", "Status: verified outcome recorded below.", record)
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
        body.append(raw_latex(r"\par\Needspace{.31\textheight}\section{Analytical plate}\centering\includegraphics[width=\linewidth,height=.32\textheight,keepaspectratio]{atlas/"+n+r"-atlas.pdf}\end{center}"))
    body.append(frame_section(n))
body.append((ROOT/"report/synthesis.md").read_text().replace("\n## ","\n## ").replace("## What the experiments establish","## What the experiments establish {.unnumbered}").replace("## The limits of observation","## The limits of observation {.unnumbered}").replace("## Continuing the inquiry","## Continuing the inquiry {.unnumbered}"))
body.append("## Provenance {.unnumbered}\n\nSource revision: `"+revision+"`. The source revision identifies the published model and experimental records. Numerical results refer to the configurations described in each chapter. Analytical diagrams describe model relationships; simulation views depict sampled numerical states.")
(out/"report.md").write_text("\n\n".join(body))
subprocess.run(["pandoc",str(out/"report.md"),"--standalone","--toc","--toc-depth=1","--number-sections","--top-level-division=chapter","--metadata","documentclass=report","--metadata","title=Ontogenesis: Computational Emergence","--metadata","subtitle=Living scientific and engineering monograph","--metadata","author=Scott Muller — Ontogenesis Project","--variable","geometry:margin=25mm","--variable","fontsize=11pt","--include-in-header=report/preamble.tex","-o",str(out/"ontogenesis.tex")],check=True)
tex=out/"ontogenesis.tex"
subprocess.run([os.sys.executable,str(ROOT/"report/cover_art.py")],check=True)
raw=tex.read_text()
custom=r"""\begin{titlepage}
\thispagestyle{empty}
\begin{tikzpicture}[remember picture,overlay]
\node[inner sep=0pt] at (current page.center) {\includegraphics[width=\paperwidth,height=\paperheight]{cover.png}};
\node[anchor=north west,text=white,font=\sffamily\small] at ([xshift=25mm,yshift=-24mm]current page.north west) {COMPUTATIONAL SCIENCE ATLAS};
\node[anchor=north west,text=white,font=\sffamily\bfseries\fontsize{39}{44}\selectfont] at ([xshift=23mm,yshift=-40mm]current page.north west) {ONTOGENESIS};
\node[anchor=north west,text=white,font=\sffamily\Large] at ([xshift=25mm,yshift=-60mm]current page.north west) {Computational emergence};
\node[anchor=south west,text=white,font=\sffamily\large] at ([xshift=25mm,yshift=30mm]current page.south west) {Scott Muller};
\node[anchor=south west,text=white,font=\sffamily\small] at ([xshift=25mm,yshift=23mm]current page.south west) {Living experimental monograph};
\node[anchor=south west,text=white,font=\sffamily\scriptsize] at ([xshift=25mm,yshift=15mm]current page.south west) {Generative cover artwork --- not experimental data};
\end{tikzpicture}\null
\end{titlepage}"""
preamble,marker,document=raw.partition(r"\begin{document}")
assert marker
document,count=re.subn(r"(?m)^[ \t]*\\maketitle[ \t]*$",lambda _:custom,document,count=1)
assert count==1
tex.write_text(preamble+marker+document)
subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","ontogenesis.tex"],cwd=out,check=True)
