# Keeping the machinery running

Ontogenesis is not just a sequence of numerical experiments. It is also an increasingly elaborate attempt to turn GitHub Actions into a small computational studio: run a simulation, collect the outputs, render something interesting, package the results, and publish a coherent record without manually assembling every artifact.

The entertaining difficulty is that each improvement introduces another thing to maintain. Higher-dimensional fields mean larger arrays. Better visuals mean more rendering. More experiments mean more artifacts, dependencies, and opportunities for an otherwise successful workflow to produce something visually disappointing. The pipeline is part of the creative exercise, not merely a delivery mechanism.

## Two kinds of complexity

Inside each experiment, local numerical rules evolve fields on a periodic lattice. Between experiments, the software, visual language, diagnostics, and automation change. Each numbered generation starts from its own initial conditions; the sequence is not a single creature growing from one saved state to the next.

Early experiments produced direct chemical-pattern images. Later versions added three- and four-dimensional sections, identities, energy accounting, structural measurements, and cinematic rendering. These are different software experiments with different observing tools—not a claim that an artificial organism has been discovered.

## What the pictures can and cannot say

A film may use projection, interpolation, camera movement, color mapping, and volumetric lighting. Those techniques can make the data much more interesting to watch, but they do not add physical behavior to the simulation. Likewise, a shape that looks persistent in a movie may not be a connected or persistent structure in the underlying arrays.

The numerical archives, matched comparisons where available, and source revisions help distinguish a compelling visual from a supported numerical observation. Passing CI means the job ran and its checks passed; it does not mean the scientific interpretation is established or the film looks good.

## The real endurance test

The project is also about compute budgets, memory, storage, runner limits, rendering time, publication, and the ongoing work of keeping dependencies and artifacts aligned. Those operational details belong in the engineering notes and appendices rather than interrupting the visual story. The main journal follows what we tried and what emerged on screen; the supporting records explain how the contraption works.
