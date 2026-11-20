# Evolution of the computational production framework

I began this project to explore continuous integration through a complicated, visually expressive system. The infrastructure was not specified in advance: it evolved alongside the mathematical models and their instruments of observation. Over the initial November 19–20, 2026 creative window, I delegated much of the engineering and mathematics to AI while concentrating my attention on the aesthetics and intelligibility of the outputs.

## Architectural progression

| Stage | Production responsibility |
|---|---|
| G0001 | Python execution, static images and JSON metrics |
| G0002 onward | Generation-specific simulation and MP4 encoding |
| G0012 onward | Higher-dimensional sections and subsequent identity diagnostics |
| G0024–25 | Native numerical state archives and observation variants |
| Publication layer | Independent PDF, reconciliation and cumulative film workflows |
| G0026 | Observer independence checks at smoke and full scales |

These are architectural milestones, not claims that all later facilities were available when each earlier experiment first ran.

The initial render workflow installs Python dependencies and executes a seeded model, retaining the gallery as an artifact. Later workflows add FFmpeg and stand-alone MP4 artifacts alongside diagnostic archives. Separate generation entry points protect the historical models from being overwritten by subsequent experiments.

As the artifacts became more complex, the report acquired a separate build pipeline: retrieve indexed video samples and archived numerical fields, generate figures, compile Pandoc and LaTeX, inspect the PDF and publish it. The film pipeline independently discovers successful main-branch experiments, normalizes video geometry and frame rate, assembles labelled chapters and checks decoding before release. The reconciliation workflow updates verified records for its configured generations and explicitly dispatches the report. The film is not a continuous numerical trajectory across generations.

## Resource management and publication

The simulation jobs for G0024 and G0025 were changed to manual dispatch (subsequently allowing workflow-file changes to trigger deliberate refreshes) to avoid expensive reruns caused by changes to observational code. The report uses concurrency cancellation to discard superseded builds; the film serializes publication. Frame caches and persistent release assets reduce reliance on temporary artifacts. These policies trade immediate recomputation for explicit control over numerical expense.

A successful experiment is not equivalent to successful downstream publication. Release files may lag source changes, and artifact expiry can prevent historical reconstruction. Publication therefore depends on preserved source data, not solely on workflow success. The workflow topology illustration records declarative completion triggers; explicit CLI dispatches and path-filtered push triggers are additional edges described in the source.

## Post-consolidation execution discipline

G0027 now executes only a verified short smoke test on push, with the expensive 24⁴ / 4800-step simulation and optional repeated observer pass behind explicit manual inputs. G0026 received the same manual gate for its historical full-domain reference after optional, default-inert intervention and observation hooks were introduced. The G0028 paired shock experiment adds a budgeted automatic 12⁴ pilot and a separately opted-in 24⁴ two-universe run. Its complete numeric result is archived as JSON; measured-field video rendering and the scientific PDF are downstream activities and do not rerun the simulation. A corrected six-panel pilot film holds authentic sampled frames for legibility rather than interpolating new numerical states.

The evolution film no longer rebuilds when the G0026 smoke check passes. Subsequent media-manifest updates, rather than unrelated documentation changes, initiate new film editions. This protects limited GitHub-hosted CPU runner time without weakening the documented controls.

## Failure and adaptation

| Observed pressure | Engineering response |
|---|---|
| Runner usage limits reported during the experiment | Separate expensive numerical execution from presentation |
| Superseded report builds | Concurrency cancellation; distinguish cancellation from failure |
| Unnecessary G0024–25 simulation triggers | Manual dispatch for those experiments |
| Temporary artifact lifetime | Persistent release archives and source identifiers |
| FFmpeg concat failure in run 44770439965 | Correct escaped newline in manifest (commit ad3d6a7) |
| Observer-dependent presentation | G0026 checkpoint hash comparison |

The FFmpeg defect is documented by the [failed film run](https://github.com/interrupt21h/ontogenesis/actions/runs/44770439965) and [corrective commit](https://github.com/interrupt21h/ontogenesis/commit/ad3d6a7a3d57397cbec0274a20a825edffa47459). A correction is not evidence of a successful rerun. Other failures require their own log evidence; the aggregate status chart does not infer causes from conclusions.

## Interpretation of engineering measurements

The recorded milestone window begins with the first numerical workflow at 04:06:58 UTC on November 19 and ends with film integration at 16:09:07 UTC on November 20. It spans 36 hours, 2 minutes and 9 seconds. The charts distinguish source growth, run envelopes, completed-job overlap and observable artifact storage. They do not measure human effort, billed runner time, mathematical sophistication or scientific validity.

I regard this infrastructure as a principal outcome of the creative experiment. My ability to direct an increasingly complex production process extended beyond my independent ability to implement and validate all of its components. The limits of the infrastructure and the mathematical models are therefore part of the record.

## Topology presentation refresh

Generations 0020–0025 now share a threshold-sensitive topology dashboard. It preserves the original secondary complement measurement, presents absolute component sizes and adaptive cell-count scaling, and shows coverage at matrix thresholds 0.10, 0.15 and 0.20. Successful refreshed runs are reconciled into the video manifest and generation records before report regeneration. Historical videos remain historical until replacement runs succeed. No numerical equations were modified.


## The G0028 artistic publication path

A limitation became visible when the first G0028 science pilot generated little
compelling motion: the 12⁴ chemical populations collapsed early, while the
six-panel presentation showed mostly diagnostic summaries. The project now
retains that pilot as measurement evidence, separately from its featured
artistic intent. The new G0028 pipeline records actual 3D fixed-omega
concentration volumes for five fields from a single four-dimensional
universe, archives them in a SHA-256-checked compact NPZ, and uses an
independent renderer with orbiting voxel projections, real 2D sections,
spatial contrast, and explicitly aesthetic temporal blending.

The automatic small-domain preview passed in [run 44829195043](https://github.com/interrupt21h/ontogenesis/actions/runs/44829195043).
A 60-second, 24⁴ / 4800-step cinematic master was explicitly opted in
through one marked GitHub commit, gated by the preview rather than triggered
on all code pushes. Preview media, field values, manifest and poster are
preserved as durable release assets and can be rerendered in a manual
render-only job without recomputing the underlying experiment. Visual
improvement is assessed separately from scientific validation and full
master results remain pending until its Actions execution finishes.


## Protecting the visual fidelity benchmark
The G0028 cinema review established a numerical and artistic reference:
G0025 generated full 24⁴ simulations at a four-step native observation
cadence and used 96³ 3D orthographic ray integration. The initial G0028
cinematic branch reduced the archived temporal cadence to 30 steps,
recorded one 3D omega hyperplane and replaced volume integration with
a stylized voxel cloud. Its encodings succeeded, but the small-domain
preview could not show a mature ecosystem and did not match the prior
rendering sophistication.

The independent [fidelity archive](../disturbance_cinematic_fidelity.py)
records four spatially distinct omega sections per observed state,
seven changing numerical fields, every-four-step samples and eight
full-precision 4D source keyframes (not complete restart state).
Its companion [renderer](../disturbance_fidelity_render.py) restores
G0025-class 96³ trilinear volume integration, with spatially measured
matrix-gradient illumination and an extinction-aware exposure gate.
Camera and time/omega interpolation remain declared visualization
operations rather than new differential updates. The old matched
control experiment and 12⁴ cinematic preview retain their historical
provenance; no higher-quality output is declared published until
CI and visual inspection justify the promotion.
