#!/usr/bin/env python3
"""Dependency-free validation of repository Markdown, SVG and 28-generation index."""
from __future__ import annotations
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "README.md", ROOT / "AGENTS.md",
    *sorted((ROOT / "docs").rglob("*.md")),
    *sorted((ROOT / "report").glob("*.md")),
]
SVGS = sorted((ROOT / "docs" / "figures").glob("*.svg")) + sorted(
    (ROOT / "docs" / "assets").glob("*.svg"))
LINK = re.compile(r"(!?)\[([^\]]+)\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
FENCE = re.compile(r"(?ms)^(\s*)(?:~~~|`{3})[^\n]*\n.*?^\1(?:~~~|`{3})\s*$")
REMOTE = ("https://", "http://", "mailto:", "tel:", "data:")


def heading_anchors(source: str) -> set[str]:
    slugs: set[str] = set()
    occurrence: dict[str, int] = {}
    for line in source.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match is None:
            continue
        text = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", match[1])
        text = re.sub(r"[`*_~]", "", text)
        text = re.sub(r"[^\w\-\s]", "", text.lower())
        slug = re.sub(r"\s", "-", text.strip())
        count = occurrence.get(slug, 0)
        occurrence[slug] = count + 1
        slugs.add(f"{slug}-{count}" if count else slug)
    return slugs


def main() -> int:
    failures: list[str] = []
    for path in SOURCES:
        if not path.is_file():
            failures.append(f"Missing Markdown: {path.relative_to(ROOT)}")
            continue
        text = FENCE.sub("", path.read_text(encoding="utf-8"))
        for m in LINK.finditer(text):
            image, alt, url = m.groups()
            if url.startswith(REMOTE) or url.startswith("#"):
                continue
            parsed = urlsplit(url)
            target = (path.parent / unquote(parsed.path)).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)}: escapes repository: {url}")
                continue
            if not target.exists():
                failures.append(f"{path.relative_to(ROOT)}: broken link {url}")
                continue
            if image and not alt.strip():
                failures.append(f"{path.relative_to(ROOT)}: image without alt text {url}")
            if parsed.fragment and target.suffix == ".md" and path.name in {
                "README.md", "EXPERIMENTS.md", "VISUAL_GALLERY.md", "PIPELINE.md"
            }:
                if unquote(parsed.fragment) not in heading_anchors(
                    target.read_text(encoding="utf-8")
                ):
                    failures.append(f"{path.relative_to(ROOT)}: missing heading {url}")
    for path in SVGS:
        try:
            root = ET.parse(path).getroot()
            if not root.tag.endswith("svg"):
                raise ValueError("not an SVG")
        except (ET.ParseError, ValueError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    expected = [f"{n:04d}" for n in range(1, 29)]
    actual = sorted(p.stem for p in (ROOT / "docs" / "generations").glob("[0-9][0-9][0-9][0-9].md"))
    if actual != expected:
        failures.append(f"Generation records incomplete: {actual}")
    history = (ROOT / "docs" / "HISTORY.md").read_text(encoding="utf-8")
    chronology = re.findall(r"^## Generation (\d{4})", history, re.MULTILINE)
    if chronology != expected:
        failures.append(f"HISTORY chronology differs from G0001–G0028: {chronology}")
    index = (ROOT / "docs" / "EXPERIMENTS.md").read_text(encoding="utf-8")
    catalog = re.findall(r"^\|\s*\**(\d{4})\**\s*\|", index, re.MULTILINE)
    if catalog != expected:
        failures.append(f"EXPERIMENTS index differs from G0001–G0028: {catalog}")
    homepage = (ROOT / "README.md").read_text(encoding="utf-8")
    if any(name not in homepage for name in (
        "docs/EXPERIMENTS.md", "docs/VISUAL_GALLERY.md", "docs/PIPELINE.md"
    )):
        failures.append("README missing canonical navigation")
    if failures:
        for failure in failures:
            print("ERROR:", failure, file=sys.stderr)
        return 1
    print(f"PASS: {len(SOURCES)} Markdown pages, {len(SVGS)} SVG assets, "
          "28 generation records and index/history chapters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
