"""Collect auditable CI metadata and render the engineering atlas."""
import datetime as dt
import json, os, subprocess, re
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as md
from collections import Counter
import yaml

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"report/build/engineering"
OUT.mkdir(parents=True,exist_ok=True)
REPO=os.environ.get("GITHUB_REPOSITORY","interrupt21h/ontogenesis")
START="2026-11-19T04:06:58Z"
END="2026-11-20T16:09:07Z"
def git(*args):
    return subprocess.check_output(["git","-C",str(ROOT),*args],text=True)
def api(endpoint,key=None):
    raw=subprocess.check_output(["gh","api","--paginate","--slurp",f"repos/{REPO}/{endpoint}"],text=True)
    pages=json.loads(raw)
    return [v for p in pages for v in (p[key] if key else p)]
def date(s): return dt.datetime.fromisoformat(s.replace("Z","+00:00"))
def window(s): return START<=s<=END
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2))
def chart(name,fig):
    fig.savefig(OUT/(name+".pdf"),bbox_inches="tight");plt.close(fig)
def main():
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"bold"})
    commits=[]
    for line in git("log","--reverse","--format=%H%x09%cI%x09%s","HEAD").splitlines():
        sha,t,subject=line.split("\t",2)
        commits.append(dict(sha=sha,time=date(t).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),subject=subject))
    # Count tracked files and their blob sizes at each historical revision.
    for c in commits:
        tree=git("ls-tree","-r","-l",c["sha"]).splitlines()
        paths=[line.split("\t",1) for line in tree]
        c["workflows"]=sum(p.startswith(".github/workflows/") and p.endswith((".yml",".yaml")) for _,p in paths)
        c["generations"]=sum(bool(re.fullmatch(r"docs/generations/\d{4}\.md",p)) for _,p in paths)
        c["source_bytes"]=sum(int(m.split()[-1]) for m,p in paths if p.endswith(".py") and m.split()[-1].isdigit())
    graph=[]
    for p in sorted((ROOT/".github/workflows").glob("*.y*ml")):
        d=yaml.load(p.read_text(),Loader=yaml.BaseLoader)
        triggers=d.get("on") or {}
        if isinstance(triggers,str): triggers={triggers:{}}
        if isinstance(triggers,list): triggers=dict.fromkeys(triggers,{})
        graph.append(dict(file=p.name,name=d.get("name",p.stem),triggers=list(triggers),upstream=(triggers.get("workflow_run") or {}).get("workflows",[]),jobs=list(d.get("jobs",{}))))
    runs=[]; jobs=[]; artifacts=[]; errors=[]
    try:
        raw=api("actions/runs?branch=main&per_page=100","workflow_runs")
        for x in raw:
            runs.append({k:x.get(k) for k in ("id","name","created_at","run_started_at","updated_at","status","conclusion","run_attempt","head_sha","html_url")})
        # Latest attempt only: older attempts are not counted as zero or silently imputed.
        for x in runs:
            if not window(x["created_at"]): continue
            try:
                for j in api(f"actions/runs/{x['id']}/jobs?filter=latest&per_page=100","jobs"):
                    jobs.append(dict(run_id=x["id"],workflow=x["name"],**{k:j.get(k) for k in ("id","name","started_at","completed_at","conclusion","status")}))
                for a in api(f"actions/runs/{x['id']}/artifacts?per_page=100","artifacts"):
                    artifacts.append(dict(run_id=x["id"],workflow=x["name"],**{k:a.get(k) for k in ("id","name","size_in_bytes","expired","created_at")}))
            except subprocess.CalledProcessError as e: errors.append(f"Run {x['id']}: metadata retrieval failed")
    except (subprocess.CalledProcessError,FileNotFoundError) as e: errors.append("GitHub API unavailable; CI data absent")
    snapshot=dict(source_revision=git("rev-parse","HEAD").strip(),collected=dt.datetime.now(dt.timezone.utc).isoformat(),window=[START,END],runs=runs,jobs=jobs,artifacts=artifacts,errors=errors,shallow=git("rev-parse","--is-shallow-repository").strip()=="true")
    save("ci-history.json",snapshot);save("development-chronology.json",commits);save("workflow-topology.json",graph)
    cc=[c for c in commits if c["time"]<=END]
    fig,ax=plt.subplots(2,1,figsize=(9,5),layout="constrained",sharex=True)
    if cc:
        t=[date(c["time"]) for c in cc]
        for key,label in [("workflows","Workflow definitions"),("generations","Generation records")]: ax[0].step(t,[c[key] for c in cc],where="post",label=label)
        ax[0].legend();ax[1].step(t,[c["source_bytes"]/1024 for c in cc],where="post",label="Python source KiB");ax[1].legend()
        ax[1].xaxis.set_major_formatter(md.DateFormatter("%d %H:%M",tz=dt.timezone.utc))
    ax[0].set_title("Repository growth through the documented milestone");ax[1].set_xlabel("UTC")
    chart("repository-growth",fig)
    rr=[x for x in runs if window(x["created_at"])]
    fig,ax=plt.subplots(figsize=(10, max(4,len(set(x["name"] for x in rr))*.27)),layout="constrained")
    names=sorted(set(x["name"] for x in rr))
    colors={"success":"#398873","failure":"#b65349","cancelled":"#a79065","skipped":"#999999"}
    for x in rr:
        a=date(x["created_at"]);b=min(date(x["updated_at"]),date(END))
        if b>a: ax.barh(names.index(x["name"]),md.date2num(b)-md.date2num(a),left=md.date2num(a),height=.6,alpha=.55,color=colors.get(x["conclusion"],"#5686aa"))
    ax.set_yticks(range(len(names)),names,fontsize=11);ax.xaxis.set_major_formatter(md.DateFormatter("%d %H:%M",tz=dt.timezone.utc));ax.set_title("CI run envelopes (overlap permitted; not billed time)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c,label=k) for k,c in colors.items()]+[Patch(color="#5686aa",label="other")],loc="upper center",bbox_to_anchor=(.5,-.08),ncol=5,fontsize=9,frameon=False)
    if not rr: ax.text(.5,.5,"CI metadata unavailable",transform=ax.transAxes,ha="center")
    chart("execution-timeline",fig)
    fig,ax=plt.subplots(1,2,figsize=(9,4),layout="constrained")
    counts=Counter(x["conclusion"] or x["status"] for x in rr)
    ax[0].bar(list(counts),list(counts.values()),color="#5686aa");ax[0].tick_params(axis="x",rotation=35);ax[0].set_title("Run states at collection")
    sizes=Counter()
    for a in artifacts:
        if a.get("created_at") and a["created_at"]<=END: sizes[a["workflow"]]+=a["size_in_bytes"] or 0
    top=sizes.most_common(12);ax[1].barh([x[0] for x in top],[x[1]/1048576 for x in top],color="#398873");ax[1].tick_params(axis="y",labelsize=7);ax[1].set_xlabel("MiB");ax[1].set_title("Retained artifact metadata (top 12)")
    chart("artifact-production",fig)
    fig,ax=plt.subplots(figsize=(10,9),layout="constrained");ax.axis("off")
    upstream=[g for g in graph if g["upstream"]]
    ax.text(.03,.96,"Experiment completion sources",weight="bold",transform=ax.transAxes)
    ax.text(.68,.96,"Publication workflows",weight="bold",transform=ax.transAxes)
    allsrc=sorted(set(n for g in upstream for n in g["upstream"]))
    for i,n in enumerate(allsrc):
        y=.9-i*.8/max(1,len(allsrc)-1)
        ax.text(.03,y,n,fontsize=11,transform=ax.transAxes,va="center")
        for j,g in enumerate(upstream):
            if n in g["upstream"]: ax.plot([.35,.66],[y,.75-j*.35],color="#5686aa",alpha=.55,linewidth=.8,transform=ax.transAxes)
    for j,g in enumerate(upstream): ax.text(.68,.75-j*.35,g["name"],fontsize=11,weight="bold",transform=ax.transAxes)
    ax.text(.03,.025,"Declarative workflow_run edges only; CLI dispatch and push paths are discussed separately.",fontsize=8,transform=ax.transAxes)
    chart("workflow-topology",fig)
    seconds=sum(max(0,(min(date(j["completed_at"]),date(END))-max(date(j["started_at"]),date(START))).total_seconds()) for j in jobs if j["started_at"] and j["completed_at"])
    lines=["## Recorded engineering metrics","",f"Collected at {snapshot['collected']}; source revision is recorded in the accompanying JSON. The milestone window is {START} to {END}.","", "| Metric | Value |","|---|---:|",f"| Commits in milestone window | {sum(window(c['time']) for c in commits)} |",f"| Workflow definitions at report revision | {len(graph)} |",f"| Observable run records initiated in window | {len(rr)} |",f"| Latest-attempt job records retrieved | {len(jobs)} |",f"| Completed-job overlap with window (hours) | {seconds/3600:.2f} |",f"| Observable artifact volume created by milestone (MiB) | {sum(sizes.values())/1048576:.2f} |","", "Job hours are a partial aggregate, not billing or human effort. Run states are observed at collection, not reconstructed as of the milestone. Deleted or expired metadata and prior attempts may be missing. No human time was measured."]
    if errors or snapshot["shallow"]: lines+=["","**Coverage limitation:** "+("; ".join(errors[:10]) or "Shallow Git history.")+" Counts are incomplete."]
    (OUT/"summary.md").write_text("\n".join(lines))
if __name__=="__main__":main()
