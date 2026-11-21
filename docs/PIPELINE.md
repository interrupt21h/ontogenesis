# Production and reproducibility

[← Project overview](../README.md) · [Documentation index](README.md) · [Experiments](EXPERIMENTS.md) · [Visual gallery](VISUAL_GALLERY.md)

![Conceptual architecture from artistic direction and source code through measured numerical fields, evidence and moving imagery](assets/production-pipeline.svg)

*Software production overview, not numerical field output or a complete GitHub Actions trigger-dependency graph.*

## The model and publication layers

Ontogenesis separates numerical integration, source-field observation, visual rendering and publication. That separation protects scientific provenance while allowing experimentation with distinct artistic techniques.

| Layer | Source of truth | Output |
|:--|:--|:--|
| Numerical model | Per-generation Python programs and [experiment records](EXPERIMENTS.md) | Simulated state evolution, controls, numerical metrics |
| Experiment execution | [GitHub Actions workflows](../.github/workflows/) | Verified sampled fields, diagnostics, encoded media |
| Numerical evidence | Archived JSON/NPZ or field-state tarballs | Real observations with source revision, seed, lattice and cadence |
| Selected cumulative film | [Film generator](../report/film.py) and [media manifest](../report/videos.json) | Versioned source-film sequence and combined MP4 |
| Monograph | [Report builder](../report/build.py), [editorial source](../report/introduction.md), [history](HISTORY.md) | Illustrated LaTeX/PDF, quantitative atlas, final-render chapter |
| Durable publication | [`atlas-media` release](https://github.com/interrupt21h/ontogenesis/releases/tag/atlas-media) | Published MP4s, source archives, provenance manifests and PDF |

Historical GitHub Actions artifacts normally have **30-day retention**; cited long-term assets should also be held in the release. A stable release filename may be replaced as a later edition is verified: use accompanying source SHA, archive hashes and run IDs to distinguish revisions.

## Current full-resolution evidence and manual gates

| Experiment / output | Workflow | Current verified state |
|:--|:--|:--|
| G0024 construction | [`specialization.yml`](../.github/workflows/specialization.yml) | Full simulation and field archive retained |
| G0025 maintenance | [`maintenance.yml`](../.github/workflows/maintenance.yml) | Full simulation and visual-quality baseline retained |
| G0026 observer independence | [`consolidation.yml`](../.github/workflows/consolidation.yml) | Full 24⁴ verification passed |
| G0027 structural statistics | [`structural-statistics.yml`](../.github/workflows/structural-statistics.yml) | Full 24⁴ metrics and 41 matching same-process checkpoints passed |
| G0028 matched treatment/control | [`disturbance.yml`](../.github/workflows/disturbance.yml) | Pilot and [24⁴ full paired science run](https://github.com/interrupt21h/ontogenesis/actions/runs/44840239338) both passed; report integrates them as separate evidence plates |
| G0028 first full cinematic | [`disturbance-cinematic.yml`](../.github/workflows/disturbance-cinematic.yml) | Full single-plane master passed CI and retained |
| G0028 full fidelity cinematic | [`disturbance-fidelity.yml`](../.github/workflows/disturbance-fidelity.yml) | Verified four-plane 24⁴ master (artifact `14680891214`) selected for cumulative-film G0028 and final PDF frame gallery |
| G0028 render-only updates | [`disturbance-fidelity-rerender.yml`](../.github/workflows/disturbance-fidelity-rerender.yml) | Uses existing NPZ source instead of recomputing a universe |
| PDF / cumulative movie | [`report.yml`](../.github/workflows/report.yml) / [`film.yml`](../.github/workflows/film.yml) | Both have verified publication runs; media selection and evidence inputs must be updated deliberately |

**The full 24⁴ paired experiment has already passed. Do not rerun it simply to refresh a PDF.** The two-arm study is considerably more expensive than a single cinematic universe; archived numerical JSON can be reused when changing the report.

### GitHub CLI

~~~bash
# Inspect the already verified full paired-control run.
gh run view 44840239338 --repo interrupt21h/ontogenesis --json status,conclusion,jobs

# Run only when an existing successful/full job is absent and no run is active.
gh workflow run disturbance.yml \
  --repo interrupt21h/ontogenesis \
  --ref main \
  -f full_resolution=true

# Rerender a retained full-fidelity archive; the integrator is not rerun.
gh workflow run disturbance-fidelity-rerender.yml \
  --repo interrupt21h/ontogenesis \
  --ref main \
  -f edition=full -f seconds=60
~~~

## Observations versus cinematic frames

The G0028 high-fidelity model evolves **24⁴ (331,776) lattice cells**. Its cinematic observer records seven fields at four selected fourth-dimensional hyperplanes at 1,203 native times and retains eight native **float32 4D seven-field observations**. Frequent visual samples are float16; the renderer interpolates them and ray-integrates a 96³ display grid to produce 1280 × 720 H.264 frames.

Rendered pixels are **not** independent numerical unknowns. Neither temporal interpolation nor moving camera coordinates create new numerical integration steps. The archived fields are **not a restart checkpoint**: complete integrator state, RNG continuation and validated restart equivalence are not retained.

## Release and scientific publication checklist

1. Verify the numerical run and its actual assertions, source SHA, seed, physical constants, and lattice configuration.
2. Verify the field schema, sample cadence, observation precision and measured JSON/NPZ assets separately from encoded MP4s.
3. Label conceptual illustrations, measured diagrams and artistic renderings distinctly.
4. Visually inspect a candidate film across formation, intervention and aftermath; passing FFmpeg is **not** an artistic review.
5. Promote the selected video by editing [`report/videos.json`](../report/videos.json) only when its captions and provenance are updated.
6. Update the scientific interpretation and measured plates separately. **Rerunning the PDF alone cannot incorporate an unreviewed full paired G0028 experiment** if its evidence input still selects the small pilot.
7. Rebuild the cumulative film and report; verify the generated PDF chapter audit and video decodability.
8. Retain unselected cinematic versions with their own manifests; never overwrite scientific evidence with a prettier film.

## Reproduce locally

~~~bash
git clone https://github.com/interrupt21h/ontogenesis.git
cd ontogenesis
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install scipy==1.15.3  # required by later generations

python render.py                # lightweight initial generation
python scripts/check_docs.py    # static Markdown link validation
~~~

The full monograph build additionally uses Pandoc, LaTeX, latexmk, librsvg2-bin, FFmpeg and numerical plotting dependencies; see [the actual workflow](../.github/workflows/report.yml) for a maintained build recipe.

The art project is isolated from employer hardware: the recorded production processes are GitHub-hosted CPU Actions, not company GPUs, self-hosted runners, or corporate credentials.
