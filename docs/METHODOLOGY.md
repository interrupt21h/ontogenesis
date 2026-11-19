# Experimental methodology and documentation policy

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
