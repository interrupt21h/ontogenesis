"""Print-edition view of the canonical experimental archive.

The detailed HISTORY stays intact; this projects its verified science
without inline workflow chatter, retrospective draft updates or CI logs.
"""
from __future__ import annotations
import re

BASE="https://github.com/interrupt21h/ontogenesis"
AUTO=re.compile(r"(?s)<!-- AUTO-CI-BEGIN -->.*?<!-- AUTO-CI-END -->")
REPRO=re.compile(r"(?ms)^### Reproduction and provenance\n.*?(?=^### |\Z)")
LINK=re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

def tex(s):
    esc={"\\":r"\textbackslash{}","%":r"\%","&":r"\&",
         "#":r"\#","_":r"\_","$":r"\$","{":r"\{","}":r"\}"}
    return "".join(esc.get(ch,ch) for ch in s)

def meta(title,value):
    return "\n\n"+("`"*3)+"{=latex}\n"+r"\AtlasMetadata{"+tex(title)+"}{"+tex(value)+"}\n"+("`"*3)+"\n\n"

def links(number,original):
    pairs=LINK.findall(original)
    def choose(keys):
        return next((u for k,u in pairs if k.lower() in keys),"")
    def absolute(p):
        return p if p.startswith("http") else BASE+"/blob/main/"+p.removeprefix("../")
    source=choose({"source"})
    workflow=choose({"workflow","ci"})
    runs=re.findall(r"https://github\.com/interrupt21h/ontogenesis/actions/runs/(\d+)",original)
    selected={"0026":"44751157353","0027":"44814192851","0028":"44823647222"}
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

G0028 examines how a localized disturbance changes a developing
four-dimensional chemical system. The numerical dynamics descend
from G0026. A deterministic periodic Gaussian shock reduces local
energy and matrix concentration in one seeded trajectory; a second
trajectory with matching initial conditions remains untreated.

## Pilot measurements

The verified paired pilot uses a 12⁴ lattice, 240 integration steps,
and an event at step 120. Immediately after the intervention, the
local disturbed-minus-control energy difference is -0.52454344;
at step 240 it is -0.00439679. The corresponding matrix differences
are -0.00332975 and -0.00036322. The magnitudes of these differences
decline by 99.16% and 89.09%, respectively.

These are **deviations from the untreated control**, not evidence
that the damaged matrix returned to its initial concentration.
The matrix was already small and declining. A more extensive
24⁴ paired study was launched separately, but this edition's
numerical comparison is the verified small-domain pilot.

## Cinematic observation

A different, single-universe archive supplies the moving artwork.
The selected preview records a three-dimensional section from a
12⁴ numerical domain. Separate full-domain cinematic editions
observe additional fields and use either stylized voxel projections
or volumetric ray integration. Camera paths, color exposure and
display interpolation are visualization operations, not further
numerical state updates.

## Interpretation

The pilot quantifies a short, single-seed response to an imposed
disturbance. Neither the attenuation of the paired difference
nor the visual representation demonstrates mature ecological
recovery or functioning biological life.
"""
}

def prepare(number,record):
    if number in EDITORIAL:
        stat={"0026":"41 tested observer checkpoints matched",
              "0027":"41/41 same-process observation checkpoints matched",
              "0028":"Paired 12⁴ pilot verified; full-domain comparison not in this edition"}
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
