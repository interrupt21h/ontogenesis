"""Build the living monograph from canonical repository records."""
from pathlib import Path
import re
import subprocess
import os
import json
from editorial import prepare, links

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
out = ROOT / "report" / "build"
out.mkdir(parents=True, exist_ok=True)
history = (ROOT / "docs/HISTORY.md").read_text()
records = re.findall(r"^## Generation (\d{4}) — (.+?)\n(.*?)(?=^## Generation |^## Research priorities|\Z)", history, re.M|re.S)
assert records and [int(n) for n,_,_ in records] == list(range(1,len(records)+1)), "Missing or unordered generations"
assert all((ROOT / f"docs/generations/{n}.md").exists() for n,_,_ in records)
groups = {1:"Chemical differentiation",4:"Transport and volumetric dynamics",8:"Energy, organization and signaling",12:"Higher-dimensional geometry and identity",15:"Heredity and ecology",18:"Morphogenesis and topology",21:"Topology and evolutionary niche construction",26:"Consolidation and measurement",28:"Environmental intervention and visual synthesis"}
phase_text = {1:"The initial experiments establish the visual language of the work: chemical reactions generate patterns without predefined objects. Competition and spatial bias then introduce differentiation between regions.",4:"Transport changes the question from where patterns form to how they move and reorganize. Feedback couples chemical activity to circulation, while volumetric experiments extend the spatial domain.",8:"Activity begins to modify its own conditions through energy consumption, matrix construction and excitation. Persistent organization becomes an observable property rather than a purely visual impression.",12:"An additional spatial coordinate makes direct observation incomplete. Tracking and simultaneous sections introduce instruments for distinguishing structural persistence from apparent motion.",15:"Inherited variation moves the inquiry from environmental memory toward selection. Metabolic coupling and matrix construction expose competing demands on persistence and growth.",18:"Structural saturation and collapse motivate selective permeability and topology. Connectivity, interfaces and complementary regions provide measurements beyond visual resemblance.",21:"Threshold-dependent topology and inherited construction motivate controlled experiments on how populations modify their own environments. Genetic specialization separates construction from signal response.",26:"The focus shifts from adding mechanisms to testing observer independence and measuring continuous structure without a fixed segmentation threshold.",28:"G0028 subjects a four-dimensional system to a controlled shock. G0029's verified same-seed full-domain transport feedback increases W coverage while decreasing V and structural-matrix coverage at the endpoint; the reduced-domain pilot does not predict the larger outcome. G0030's verified ecology studies showed early loss of thresholded V activity rather than ecological succession. G0031's loss-rate frontier switched which population dominated. G0032's controlled static spatial niches retained globally active but locally separate V and W in one seed, not both. Longer stability is unproven. Numerical plots and cinematic artworks remain distinct, and none establishes biological life."}
base = "https://github.com/interrupt21h/ontogenesis/blob/main/"
def convert(text):
    text = re.sub(r"```math\n(.*?)\n```", lambda m: "$$\n"+m[1]+"\n$$", text, flags=re.S)
    text = re.sub(r"\]\((?:\.\./)+([^\s)]+)\)", lambda m: "]("+base+m[1]+")", text)
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
    labels=("Initialization","Intermediate development","Final development") if meta["indices"][0]==0 else ("Early development","Intermediate development","Final development")
    if n=="0024" and meta["indices"]==[0,152,1200]:
        labels=("Initialization (step 0)","Peak structural coverage (step 608)","Final observation (step 4800)")
    paths=[f"frames/{n}-{artifact}/{i}.jpg" for i in range(3)]
    def picture(path,width,height):
        return r"\includegraphics[width="+width+",height="+height+r",keepaspectratio]{"+path+"}"
    def caption(i):
        return labels[i]+" --- frame "+str(meta["indices"][i]+1)
    provenance=r"\par\smallskip{\footnotesize Source animation artifact "+str(artifact)+r". Frame numbers refer to playback order, not integration steps. \par}"
    from PIL import Image
    if not all((out/p).is_file() for p in paths):
        return ""
    blocks=[]
    for i,path in enumerate(paths):
        with Image.open(out/path) as im:
            w,h=im.size
        heading=("Development sequence" if i==0 else "Development sequence (continued)")
        block=r"\clearpage\AtlasPlateHeading{"+n+"}{"+heading+"}{"+str(i+1)+" of 3 | "+str(meta["count"])+r" frames in animation}"
        block+=r"\begin{center}\vspace*{.035\textheight}"+picture(path,r"\linewidth",r".70\textheight")+r"\par\medskip{\large\bfseries "+caption(i)+r"}\par\smallskip{\small Source raster: "+str(w)+" by "+str(h)+r" pixels}\end{center}"
        block+=r"\noindent "+provenance
        blocks.append(raw_latex(block))
    # Crops are explicitly labelled image regions, not claims about physical coordinates.
    if int(n)>=14 and n!="0028":
        # The G0028 fidelity frame is a single central volumetric composition.
        # Earlier dual-panel crop boxes would cut away the numerical subject.
        with Image.open(out/paths[2]) as im:
            if im.size==(1280,720):
                for tag,rect,label in (("left",(14,110,495,575),"Left visualization region"),("right",(510,110,985,575),"Right visualization region")):
                    detail=Path(paths[2]).with_name("final-detail-"+tag+".png")
                    im.crop(rect).save(out/detail)
                    blocks.append(raw_latex(r"\clearpage\AtlasPlateHeading{"+n+r"}{Final frame detail}{"+label+r"}\begin{center}"+picture(str(detail),r"\linewidth",r".65\textheight")+r"\par\medskip{\large "+label+r"}\end{center}\noindent Enlarged crop of the final playback frame; no new numerical information is inferred."+provenance))
    return "".join(blocks)

def research_plate(name,heading,caption):
    # Plates are embedded as raw TeX: bare superscripts trigger Missing $.
    if re.search(r"\b\d+\^\d+", caption):
        raise ValueError("Raw LaTeX plate caption contains an unescaped power")
    return raw_latex(r"\par\Needspace{.43\textheight}\section*{"+heading+r"}\begin{center}\includegraphics[width=\linewidth,height=.62\textheight,keepaspectratio]{atlas/"+name+r".pdf}\end{center}\noindent "+caption+r"\par")

def final_render_plate(n, title, interpretation, observed=(1,2)):
    """Two curated source-animation stills, NOT made-up numerical keyframes."""
    manifest=json.loads((ROOT/"report/videos.json").read_text())
    artifact=manifest.get(n)
    if artifact is None:
        raise RuntimeError(f"No verified media manifest entry for gallery G{n}")
    if n=="0028" and artifact!=14679397104:
        raise RuntimeError("G0028 gallery must use the selected full-resolution cinematic edition 14679397104")
    folder=out/"frames"/f"{n}-{artifact}"
    index_file=folder/"frames.json"
    if not index_file.exists():
        raise RuntimeError(f"No verified cached film frames for gallery G{n}: {artifact}")
    meta=json.loads(index_file.read_text())
    if meta["count"]<3 or len(meta["indices"])!=3:
        raise RuntimeError(f"Incomplete frame metadata for G{n}")
    plates=[]
    for index in observed:
        file=folder/f"{index}.jpg"
        if not file.is_file() or file.stat().st_size<1024:
            raise RuntimeError(f"Gallery image unavailable: {file}")
        frame=int(meta["indices"][index])+1
        seq=("INTERMEDIATE" if index==1 else
             "FINAL" if index==2 else "INITIAL")
        plates.append(
            r"\begin{center}\includegraphics[width=.96\linewidth,height=.285\textheight,keepaspectratio]{"
            +f"frames/{n}-{artifact}/{index}.jpg"
            +r"}\par\medskip{\sffamily\bfseries\small "+seq+
            f" PLAYBACK OBSERVATION  /  FRAME {frame} OF {meta['count']}"+
            r"}\end{center}\par\medskip")
    text=(
        r"\clearpage\noindent{\sffamily\small\bfseries\color{phaseaccent} "
        +f"FINAL RENDERS  /  GENERATION {n}"
        +r"}\par\medskip{\sffamily\LARGE\bfseries\color{ontoink} "
        +title+r"}\par\medskip{\color{phaseaccent}\hrule height 1.4pt}\par\medskip"
        +"".join(plates)
        +r"\noindent{\footnotesize\color{ontoink} "+interpretation+r"\par}"
        +r"\par\medskip{\footnotesize Source GitHub Actions video artifact "
        +str(artifact)+r"; frame labels reflect playback order, not numerical step.}"
    )
    return raw_latex(text)


subprocess.run([os.sys.executable, str(ROOT / 'report/atlas.py')],check=True)
subprocess.run([os.sys.executable,str(ROOT/'report/research_atlas.py')],check=True)
subprocess.run([os.sys.executable,str(ROOT/'report/phase_art.py')],check=True)
body = [re.sub(r"(?m)^## (.+)$",r"## \1 {.unnumbered}",intro.replace("# What have we gotten ourselves into?","# What have we gotten ourselves into? {.unnumbered}",1))]
essay = (ROOT / "report/artist_statement.md").read_text()
essay = essay.replace("# Recursive creation: human intention, machine intelligence and computational emergence", "# Recursive creation",1)
essay = re.sub(r"(?m)^(#{1,2} .+)$", r"\1 {.unnumbered}", essay)
essay = essay.replace("## The process as medium", raw_latex(r"\begin{center}\includegraphics[width=.96\linewidth,height=.20\textheight,keepaspectratio]{phase_art/8.png}\end{center}")+"## The process as medium",1)
essay = essay.replace("Three distinct processes provide the conceptual structure of the work.", "Three distinct processes provide the conceptual structure of the work."+raw_latex(r"""\begin{center}
\begin{tikzpicture}[every node/.style={font=\sffamily\small,align=left}]
\fill[phaseI!9,rounded corners=4pt] (0,0) rectangle (12.6,5.1);
\node[anchor=north west,text=phaseI,font=\sffamily\bfseries] at (.3,4.9) {03 / Creative inquiry};
\node[anchor=north west] at (.3,4.45) {Questions, interpretation, aesthetic selection};
\fill[phaseIV!13,rounded corners=4pt] (.65,.35) rectangle (11.95,3.65);
\node[anchor=north west,text=phaseIV,font=\sffamily\bfseries] at (.95,3.45) {02 / Model revision};
\node[anchor=north west] at (.95,3.0) {Mechanisms, parameters, instruments};
\fill[phaseIII!18,rounded corners=4pt] (1.3,.7) rectangle (11.3,2.25);
\node[anchor=north west,text=phaseIII,font=\sffamily\bfseries] at (1.6,2.05) {01 / Simulated world};
\node[anchor=north west] at (1.6,1.55) {State updates, feedback, inherited variation};
\end{tikzpicture}
\end{center}"""),1)
essay = essay.replace("The development cycle can be described in six stages.", "The development cycle can be described in six stages."+raw_latex(r"""\begin{center}
\begin{tikzpicture}[x=1cm,y=1cm, every node/.style={font=\sffamily\small}, stage/.style={rounded corners=3pt,draw=ontoblue,fill=ontoblue!6,minimum width=3.7cm,minimum height=1.15cm,align=center}, flow/.style={-{Stealth[length=2.5mm]},thick,draw=ontoblue}]
\node[stage] (a) at (0,0) {\bfseries Intention\\Human inquiry};
\node[stage] (b) at (4.8,0) {\bfseries Synthesis\\AI construction};
\node[stage] (c) at (9.6,0) {\bfseries Execution\\Numerical experiment};
\node[stage] (d) at (9.6,-2) {\bfseries Observation\\Emergent behavior};
\node[stage] (e) at (4.8,-2) {\bfseries Evaluation\\Critical judgment};
\node[stage] (f) at (0,-2) {\bfseries Revision\\New possibilities};
\draw[flow] (a)--(b); \draw[flow] (b)--(c); \draw[flow] (c)--(d);
\draw[flow] (d)--(e); \draw[flow] (e)--(f); \draw[flow] (f)--(a);
\node[font=\sffamily\footnotesize,text=ontoblue] at (4.8,-1) {Evidence informs the next inquiry};
\end{tikzpicture}
\end{center}"""),1)
body.append(essay)
engineering = (ROOT/"report/production.md").read_text()
body.append(re.sub(r"(?m)^(#{1,2} .+)$",r"\1 {.unnumbered}",engineering))
engineering_dir=out/"engineering"
body.append("## Reading the atlas {.unnumbered}\n\nThe early generations explore pattern formation and competing chemical fields. Subsequent phases introduce transport, resources and environmental feedback, followed by four-dimensional observation, inherited variation and structural construction. The experimental plates show selected moments in playback; numerical plots and fixed-coordinate sections provide complementary evidence. Read the chapters as a sequence of evolving questions rather than as steps toward a predetermined endpoint.")
body.append(research_plate("research-genealogy","The genealogy of the investigation","Chronological programme and thematic clusters, not a direct numerical-parentage graph. Amber marks observation-oriented revisions; explicit branch relationships appear on the following plate."))
branch_diagram=ROOT/"docs/figures/research-finale.svg"
if not branch_diagram.is_file():
    raise RuntimeError("Missing late-experiment model ancestry SVG")
subprocess.run(["rsvg-convert","-f","pdf","-o",str(out/"atlas/research-finale.pdf"),str(branch_diagram)],check=True)
body.append(research_plate("research-finale","The late-experiment branch structure","Verified software inheritance branches at G0023: G0024 then G0025 develop construction and maintenance, while G0026 supports G0027 numerical measurement and G0028 intervention. Renderers may reuse artistic techniques without altering a later model's numerical ancestry."))
body.append("**Reading the branches.** G0024 and G0025 explore a line of construction specialization and maintenance. G0026 instead returns to the G0023 factorial baseline to verify numerical observation. Its headless implementation supports G0027's new statistics, G0028's externally imposed disturbance and G0029's optional adaptive curl feedback. A similarity in visual rendering across those branches does not imply that the evolving fields, genetic states, or final conditions were carried forward between generations.")
for n,title,record in records:
    if int(n) in groups:
        phase_end=next((k-1 for k in groups if k>int(n)),len(records))
        phase_index=list(groups).index(int(n))
        roman=("I","II","III","IV","V","VI","VII","VIII","IX")[phase_index]
        subtitles=["Pattern and competition","Motion and dimensionality","Resources and feedback","Sections and persistence","Variation and exchange","Interfaces and connectivity","Construction and selection","Reproducibility and evidence","Intervention and evolving perception"]
        title_style=r"\raggedright\sffamily\bfseries\fontsize{29}{34}\selectfont\hyphenpenalty=10000\exhyphenpenalty=10000 "
        body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{phase"+roman+r"}\pagecolor{phaseblack}\color{white}\thispagestyle{empty}\refstepcounter{part}\addcontentsline{toc}{part}{\thepart\quad "+groups[int(n)]+r"}\PhaseBand{"+roman+"}{"+(n if phase_end==int(n) else n+"--"+f"{phase_end:04d}")+r"}{\sffamily\large "+subtitles[phase_index]+r"\par}\medskip{"+title_style+groups[int(n)]+r"\par}\bigskip{\raggedright\sffamily\large "+phase_text[int(n)]+r"\par}\bigskip\noindent\includegraphics[width=\linewidth]{phase_art/"+str(8 if phase_index==7 else 10 if phase_index==8 else phase_index+1)+r".png}\par\vfill{\color{phaseaccent}\hrule height 2pt}\medskip{\raggedright\sffamily\small "+r"\quad / \quad ".join(key+" "+name for key,name,_ in records[int(n)-1:phase_end])+r"\par}\clearpage\nopagecolor\color{black}"))
    # Print-ready experiment: remove draft history and technical run trails.
    record = prepare(n,record)
    # Mechanism SVGs have a separate PDF rendering. Strip their Markdown
    # image references from the print projection to avoid pdflatex \includesvg.
    record = re.sub(r"(?m)^!\[[^\]\n]*\]\((?:\.\./)?figures/\d{4}\.svg\)[ \t]*$", "", record)
    # Preserve math and code while normalizing plain-text lattice powers.
    tick=chr(96)
    splitter="("+tick*3+r"[\s\S]*?"+tick*3+r"|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|"+tick+r"[^"+tick+r"\n]+"+tick+")"
    segments=re.split(splitter,record)
    for k in range(0,len(segments),2):
        segments[k]=re.sub(r"(?<![\w$])(\d+)\^([234])(?![\w$])",
            lambda m:"$"+m[1]+"^{"+m[2]+"}$",segments[k])
    record="".join(segments)
    atlas=out / "atlas" / f"{n}-atlas.svg"
    if atlas.exists():
        subprocess.run(["rsvg-convert","-f","pdf","-o",str(atlas.with_suffix(".pdf")),str(atlas)],check=True)
        analytical=raw_latex(r"\par\section{Analytical plate}\nopagebreak\begin{center}\includegraphics[width=\linewidth,height=.30\textheight,keepaspectratio]{atlas/"+n+r"-atlas.pdf}\end{center}")
    else:
        analytical=""
    chapter=convert(re.sub(r"^### ","## ",record,flags=re.M))
    result=re.search(r"(?ms)^## (?:Visualization and observed results|Verified outcome|Verified CI outcome|Verified factorial outcome)\n\n?(.*?)(?=^## |\Z)",chapter)
    if result:
        prose=next((line.strip() for line in result[1].splitlines() if line.strip() and not line.startswith(("|","-","$","[","#",chr(96)))),"")
        if prose and len(prose)<650 and not prose.lower().startswith("pending"):
            finding=raw_latex(r"\noindent{\color{phaseaccent}\rule{\linewidth}{1.2pt}}\par{\sffamily\bfseries\small\color{phaseaccent} EXPERIMENTAL OBSERVATION\par}\smallskip")+prose+"\n\n"+raw_latex(r"\noindent{\color{phaseaccent}\rule{\linewidth}{.5pt}}\par")
            # Keep the original observation in its scientific context; avoid duplicating prose.
            pass
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
        body.append(('## Conceptual intervention design (not simulation data)' if n=="0028" else '## Mechanism illustration')+'\n\n'+r'\begin{center}\includegraphics[width=.92\linewidth]{mechanisms/'+n+r'.pdf}\end{center}')
    plot=ROOT / "report" / "plots" / f"{n}.tex"
    if plot.exists():
        body.append("## Quantitative atlas\n\n"+plot.read_text())
    if n=="0012":
        body.append(research_plate("spatial-sections","Observing four spatial dimensions","The periodic fourth coordinate indexes three-dimensional sections. The two observatory views introduced in Generation 0014 are separated by half the domain; they need not depict the same structures."))
    if n=="0021":
        body.append(research_plate("threshold-profile","Threshold-dependent organization","Measured final G0021 profile. The Euler characteristic and coverage describe different properties; neither alone establishes functional compartments."))
    if n=="0024":
        body.append(research_plate("genetic-architecture","Independent inherited traits","Sixteen genotypes per species form a four-dimensional binary mutation graph. Independence here means separate encoded loci, not statistically independent allele frequencies."))
    if (out/f"atlas/{n}-field-evolution.pdf").exists():
        for suffix,heading,caption in [
            ("field-evolution","Numerical development","Native x-y sections at fixed fourth and third coordinates; color scales are fixed over all archived steps for each field."),
            ("field-projections","Projected chemical environment","Mean concentrations over the fourth and third axes. These projections are not individual spatial sections."),
            ("trait-landscape","Spatial distribution of heredity","Local population-weighted allele fractions; cells with negligible total population are undefined."),
            ("structural-volume","Matrix concentration, spatial contrast and occupancy","The native section is selected by maximum occupied count at threshold 0.20, or maximum concentration when global occupancy is zero; z intersects the section maximum. Absolute and mean-relative views share the same coordinates. The histogram covers the entire four-dimensional lattice. The final panel shows occupancy across every fourth-coordinate section, or global threshold sensitivity when no cells exceed 0.20. Relative contrast does not by itself establish functional structure."),
            ("field-metrics","Measured developmental trajectories","Global coverage and allele frequencies independently recomputed from archived numerical states. Connecting lines guide the eye between samples.")]:
            body.append(research_plate(n+"-"+suffix,heading,caption))
    if n in ("0026","0027"):
        body.append(research_plate(n+"-evidence","Measured evidence","Recorded full-resolution numerical diagnostics, seed 42, 4800 steps. These are measurements, not reconstructed spatial fields. Artifact identifiers appear on the plate."))
    if n=="0028":
        body.append(research_plate("0028-full-evidence","Full-resolution matched disturbance","Recorded numerical time series from the verified $24^{4}$, 4,800-step paired experiment, with a single intervention at step 2400 (artifact 14682932255). At the endpoint, the local matrix contrast crosses zero; attenuation of its magnitude is not restoration of the original structural distribution."))
        body.append(research_plate("0028-evidence","Localized disturbance: matched pilot measurements","Recorded numerical time series from the verified $12^{4}$, 240-step paired pilot (artifact 14670709650); the dashed line marks the external event at step 120. Differences are disturbed minus control; this is not full-resolution evidence."))
    if n=="0030":
        plate=out/"atlas/0030-pilot.png"
        if not plate.is_file() or plate.stat().st_size<4096:
            raise RuntimeError("Missing verified G0030 numerical plate")
        body.append(raw_latex(
            r"\clearpage\section{G0030: measured ecological trajectories}"
            r"\begin{center}\includegraphics[width=\linewidth,height=.60\textheight,"
            r"keepaspectratio]{atlas/0030-pilot.png}\end{center}"
            r"\noindent The plotted curves are direct G0030 numerical observations"
            r" for seed 42; the second seed is retained in the numerical JSON."
            r" No simulated arm retained V activity above the endpoint threshold."
            r" Neither coexistence nor succession was demonstrated."
        ))
    if n=="0031":
        plate=out/"atlas/0031-pilot.png"
        if not plate.is_file() or plate.stat().st_size<4096:
            raise RuntimeError("Missing verified G0031 numerical plate")
        body.append(raw_latex(
            r"\clearpage\section{G0031: measured population viability frontier}"
            r"\begin{center}\includegraphics[width=\linewidth,height=.60\textheight,"
            r"keepaspectratio]{atlas/0031-pilot.png}\end{center}"
            r"\noindent The plotted curves are the actual two-seed numeric observations"
            r" from five externally specified V-loss rates at 16\textsuperscript{4} cells."
            r" The historical default is preserved. All measured endpoints"
            r" had zero thresholded co-occupation, and the dominant population"
            r" changed with the multiplier and seed. This is not spatial footage."
        ))
    if n=="0032":
        plate=out/"atlas/0032-pilot.png"
        if not plate.is_file() or plate.stat().st_size<4096:
            raise RuntimeError("Missing verified G0032 numerical niche plate")
        body.append(raw_latex(
            r"\clearpage\section{G0032: measured complementary habitat activity}"
            r"\begin{center}\includegraphics[width=\linewidth,height=.60\textheight,"
            r"keepaspectratio]{atlas/0032-pilot.png}\end{center}"
            r"\noindent The curves are measured 16\textsuperscript{4} time series from two seeds"
            r" and four externally imposed spatial-preference treatments."
            r" Seed 73 retained globally active V and W in separate lattice"
            r" cells, with zero active same-cell co-occupation at step 240."
            r" Seed 42 did not reproduce the outcome. No spatial footage was inferred."
        ))
        native=out/"atlas/0032-spatial.png"
        if not native.is_file() or native.stat().st_size<4096:
            raise RuntimeError("Missing verified G0032 native-4D spatial still")
        body.append(raw_latex(
            r"\clearpage\section{G0032: genuine recorded four-dimensional field}"
            r"\begin{center}\includegraphics[width=\linewidth,height=.66\textheight,"
            r"keepaspectratio]{atlas/0032-spatial.png}\end{center}"
            r"\noindent Authentic float32 four-dimensional concentrations were"
            r" independently recorded for seed 73 over 480 steps with two"
            r" matched treatments. This frame is a fixed omega=8 hyperplane."
            r" Camera rotation is for display only; the experiment is not"
            r" a life simulation with autonomous organisms."
        ))
    body.append(frame_section(n))
body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{ontogreen}"))
body.append((ROOT/"report/final_renders.md").read_text())
for generation,title,note in [
    ("0024","Specialization: visible structure and measured limits",
     "A sampled observatory, not the entire four-dimensional field. G0024 develops inherited construction traits and its final structural coverage depends strongly on the threshold."),
    ("0025","Maintenance: the established volumetric baseline",
     "G0025 uses a genuine 96-cubed volumetric ray sampler for a moving observed section. Light transport is an artistic rendering operation, not an extra simulation process."),
    ("0028","Disturbance: evolving full-domain fields",
     "An artistic view of a 24-to-the-fourth numerical world evolved for 4800 steps. Moving observed-field voxels reveal spatial structures before and after a local disturbance. The film is distinct from the paired experimental comparison, and its camera motion does not add numerical steps."),
]:
    body.append(final_render_plate(generation,title,note))
body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{ontogreen}"))
body.append((ROOT/"report/synthesis.md").read_text().replace("## The original experiment revisited","## The original experiment revisited {.unnumbered}").replace("## What the experiments establish","## What the experiments establish {.unnumbered}").replace("## The limits of observation","## The limits of observation {.unnumbered}").replace("## Continuing the inquiry","## Continuing the inquiry {.unnumbered}"))
body.append(research_plate("comparative-endpoints","Comparative experimental evidence","Upper: descriptive historical endpoints, not a controlled contrast. Lower: four matched-seed G0023 arms; the cost treatment bundles two penalties. All matrix values use threshold 0.20."))
body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{ontoblue}"))
body.append("# Appendix A — Experimental source record {.unnumbered}\n\n"
    "This register preserves source-code, workflow and run references for "
    "every generation without interrupting the experiment chapters. A "
    "successful run verifies its specified execution and assertions; "
    "it does not independently validate artificial life.\n\n"
    "| Generation | Implementation | Workflow | Verified run |\n"
    "|:--|:--|:--|:--|\n"+
    "\n".join(links(n,title,original) for n,title,original in records))
body.append(raw_latex(r"\clearpage"))
body.append("# Appendix B — Computational production record {.unnumbered}\n\n"
    "These engineering measurements describe the experiment's documented "
    "creation and publication processes. They do not measure biological "
    "significance, human labor or the complexity of the mathematical world.")
if (engineering_dir/"summary.md").exists():
    body.append((engineering_dir/"summary.md").read_text().replace(
        "## Recorded engineering metrics",
        "## Recorded engineering metrics {.unnumbered}"))
for filename,heading,caption in [
    ("repository-growth","Repository evolution",
     "Source and workflow growth across the recorded milestone."),
    ("execution-timeline","Computational execution",
     "Concurrent job envelopes, not total labor or billed time."),
    ("artifact-production","Archived artifact and run records",
     "Collected repository metadata; expired artifacts may be absent."),
    ("workflow-topology","Publication dependencies",
     "Grouped completion triggers, excluding manual dispatch and release-data reuse.")
]:
    body.append("## "+heading+" {.unnumbered}\n\n"+
        raw_latex(r"\begin{center}\includegraphics[width=\linewidth,height=.55\textheight,keepaspectratio]{engineering/"+
          filename+r".pdf}\end{center}")+"\n\n"+caption)
body.append("## Edition provenance {.unnumbered}\n\n"
    "Repository source revision: "+revision+". "
    "The numerical interpretations refer to each chapter's described "
    "configuration. Conceptual diagrams, native-field measurements and "
    "cinematic frames are different kinds of representation.")
author = (ROOT/"docs/AUTHOR.md").read_text().split("\n",1)[1].strip()
author = "\n".join(line for line in author.splitlines()
                   if not line.startswith("[←")).strip()
body.append(raw_latex(r"\clearpage\colorlet{phaseaccent}{ontogreen}")+"# About the artist {.unnumbered}"+raw_latex(r"\noindent\includegraphics[width=\linewidth,height=.22\textheight,keepaspectratio]{phase_art/9.png}\par\medskip{\sffamily\bfseries\LARGE\color{ontoink} Scott Muller\par}{\sffamily\small\color{ontoblue} Matsch Systems / Systems engineering / Computational art\par}\medskip{\color{ontogreen}\hrule}\medskip")+author)
(out/"report.md").write_text("\n\n".join(body))
subprocess.run(["pandoc",str(out/"report.md"),"--standalone","--toc","--toc-depth=1","--number-sections","--top-level-division=chapter","--metadata","documentclass=report","--metadata","title=Ontogenesis: Computational Excess","--metadata","subtitle=An illustrated field journal of evolving simulations and overworked CI","--metadata","author=Scott Muller — Ontogenesis Project","--variable","geometry:margin=25mm","--variable","fontsize=11pt","--include-in-header=report/preamble.tex","-o",str(out/"ontogenesis.tex")],check=True)
tex=out/"ontogenesis.tex"
subprocess.run([os.sys.executable,str(ROOT/"report/cover_art.py")],check=True)
raw=tex.read_text()
custom=r"""\begin{titlepage}
\thispagestyle{empty}
\begin{tikzpicture}[remember picture,overlay]
\node[inner sep=0pt] at (current page.center) {\includegraphics[width=\paperwidth,height=\paperheight]{cover.png}};
\node[anchor=north west,text=white,font=\sffamily\small] at ([xshift=25mm,yshift=-24mm]current page.north west) {COMPUTATIONAL FIELD JOURNAL};
\node[anchor=north west,text=white,font=\sffamily\bfseries\fontsize{39}{44}\selectfont] at ([xshift=23mm,yshift=-40mm]current page.north west) {ONTOGENESIS};
\node[anchor=north west,text=white,font=\sffamily\Large] at ([xshift=25mm,yshift=-60mm]current page.north west) {An experiment in computational excess};
\node[anchor=south west,text=white,font=\sffamily\large] at ([xshift=25mm,yshift=30mm]current page.south west) {Scott Muller};
\node[anchor=south west,text=white,font=\sffamily\small] at ([xshift=25mm,yshift=23mm]current page.south west) {An illustrated computational field journal};
\node[anchor=south west,text=white,font=\sffamily\small] at ([xshift=25mm,yshift=16mm]current page.south west) {scott@21h.io};
\end{tikzpicture}\null
\end{titlepage}"""
preamble,marker,document=raw.partition(r"\begin{document}")
assert marker
document,count=re.subn(r"(?m)^[ \t]*\\maketitle[ \t]*$",lambda _:custom,document,count=1)
assert count==1
tex.write_text(preamble+marker+document)
subprocess.run(["latexmk","-pdf","-interaction=nonstopmode","-halt-on-error","ontogenesis.tex"],cwd=out,check=True)
