# Repository instructions

Every new Ontogenesis generation must include a detailed generation record, consolidated history update and README index update. Follow [docs/METHODOLOGY.md](docs/METHODOLOGY.md) and [docs/GENERATION_TEMPLATE.md](docs/GENERATION_TEMPLATE.md). Preserve original generation code. Mark results pending until CI verifies execution; subsequently record measured results and artifact provenance. Keep video as a standalone raw MP4, diagnostics separate. Do not claim causal findings without controls. Document numerical limitations and design decisions.

## Mathematical typography

Use GitHub native LaTeX math blocks (fenced `math` or double-dollar delimiters) for display equations and single-dollar delimiters for inline notation. Break long equations across lines, define symbols, and use separate descriptive headings for distinct equations. Do not place mathematical models in plain-text code fences. See [GitHub mathematical expressions](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).

## Living monograph

Keep report/introduction.md mechanism map and analytical or measured illustrations current; report/build.py regenerates the complete LaTeX monograph from docs/HISTORY.md. Verify scientific-report CI, retain the standalone PDF, and update the README with the newest verified direct PDF artifact link when available. Label diagrams as conceptual or measured; do not invent simulation images. Preserve the durable report workflow link.

For each newly verified standalone MP4, add its artifact ID to report/videos.json. The report workflow extracts three actual playback frames; verify availability and compilation before changing the README direct PDF link. Cached frames are an optimization, not permanent archival storage. Never substitute conceptual imagery for missing frames.

## Visual editorial standard

Every generation must include a mechanism-specific SVG under docs/figures/NNNN.svg, embedded in its descriptive Markdown page and reused by the report compiler. Clearly distinguish mechanism schematics, analytical plots and actual simulation frames. Preserve existing equations and provenance. Add measured charts and representative real frame images wherever available. Verify PDF compilation and inspect layout when possible; do not claim visual verification from CI alone. Local report builds require librsvg2-bin in addition to existing dependencies.

## Atlas publication layout
Use navy, teal and amber accents, serif scientific text and sans-serif plate labels. For dashboard generations use full-text-width original frames without a restrictive height cap. Provide labeled individual native-pixel subplot crops on dedicated detail pages when the layout is known; never infer measurements from crops. Verify pagination and legibility visually before describing an edition as publication-ready.

## Numerical observation policy
Preserve native numerical fields for new model revisions at documented steps. Include axis order, shape, dtype, seed, source revision, field semantics and threshold definitions. Adapt the archive schema for different genotype counts rather than mislabeling fields. Publish verified observations separately from MP4s. Generate quantitative plates from archived values; explicitly distinguish sections, projections and interpolated views. Never reconstruct missing concentrations from video colors. Observation archives are not restart checkpoints unless integrator and RNG state are also preserved and restart equivalence is tested.


## Final creative phase: G0028–G0032
The owner-approved direction is G0028 environmental disturbances and recovery; G0029 adaptive transport networks; G0030 ecological succession; G0031 functional compartmentalization; G0032 extended-universe finale. Treat G0032 as the planned endpoint, not a promise that every mechanism will succeed. Favor visibly dynamic, informative outcomes and matched-seed controls over adding complexity for its own sake. Preserve the original two-day creative window separately from later work. Do not claim predicted visual behavior as measured results.

## Infrastructure isolation and execution budget
Use standard GitHub-hosted CPU Actions runners only; do not use employer systems, local GPU infrastructure, self-hosted runners, external compute services or work credentials. Use explicit CPU/memory/time budgets, smoke-test gates, bounded parameter pilots, manual dispatch for expensive jobs, and conservative matrix parallelism. Profile before increasing domain size or duration; favor vectorized float32 operations where numerically validated, bounded archives, and render-only workflows from retained data. Avoid redundant simulation runs from documentation edits. Larger domains are optional and contingent on measured runner resource requirements; never assume GPU access. Keep native provenance and numerical controls. Where feasible publish standalone cinematic, scientific observatory and matched-control MP4s, with documented fixed and adaptive sampling. Integrate successful results into the report, README and cumulative film; distinguish schematics from actual observations. Do not silently reduce scientific controls to meet budget: document any reduced scope.


## Artistic priority and visual acceptance standard (G0028 onwards)
Ontogenesis is primarily an evolving, distinctive work of computational art. Its
featured films must communicate *dynamic artificial-life behavior*, not just
animate diagnostic graphs. The canonical artistic artifact is a standalone,
cinematically edited MP4 with actual changing simulated fields and an intelligible
temporal arc; charts, readouts and matched-control movies are secondary evidence.
Present a spatially expressive view (sections, measured volumetric projections,
traced field structures, or comparable nontrivial modes), meaningful motion,
coherent color direction, and clear development before and after each event.
Use longer pre-event development and avoid showcasing early transient collapse as
mature ecological activity. Inspect actual rendered frames: CI passing and
encoding success alone do NOT establish artistic merit.

Keep the art scientifically attributable: spatial/temporal interpolation,
adaptive exposure, voxel glyphs, contour lines, camera motion and symbolic
event markers are permitted *presentation operations*, explicitly distinguished
from numerically evolved concentrations. Never fabricate organism structures,
invent unavailable 4D observations or imply that renderer camera motion is a
physical current. Preserve raw numeric observations and source provenance so
the visual language can evolve independently. A low-domain smoke video is a
technical preview; do not silently promote it as full-domain evidence. Never
replace a verified featured video with a worse test render; keep the older
artifact accessible until the new visual has been inspected and approved.


## G0025 baseline for future cinematic visual fidelity
G0025 is the minimum reference standard, not a discarded old render.
New featured films should match or exceed the prior full 24⁴ lattice,
4,800-step simulation, four-step native observation cadence and
96³ 3D orthographic ray-integrated light rendering where applicable.
Use multiple observed omega positions rather than silently collapsing
a 4D world to one unchanging fixed section. Do not confuse 1280×720
encoded pixels with numerical spatial resolution; record sample counts,
ray-grid dimensions, physical field channels and numerical precision.
Retain full-precision native field observations when affordable while
using bounded float16 visual archives if explicitly identified.

Do not promote a technically passing movie unless visual inspection
reveals actual spatial structure and temporal evolution. Inspect contact
sheets across early formation, disturbance and late response, and
preserve earlier verified featured art if a new candidate looks worse.
Dynamic exposure must be documented and must not turn homogeneous
extinct chemistry into artificial organisms. The cost of fidelity
is subject to the independent GitHub-hosted CPU runner budget.
