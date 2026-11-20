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
    provenance=r"\par\smallskip{\footnotesize Source animation artifact "+str(artifact)+r". Frame numbers refer to playback order, not integration steps. \par}"
    if int(n)<14:
        panels=[r"\begin{minipage}[t]{.48\linewidth}\centering "+picture(paths[i],r"\linewidth",r".25\textheight")+r"\par\small "+caption(i)+r"\end{minipage}" for i in (0,1)]
        block=r"\par\Needspace{.68\textheight}\AtlasPlateHeading{"+n+r"}{Development sequence}{"+str(meta["count"])+r" total}\noindent "+r"\hfill ".join(panels)+r"\par\medskip\begin{center}"+picture(paths[2],r".76\linewidth",r".32\textheight")+r"\par\small "+caption(2)+r"\end{center}"+provenance
        return raw_latex(block)
    from PIL import Image
    # One chronological context plate and a full-width endpoint detail plate.
    rows=[]
    for i in (0,1):
        rows.append(r"\begin{minipage}{\linewidth}\centering "+picture(paths[i],r"\linewidth",r".195\textheight")+r"\par\small "+caption(i)+r"\end{minipage}\par\smallskip")
    rows.append(r"\begin{minipage}{\linewidth}\centering "+picture(paths[2],r"\linewidth",r".195\textheight")+r"\par\small "+caption(2)+r"\end{minipage}\par\smallskip")
    context=raw_latex(r"\clearpage\AtlasPlateHeading{"+n+r"}{Development sequence}{"+str(meta["count"])+r" total}"+"".join(rows)+provenance)
    with Image.open(out/paths[2]) as im:
        if im.size!=(1280,720):
            return context
        panels=[]
        for tag,rect,label in (("chemistry",(14,110,495,575),"Chemistry section"),("identity",(510,110,985,575),"Identity section")):
            detail=Path(paths[2]).with_name("final-"+tag+".png")
            im.crop(rect).save(out/detail)
            panels.append(r"\begin{center}"+picture(str(detail),r".95\linewidth",r".32\textheight")+r"\par\small "+label+r"\end{center}")
    return context+raw_latex(r"\clearpage\AtlasPlateHeading{"+n+r"}{Final spatial sections}{"+str(meta["indices"][2]+1)+r"}"+"".join(panels)+r"\par\small Distinct fourth-coordinate sections, enlarged without interpolation of new scientific detail."+provenance)

def research_plate(name,heading,caption):
    return raw_latex(r"\par\Needspace{.43\textheight}\section*{"+heading+r"}\begin{center}\includegraphics[width=\linewidth,height=.48\textheight,keepaspectratio]{atlas/"+name+r".pdf}\end{center}\noindent "+caption+r"\par")

subprocess.run([os.sys.executable, str(ROOT / 'report/atlas.py')],check=True)
subprocess.run([os.sys.executable,str(ROOT/'report/research_atlas.py')],check=True)
body = [re.sub(r"(?m)^## (.+)$",r"## \1 {.unnumbered}",intro.replace("# Vision and method","# Vision and method {.unnumbered}",1))]
body.append(research_plate("research-genealogy","The genealogy of the investigation","Each revision inherits or extends a computational model. Amber marks revisions concentrated on instruments or controls. This chronology is not a biological genealogy."))
for n,title,record in records:
    if int(n) in groups:
        phase_end=next((k-1 for k in groups if k>int(n)),len(records))
        manifest=json.loads((ROOT/"report/videos.json").read_text())
        phase_index=list(groups).index(int(n))
        roman=("I","II","III","IV","V","VI","VII")[phase_index]
        images=[]
        for g in range(int(n),phase_end+1):
            key=f"{g:04d}"
            p=out/"frames"/f"{key}-{manifest.get(key)}"/"2.jpg"
            if p.exists():
                images.append((key,str(p.relative_to(out)),records[g-1][1]))
        # A full-page dark editorial opening, with independent conceptual and empirical panels.
        concepts={1:("LOCAL REACTIONS", "Spatial differentiation", "Competition for substrate"),4:("CONSERVATIVE FLUX", "Transport across faces", "Feedback from chemistry"),8:("LOCAL ENVIRONMENT", "Energy and matrix", "Excitation and memory"),12:("SPATIAL SECTIONS", "Fourth-axis sampling", "Identity across observations"),15:("INHERITED VARIATION", "Mutation and selection", "Metabolic exchange"),18:("STRUCTURAL GEOMETRY", "Selective permeability", "Periodic connectivity"),21:("NICHE CONSTRUCTION", "Inherited construction", "Matched experimental controls")}
        tag,left,right=concepts[int(n)]
        concept=r"\begin{tikzpicture}[x=1cm,y=1cm]\draw[phaseaccent,line width=1.5pt] (0,0) -- (12,0);"
        for j,label in enumerate((left,right)):
            x=3+6*j
            concept+=r"\node[draw=phaseaccent,rounded corners=3pt,minimum width=5.5cm,minimum height=1.2cm,text=white,font=\sffamily\small,align=center] at ("+str(x)+r",0) {"+label+r"};"
        concept+=r"\end{tikzpicture}"
        rows=[]
        for i in range(0,len(images),2):
            tiles=[]
            for key,path,title in images[i:i+2]:
                tiles.append(r"\begin{minipage}[t]{.48\linewidth}\centering\includegraphics[width=\linewidth,height=.175\textheight,keepaspectratio]{"+path+r"}\par{\sffamily\small\bfseries\color{white} "+key+r" / "+title+r"}\end{minipage}")
            rows.append(r"\noindent\hfill"+r"\hfill".join(tiles)+r"\hfill\null\par\medskip")
        body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{phase"+roman+r"}\pagecolor{phaseblack}\color{white}\thispagestyle{empty}\refstepcounter{part}\addcontentsline{toc}{part}{\thepart\quad "+groups[int(n)]+r"}\PhaseBand{"+roman+"}{"+n+"--"+f"{phase_end:04d}"+r"}{\sffamily\bfseries\fontsize{32}{36}\selectfont "+groups[int(n)]+r"\par}\medskip{\sffamily\large "+phase_text[int(n)]+r"\par}\vfill{\sffamily\bfseries\small "+tag+r" / CONCEPTUAL RELATIONSHIP\par}\medskip\noindent\hfill"+concept+r"\hfill\null\par\vfill"+"\n".join(rows)+r"{\sffamily\footnotesize Sampled experimental frames.\par}\clearpage\nopagecolor\color{black}"))
    record = re.sub(r"(?ms)^### Reproduction and provenance\n(.*?)(?=^### |\Z)", lambda m: "\n\n**Experiment sources:** " + " · ".join(line.strip()[2:] for line in m[1].splitlines() if line.strip().startswith("- ") and "Run from repository" not in line) + "\n\n", record)
    record = re.sub(r"(?m)^[-*] Run from repository root:.*\n?", "", record)
    # Only normalize plain prose, never existing math or code.
    pieces = re.split(r"(```[\s\S]*?```|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|`[^`\n]+`)", record)
    for i in range(0,len(pieces),2):
        pieces[i] = re.sub(r"(?<![\w$])(\d+)\^([234])(?![\w$])",lambda m: "$"+m[1]+"^{"+m[2]+"}$",pieces[i])
    record = "".join(pieces)
    if "Verified CI outcome" in record or "Verified factorial outcome" in record or "Verified outcome" in record:
        record = re.sub(r"(?im)^Status: (?:CI )?pending[^\n]*$", "Status: verified outcome recorded below.", record)
    atlas=out / "atlas" / f"{n}-atlas.svg"
    if atlas.exists():
        subprocess.run(["rsvg-convert","-f","pdf","-o",str(atlas.with_suffix(".pdf")),str(atlas)],check=True)
        analytical=raw_latex(r"\par\section{Analytical plate}\nopagebreak\begin{center}\includegraphics[width=\linewidth,height=.32\textheight,keepaspectratio]{atlas/"+n+r"-atlas.pdf}\end{center}")
    else:
        analytical=""
    chapter=convert(re.sub(r"^### ","## ",record,flags=re.M))
    if analytical:
        anchor=re.search(r"(?m)^## Interpretation and limitations",chapter)
        if anchor:
            chapter=chapter[:anchor.start()]+analytical+chapter[anchor.start():]
        else:
            chapter+=analytical
    body.append("\\setcounter{chapter}{"+str(int(n)-1)+"}\n\n# Generation "+n+" — "+title+"\n\n"+chapter)
    figure=ROOT / 'docs' / 'figures' / f'{n}.svg'
    if figure.exists() and "CONCEPTUAL MECHANISM" not in figure.read_text().upper():
        target=out / "mechanisms"
        target.mkdir(exist_ok=True)
        subprocess.run(["rsvg-convert","-f","pdf","-o",str(target / f"{n}.pdf"),str(figure)],check=True)
        body.append('## Mechanism illustration\n\n'+r'\begin{center}\includegraphics[width=.92\linewidth]{mechanisms/'+n+r'.pdf}\end{center}')
    plot=ROOT / "report" / "plots" / f"{n}.tex"
    if plot.exists():
        body.append("## Quantitative atlas\n\n"+plot.read_text())
    if n=="0012":
        body.append(research_plate("spatial-sections","Observing four spatial dimensions","The periodic fourth coordinate indexes three-dimensional sections. The two observatory views introduced in Generation 0014 are separated by half the domain; they need not depict the same structures."))
    if n=="0021":
        body.append(research_plate("threshold-profile","Threshold-dependent organization","Measured final G0021 profile. The Euler characteristic and coverage describe different properties; neither alone establishes functional compartments."))
    if n=="0024":
        body.append(research_plate("genetic-architecture","Independent inherited traits","Sixteen genotypes per species form a four-dimensional binary mutation graph. Independence here means separate encoded loci, not statistically independent allele frequencies."))
    if n=="0024" and (out/"atlas/0024-field-evolution.pdf").exists():
        for suffix,heading,caption in [
            ("field-evolution","Numerical development","Native x-y sections at fixed fourth and third coordinates; color scales are fixed over all five sampled steps for each field."),
            ("field-projections","Projected chemical environment","Mean concentrations over the fourth and third axes. These projections are not individual spatial sections."),
            ("trait-landscape","Spatial distribution of heredity","Local population-weighted allele fractions; cells with negligible total population are undefined."),
            ("structural-volume","Structural occupancy in three dimensions","Native cell centers above matrix threshold 0.20 in two fourth-coordinate sections. The rectangular cut does not reveal all periodic connections."),
            ("field-metrics","Measured developmental trajectories","Global coverage and allele frequencies independently recomputed from five archived numerical states. Connecting lines guide the eye between samples.")]:
            body.append(research_plate("0024-"+suffix,heading,caption))
    body.append(frame_section(n))
body.append((ROOT/"report/synthesis.md").read_text().replace("## What the experiments establish","## What the experiments establish {.unnumbered}").replace("## The limits of observation","## The limits of observation {.unnumbered}").replace("## Continuing the inquiry","## Continuing the inquiry {.unnumbered}"))
body.append(research_plate("comparative-endpoints","Comparative experimental evidence","Upper: descriptive historical endpoints, not a controlled contrast. Lower: four matched-seed G0023 arms; the cost treatment bundles two penalties. All matrix values use threshold 0.20."))
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
