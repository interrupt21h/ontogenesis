# Experimental methodology and documentation policy

[← Project overview](../README.md) · [Documentation](README.md) · [Experiments](EXPERIMENTS.md) · [Execution guide](PIPELINE.md)

## Numerical conventions

Periodic lattices use unit spacing and unit time steps. The discrete Laplacian sums nearest neighbors minus twice the spatial dimension times the center. Transport uses conservative first-order upwind fluxes; heterogeneous diffusion uses face-averaged coefficients. Divergence-free prescribed velocity does not constitute a momentum-conserving fluid simulation. Concentrations and energy are dimensionless. Active chemical coverage uses concentration > 0.1; matrix coverage uses M > 0.2. Coverage is not mass fraction. All historical runs use seed 42. Each generation restarts from its own initial conditions.

## Evidence standards

Successful CI demonstrates execution and runtime assertions, not scientific validation. Preserve run IDs, final metrics, source revision and artifact links. Report hypothesized effects separately from measured outcomes. Compare matched-seed controls and parameter sweeps before asserting causality. Record uncertainty and numerical limitations, including threshold sensitivity, sample cadence, resolution, numerical diffusion, denominator floors and pooling of species. Entity lineages are overlap-based identities rather than biological ancestry.

## Required documentation for every future generation

1. Create `docs/generations/NNNN.md` before or alongside the code.
2. Describe the research question, parent generation, changed and unchanged mechanisms, equations, units/conventions, parameters, initialization, resolution, cadence, dependencies and rendering design.
3. List expected observables, invariants, limitations and planned controls. Mark results pending until CI completes.
4. Update the per-generation record with actual logged metrics, run ID, revision, outcome, artifact sizes and links; never present a schematic as a simulation result.
5. Add the generation to [HISTORY.md](HISTORY.md) and the [README index](../README.md). Update the latest verified MP4 only after success.
6. Preserve earlier source files and historical results. Keep standalone MP4 separate from diagnostics. Artifacts expire; retain key numeric results in versioned documentation.
7. Review docs together with code on each iteration. Update failed-run records and explain corrections.

## Suggested record template

See [generation template](GENERATION_TEMPLATE.md). Individual records are the primary detailed entries; the history is a consolidated narrative and should stay synchronized.

## Future experiments

Use matched-seed ensembles, ablations, stability checks, resolution tests, mass-budget diagnostics and quantitative topology. For cross-feeding, compare both directions disabled, each direction independently enabled and both enabled. For structural development, distinguish connected masks from bounded functional compartments.

## Mathematical typography

Use GitHub native LaTeX math blocks (fenced `math` or double-dollar delimiters) for display equations and single-dollar delimiters for inline notation. Break long equations across lines, define symbols, and use separate descriptive headings for distinct equations. Do not place mathematical models in plain-text code fences. See [GitHub mathematical expressions](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/writing-mathematical-expressions).

## Numerical fidelity versus moving imagery

A 1280 × 720 video frame is a display product, **not** a 1280 × 720 spatial numerical lattice. Ray sampling, field exposure, temporal interpolation, spatial reconstruction, camera orbit and animated section traversal are artistic transformations of recorded simulation states. They do not add numerical evolution. Record lattice dimensions, observation times, channel definitions, fourth-coordinate sampling and numerical precision alongside every film.

Float16 is permitted for bounded playback archives when the numerical integrator uses float32 and the conversion is declared. Eight float32 four-dimensional observations of seven fields are still **not restartable solver checkpoints** when other state or random-number continuation is absent.

## Curated artwork and publication

Use [the visual gallery](VISUAL_GALLERY.md) for current film editions and their distinct provenance, [the experiment atlas](EXPERIMENTS.md) for comprehensive numbering, and [the production guide](PIPELINE.md) for exact run commands and release conventions. CI success proves the asserted execution path; it does not justify replacing the featured artistic film without inspecting spatial detail, time progression and the full narrative arc. The selected cumulative-film source is [`report/videos.json`](../report/videos.json). Rebuilding the report **cannot** incorporate a new full paired-controlled experiment without updating its numerical source and evidence plate.
