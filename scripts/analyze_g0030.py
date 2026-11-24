"""Posthoc G0030 measured population activity, without a numerical rerun.

Determines when thresholded activity is last recorded, within the archived
observation cadence. This does not establish biological extinction, mutualism,
ecological succession or a causal effect from the external supply reversal.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ARMS=("neither","w_to_v_only","v_to_w_only","both")
METRICS=("v_active","w_active","coexistence","v_mean","w_mean",
         "energy_mean","matrix_mean","matrix_coverage",
         "metabolite_v_mean","metabolite_w_mean","metabolite_overlap",
         "genotype_entropy_bits")

def validate(source):
    if source.get("generation")!="0030":
        raise ValueError("Input is not a G0030 measurement archive")
    steps=source.get("steps")
    event=source.get("season_switch")
    if not isinstance(steps,int) or steps<=0:
        raise ValueError("Missing positive integration duration")
    if not isinstance(event,int) or not 0<event<steps:
        raise ValueError("Invalid common event step")
    times=source.get("times")
    if (not isinstance(times,list) or len(times)<3 or
        not all(isinstance(t,int) for t in times) or
        times[0]!=0 or times[-1]!=steps or times!=sorted(set(times)) or
        event not in times or not any(t>event for t in times)):
        raise ValueError("Invalid observation timeline or event")
    seeds=source.get("seeds")
    if not isinstance(seeds,list) or not seeds or len(seeds)!=len(set(seeds)):
        raise ValueError("Missing independent seeds")
    for seed in seeds:
        cohort=source.get("observations",{}).get(str(seed),{})
        if set(cohort)!=set(ARMS):
            raise ValueError(f"Unmatched factorial arms for seed {seed}")
        for arm,rows in cohort.items():
            if [r.get("step") for r in rows]!=times:
                raise ValueError(f"Unmatched observation times for seed {seed}, {arm}")
            for row in rows:
                for name in METRICS:
                    value=row.get(name)
                    if not isinstance(value,(float,int)) or not math.isfinite(value):
                        raise ValueError(f"Invalid {name} for seed {seed}, {arm}")
                for name in ("v_active","w_active","coexistence","matrix_coverage"):
                    if not -1e-9<=row[name]<=1+1e-9:
                        raise ValueError(f"Coverage outside zero-one range: {name}")

def time_average(rows,field):
    """Trapezoidal time average across saved samples only."""
    if len(rows)<2 or rows[-1]["step"]<=rows[0]["step"]:
        raise ValueError("Need multiple ordered observations")
    area=sum((b["step"]-a["step"])*(a[field]+b[field])/2
             for a,b in zip(rows,rows[1:]))
    return area/(rows[-1]["step"]-rows[0]["step"])

def loss_window(rows,key):
    """Observed suffix of zero coverage; no claim about times between samples."""
    active=[i for i,row in enumerate(rows) if row[key]>0]
    if not active:
        return {"ever_above_threshold":False,"last_active_sample":None,
                "first_persistently_inactive_sample":rows[0]["step"]}
    idx=active[-1]
    return {"ever_above_threshold":True,
            "last_active_sample":rows[idx]["step"],
            "first_persistently_inactive_sample":(
                rows[idx+1]["step"] if idx+1<len(rows) else None)}

def analyze(source):
    validate(source)
    switch=source["season_switch"]
    result={
        "generation":"0030",
        "analysis_edition":"measured-trajectory-qualification-v1",
        "numerical_source_sha":source.get("source_sha"),
        "source_job":"https://github.com/interrupt21h/ontogenesis/actions/runs/45266523722",
        "n":source["n"],"steps":source["steps"],"season_switch":switch,
        "seeds":source["seeds"],"arms":list(ARMS),"analysis":{},
        "interpretation_limits":[
            "Observed activity loss is bounded by sample cadence, not a known exact extinction instant.",
            "Zero thresholded coverage does not imply numerical concentration is everywhere zero.",
            "All arms share a forced supply reversal; a no-reversal environmental control is absent.",
            "Two seeds and endpoint contrasts do not prove stable succession or mutualism.",
            "Time-integrated metrics are trapezoidal interpolation for descriptive analysis only.",
        ],
    }
    all_v_zero=True
    all_co_zero=True
    for seed in source["seeds"]:
        key=str(seed)
        control=source["observations"][key]["neither"][-1]
        arms={}
        for arm in ARMS:
            rows=source["observations"][key][arm]
            at_switch=next(row for row in rows if row["step"]==switch)
            final=rows[-1]
            arms[arm]={
                "v_coverage":loss_window(rows,"v_active"),
                "w_coverage":loss_window(rows,"w_active"),
                "at_event":{name:at_switch[name] for name in
                            ("v_active","w_active","coexistence","energy_mean")},
                "endpoint":{name:final[name] for name in METRICS},
                "w_endpoint_delta_vs_neither_percentage_points":100*(
                    final["w_active"]-control["w_active"]),
                "time_integrated_mean":{name:time_average(rows,name) for name in
                                         ("v_active","w_active","coexistence",
                                          "matrix_coverage","genotype_entropy_bits")},
                "max_observed_v_active":max(row["v_active"] for row in rows),
                "max_observed_w_active":max(row["w_active"] for row in rows),
            }
            all_v_zero &= final["v_active"]==0
            all_co_zero &= final["coexistence"]==0
        result["analysis"][key]=arms
    result["all_endpoints_v_inactive_by_threshold"]=all_v_zero
    result["all_endpoints_cooccupancy_inactive_by_threshold"]=all_co_zero
    return result

def markdown(result):
    lines=[
        "# G0030 — Where did active coexistence go?",
        "",
        "*Retrospective measurement of an existing simulation archive, not new dynamics.*",
        "",
        f"**Source:** {result['n']}⁴ periodic cells, {result['steps']} updates, "
        f"shared spatial supply inversion at step {result['season_switch']}, "
        f"seeds {', '.join(map(str,result['seeds']))}.",
        "",
        "| Seed | Cross-feeding | Last V-active sample | First later persistently inactive sample | V at environmental change | Final W activity | W delta vs neither | Mean co-occupancy over time |",
        "|:--|:--|--:|--:|--:|--:|--:|--:|",
    ]
    for seed in result["seeds"]:
        for arm,item in result["analysis"][str(seed)].items():
            loss=item["v_coverage"]
            pretty=lambda x:"not observed" if x is None else str(x)
            lines.append(
                f"| {seed} | {arm.replace('_',' ')} | "
                f"{pretty(loss['last_active_sample'])} | "
                f"{pretty(loss['first_persistently_inactive_sample'])} | "
                f"{100*item['at_event']['v_active']:.3f}% | "
                f"{100*item['endpoint']['w_active']:.3f}% | "
                f"{item['w_endpoint_delta_vs_neither_percentage_points']:+.3f} pp | "
                f"{100*item['time_integrated_mean']['coexistence']:.4f}% |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Each time is an **observed numerical sample**. The first later persistently "
        "inactive sample is the first zero in the observed zero suffix, not the "
        "moment of biological death. Activity may be unobserved between samples.",
        "",
        ("Every arm had zero active V coverage and active co-occupancy at its endpoint. "
         if result["all_endpoints_v_inactive_by_threshold"] and
         result["all_endpoints_cooccupancy_inactive_by_threshold"] else
         "Some arms retained endpoint V activity or co-occupancy. ")+
        "Cross-feeding changed some W endpoint fractions, but this is not evidence "
        "of sustained reciprocal coexistence.",
        "",
        "## Limitations",
        "",
    ])
    lines.extend("- "+x for x in result["interpretation_limits"])
    lines.extend([
        "",
        "[Original G0030 numerical pilot and provenance]"
        "(https://github.com/interrupt21h/ontogenesis/actions/runs/45266523722)",
        "",
    ])
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--json",type=Path,required=True)
    p.add_argument("--markdown",type=Path,required=True)
    args=p.parse_args()
    src=json.loads(args.input.read_text())
    result=analyze(src)
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.markdown.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    args.markdown.write_text(markdown(result))
    print(markdown(result))

if __name__=="__main__":
    main()
