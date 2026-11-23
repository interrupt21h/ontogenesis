"""Fail fast on unresolved draft fragments in the print-edition projection."""
import re
from pathlib import Path
from editorial import prepare,links

root=Path(__file__).resolve().parents[1]
text=(root/"docs/HISTORY.md").read_text()
records=re.findall(
    r"^## Generation (\d{4}) — (.+?)\n(.*?)(?=^## Generation |^## Research priorities|\Z)",
    text,re.M|re.S)
assert [int(n) for n,_,_ in records]==list(range(1,30)), "29 records required"
for n,title,original in records:
    finished=prepare(n,original)
    assert len(finished)>150,(n,"empty print narrative")
    assert "<!-- AUTO-CI" not in finished,(n,"CI log leaked")
    assert "Experiment sources:" not in finished,(n,"unformatted tag trail")
    assert "Status:" not in finished,(n,"unformatted status")
    assert re.search(r"^Parent:",finished,re.M) is None,(n,"unformatted lineage")
    assert "Workflow ·" not in finished,(n,"inline workflow trail")
    row=links(n,title,original)
    assert row.startswith("| [G"+n+"]"),(n,"bad provenance row")
for n,title,original in records[-3:]:
    clean=prepare(n,original)
    for bad in ("verification update","preview run","rerender","now retains",
                "we updated","I changed","was fixed"):
        assert bad not in clean.lower(),(n,bad)
print("PASS: 29 experimental narratives, metadata panels, appendix provenance")
