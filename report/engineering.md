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
