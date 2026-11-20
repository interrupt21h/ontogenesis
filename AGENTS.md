# Repository instructions

Every new Ontogenesis generation must include a detailed generation record, consolidated history update and README index update. Follow [docs/METHODOLOGY.md](docs/METHODOLOGY.md) and [docs/GENERATION_TEMPLATE.md](docs/GENERATION_TEMPLATE.md). Preserve original generation code. Mark results pending until CI verifies execution; subsequently record measured results and artifact provenance. Keep video as a standalone raw MP4, diagnostics separate. Do not claim causal findings without controls. Document numerical limitations and design decisions.

## Mathematical typography

Use GitHub native LaTeX math blocks (fenced `math` or double-dollar delimiters) for display equations and single-dollar delimiters for inline notation. Break long equations across lines, define symbols, and use separate descriptive headings for distinct equations. Do not place mathematical models in plain-text code fences. See [GitHub mathematical expressions](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).

## Living monograph

Keep report/introduction.md mechanism map and analytical or measured illustrations current; report/build.py regenerates the complete LaTeX monograph from docs/HISTORY.md. Verify scientific-report CI, retain the standalone PDF, and update the README with the newest verified direct PDF artifact link when available. Label diagrams as conceptual or measured; do not invent simulation images. Preserve the durable report workflow link.

For each newly verified standalone MP4, add its artifact ID to report/videos.json. The report workflow extracts three actual playback frames; verify availability and compilation before changing the README direct PDF link. Cached frames are an optimization, not permanent archival storage. Never substitute conceptual imagery for missing frames.
