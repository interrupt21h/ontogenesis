"""Print-edition view of the canonical experimental archive.

The detailed HISTORY stays intact; this projects its verified science
without inline workflow chatter, retrospective draft updates or CI logs.
"""
from __future__ import annotations
import re

BASE="https://github.com/interrupt21h/ontogenesis"
AUTO=re.compile(r"(?s)<!-- AUTO-CI-BEGIN -->.*?<!-- AUTO-CI-END -->")
REPRO=re.compile(r"(?ms)^### Reproduction(?: and provenance)?\n.*?(?=^### |\Z)")
LINK=re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def tex(s):
    esc={"\\":r"\textbackslash{}","%":r"\%","&":r"\&",
         "#":r"\#","_":r"\_","$":r"\$","{":r"\{","}":r"\}"}
    return "".join(esc.get(ch,ch) for ch in s)

def meta(title,value):
    return "\n\n"+("`"*3)+"{=latex}\n"+r"\AtlasMetadata{"+tex(title)+"}{"+tex(value)+"}\n"+("`"*3)+"\n\n"

def links(number,title,original):
    pairs=LINK.findall(original)
    def choose(keys):
        return next((u for k,u in pairs if k.lower() in keys),"")
    def absolute(p):
        return p if p.startswith("http") else BASE+"/blob/main/"+p.removeprefix("../")
    source=choose({"source"})
    workflow=choose({"workflow","ci"})
    runs=re.findall(r"https://github\.com/interrupt21h/ontogenesis/actions/runs/(\d+)",original)
    selected={"0026":"44751157353","0027":"44814192851","0028":"44840239338"}
    run=selected.get(number,runs[-1] if runs else "")
    docs=f"[G{number}]({BASE}/blob/main/docs/generations/{number}.md)"
    src=f"[Source]({absolute(source)})" if source else "—"
    wf=f"[Workflow]({absolute(workflow)})" if workflow else "—"
    ci=f"[Run {run}]({BASE}/actions/runs/{run})" if run else "—"
    return f"| {docs} | {src} | {wf} | {ci} |"

def compact_metrics(source,number):
    if number in ("0023","0024"):return ""
    m=AUTO.search(source)
    if not m:return ""
    pairs=dict((k.strip().lower(),v.strip()) for k,v in
               re.findall(r"(?m)^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|$",m.group()))
    labels={"v active":"V active (%)","w active":"W active (%)",
            "energy mean":"Mean energy","structure mean":"Mean matrix",
            "structure active":"Matrix coverage above 0.20 (%)",
            "genotype entropy":"Genotype entropy (bits)"}
    lines=[]
    for key,label in labels.items():
        if key not in pairs:continue
        try:v=float(pairs[key])
        except ValueError:continue
        if key in ("v active","w active","structure active"):v*=100
        lines.append(f"| {label} | {v:.6g} |")
    if len(lines)<3:return ""
    return ("\n\n### Recorded endpoint\n\nSelected numerical observables. "
            "Thresholded coverage is not a measure of functional life.\n\n"
            "| Measure | Value |\n|:--|--:|\n"+"\n".join(lines)+"\n")

EDITORIAL={
"0026":r"""
## Question and numerical ancestry

Does observation alter the result of a numerical simulation? G0026
returns to the G0023 factorial baseline, changing instrumentation but
adding no physical interaction. The headless and observed configurations
are advanced from matched initial states.

## Method and measurements

The full experiment integrates a periodic 24⁴ lattice for 4,800 steps.
At 41 checkpoints, SHA-256 hashes of thirteen dynamic fields agree
between the headless and tested read-only observer configurations.
Final mean matrix concentration is 0.147089481, standard deviation
0.0409239273, and coverage above threshold 0.20 is 10.5041%.
The strongest nonzero Fourier mode has a 24-cell wavelength,
the entire periodic domain width.

## Interpretation

The tested observer does not change the numerical state at those
checkpoints. This does not establish bitwise reproducibility between
different machines, nor does the domain-scale spectral mode establish
an intrinsic biological structural length.
""",
"0027":r"""
## Question and numerical ancestry

Can structural variation be measured without selecting an arbitrary
binary segmentation threshold? G0027 retains G0026's physical update
equations and adds radial Fourier-spectrum summaries and Otsu
histogram segmentation.

## Measurements

At step 4,800, mean matrix concentration is 0.1470894561 and
standard deviation 0.0409239276. The adaptive threshold is 0.14,
with 58.21096% coverage and binned separability 0.7152774.
The lowest measured nonzero radial shell, 0.03125–0.0625 cycles
per cell, contains 77.50962% of nonzero spectral energy.
These are descriptors of broad structural variation, not
proof of discrete functional phases.

## Observer verification and limits

Separate-run G0026 and G0027 hashes differ after initialization
despite closely agreeing endpoints. Such a comparison does not
establish bitwise reproducibility between runners. The controlled
*same-process* test matched all **41 of 41** observation checkpoints
against the headless calculation, supporting observer noninterference
under those tested conditions. Spectral and adaptive-segmentation
metrics do not by themselves identify organisms or compartments.
""",
"0028":r"""
## Controlled intervention

G0028 examines the response of a four-dimensional chemical system to a
single, externally imposed spatial disturbance. Its numerical dynamics
descend from G0026. The same seed, initial condition and integration
schedule are used in two arms: one untreated control and one
trajectory receiving a localized periodic Gaussian reduction of energy
and structural matrix.

## Pilot and full-domain comparisons

The exploratory paired pilot uses a 12⁴ lattice, 240 steps and an
intervention at step 120. It records the local disturbed-minus-control
energy difference moving from -0.52454344 to -0.00439679, and the matrix
difference from -0.00332975 to -0.00036322.

The independently executed **24⁴ paired experiment** extends to
4,800 integration steps, with the intervention at step 2400. It uses
seed 42 and records 123 observed times per arm. The affected Gaussian
core contains 1,897 of the 331,776 cells. At the event, the local
energy difference is -0.44120503; by step 4800 it is -0.02491707,
a **94.35%** reduction in the magnitude of the deficit. The matrix
difference changes from -0.08870594 to **+0.01060031**. Its
absolute magnitude attenuates by **88.05%**, but the sign crosses
zero: the disturbed arm ends with a higher local mean than control.

At the full-domain endpoint, global mean matrix concentration is
0.148343 in the disturbed arm and 0.147089 in control. Yet only
**5.00%** of disturbed cells exceed matrix threshold 0.20, versus
**10.50%** in control. Mean concentration and high-threshold coverage
therefore describe different aspects of the outcome. Active V
fractions are 2.05% and 3.61%, respectively, while active W
fractions are 85.35% and 68.28%.

## Interpretation and artistic observation

The paired experiment supports a measured, seed-specific response to
the localized intervention. Recovery of the *difference from control*
does not mean restoration of the initial matrix field, its connectivity
or any biological function. The altered global coverage and
population balance caution against equating a small endpoint local
difference with return to an unchanged ecological state.

G0028 also has separately archived cinematic observations of single
disturbed universes. The selected 12⁴ preview and the 24⁴ artistic
editions use camera motion, spatial sectioning, exposure and ray
integration. These are field-derived visualizations, not a two-arm
causal measurement. Neither the film nor the single-seed experiment
establishes generalized ecological resilience.

"""
}

def prepare(number,record):
    if number in EDITORIAL:
        stat={"0026":"41 tested observer checkpoints matched",
              "0027":"41/41 same-process observation checkpoints matched",
              "0028":"Full 24⁴ paired experiment and reduced-domain pilot verified"}
        parent={"0026":"G0023 factorial baseline","0027":"G0026 numerical baseline",
                "0028":"G0026 numerical driver"}
        return meta("EVIDENCE",stat[number])+meta("MODEL ANCESTRY",parent[number])+EDITORIAL[number]

    original=record
    status=re.search(r"(?m)^Status:\s*(.+)$",record)
    prefix=""
    if status:
        value=status.group(1)
        if value.lower().startswith("ci verified"):
            value="Verified at the recorded seed and lattice configuration"
        prefix+=meta("EVIDENCE",value[:130])
        record=record[:status.start()]+record[status.end():]
    parent=re.search(r"(?m)^Parent:\s*(G\d{4})[^.;\n]*(?:[.;]\s*)?",record)
    if parent:
        prefix+=meta("MODEL ANCESTRY",parent.group(1))
        record=record[:parent.start()]+record[parent.end():]
    # Recast instructions from the engineering notes as documentary prose.
    if number=="0019":
        record=record.replace(
            "Replace lower identity timeline panel with three fixed-scale time-series panels:",
            "The observatory presents three fixed-scale time-series panels:")
        record=record.replace(
            "Retain live entity list, recent events and two rotating sections.",
            "The display includes an entity list, recent events and two rotating sections.")
        record=record.replace("expected duration", "recorded duration")
        record=record.replace("Increased rendering cadence may increase runtime; 90-minute timeout retained.","")
    elif number=="0020":
        record=record.replace(
            "Replace cut-dependent complement segmentation with periodic face-connected labels.",
            "Periodic face-connected labels supersede cut-dependent complement segmentation.")
    brief=compact_metrics(record,number)
    record=AUTO.sub("",record)
    record=REPRO.sub("",record)
    # Remove stand-alone repository link trails; full links go in Appendix A.
    record=re.sub(r"(?m)^\s*(?:\[(?:Source|Workflow|CI|Successful run|Standalone MP4|Diagnostics)\]\([^\n]+\).*)$","",record)
    record=re.sub(r"(?m)^<!--.*?-->\s*$","",record)
    record=re.sub(r"(?m)^[-*] Run from repository root:.*$","",record)
    if brief and not ("### Verified outcome" in record or
                      "### Verified factorial outcome" in record):
        record+=brief
    return prefix+re.sub(r"\n{4,}","\n\n\n",record).strip()+"\n"
