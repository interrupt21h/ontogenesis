"""Validate Ontogenesis's complete 32-generation visual atlas and real release assets.

The check distinguishes archived films, diagnostic numerical animations and
native 4D-derived spatial imagery. Broken video/poster links and missing
source archive dependencies are CI failures rather than silent UI omissions.
"""
from __future__ import annotations
import argparse,json,re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlparse

BASE="https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/"
FILMS={
    "0028":("ontogenesis-0028-cinematic.mp4","spatial-film"),
    "0029":("ontogenesis-0029-voxel-cinematic.mp4","spatial-film"),
    "0030":("ontogenesis-0030-diagnostic.mp4","measured-animation"),
    "0031":("ontogenesis-0031-evidence.mp4","measured-animation"),
    "0032":("ontogenesis-0032-evidence.mp4","measured-animation"),
}

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards=[]
        self.current=None
        self.assets=set()
    def handle_starttag(self,tag,attrs):
        attributes=dict(attrs)
        if tag=="article" and "tile" in attributes.get("class","").split():
            if self.current is not None:raise ValueError("Nested generation cards")
            self.current={"title":attributes.get("data-title",""),
                          "kinds":attributes.get("data-kind","").split(),
                          "assets":set(),"links":set()}
            self.cards.append(self.current)
        for key in ("src","href","poster"):
            url=attributes.get(key)
            if not url:continue
            if url.startswith(BASE):
                name=unquote(url[len(BASE):].split("?")[0])
                if not name or "/" in name:raise ValueError("Unrecognized archive asset URL")
                self.assets.add(name)
                if self.current is not None:self.current["assets"].add(name)
            if key=="href" and self.current is not None:
                self.current["links"].add(url)
    def handle_endtag(self,tag):
        if tag=="article":self.current=None

def verify(html,video_manifest,available):
    parser=Parser()
    parser.feed(html)
    if len(parser.cards)!=32:
        raise ValueError(f"Expected exactly 32 generation visual cards, got {len(parser.cards)}")
    target=[f"{i:04d}" for i in range(1,33)]
    ids=[]
    for card in parser.cards:
        match=re.match(r"g(\d{4})\b",card["title"])
        if not match:raise ValueError("Card missing generation ID")
        ids.append(match.group(1))
    if ids!=target:raise ValueError("Duplicate, unordered or omitted generations")
    for i in range(1,33):
        g=f"{i:04d}";assets=parser.cards[i-1]["assets"]
        if i<=26:
            film=(f"video-{g}-{video_manifest[g]}.mp4" if 2<=i<=25 else
                  "video-0001-14498676883.mp4" if i==1 else "video-0026-14651386328.mp4")
            expected={film,f"ontogenesis-atlas-{g}.png"}
            if not expected<=assets or "archived-film" not in parser.cards[i-1]["kinds"]:
                raise ValueError(f"Generation {g} lacks its actual archived source movie or poster")
        elif i==27:
            if (f"ontogenesis-atlas-{g}.png" not in assets or
                "measured-plot" not in parser.cards[i-1]["kinds"]):
                raise ValueError("G0027 must show actual structural-statistics measurements")
        else:
            film,kind=FILMS[g]
            if film not in assets or kind not in parser.cards[i-1]["kinds"]:
                raise ValueError(f"Missing verified G{g} visual edition")
    g32=parser.cards[31]
    required={"ontogenesis-0032-spatial.mp4","g0032-native-fields-seed73.npz"}
    if not required<=g32["assets"] or "spatial-film" not in g32["kinds"]:
        raise ValueError("G0032 native spatial alternative missing or misidentified")
    missing=parser.assets-set(available)
    if missing:raise ValueError("Visual atlas contains unavailable release assets: "+", ".join(sorted(missing)))
    if "ontogenesis-visual-poster-manifest.json" not in available:
        raise ValueError("Historic poster provenance manifest missing from release")
    if len(parser.assets)<60:
        raise ValueError("Unusually few source-backed images or videos")
    return {
        "generation_count":len(parser.cards),
        "generation_ids":ids,
        "distinct_release_assets_in_atlas":len(parser.assets),
        "all_embedded_release_assets_present":True,
        "g0032_native_spatial_edition":True,
        "visual_types":{kind:sum(kind in card["kinds"] for card in parser.cards)
                        for kind in ("archived-film","spatial-film","measured-animation","measured-plot")},
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--html",type=Path,default=Path("docs/visual-atlas.html"))
    p.add_argument("--videos",type=Path,default=Path("report/videos.json"))
    p.add_argument("--asset-list",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    manifest=json.loads(a.videos.read_text())
    listing=json.loads(a.asset_list.read_text())
    if "assets" in listing:listing=listing["assets"]
    available={entry["name"] for entry in listing}
    report=verify(a.html.read_text(),manifest,available)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
