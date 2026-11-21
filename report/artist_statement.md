# Delegating complexity

*Notes on making something unnecessarily complicated with AI assistance and GitHub Actions.*

## The idea

I wanted to see how far I could push a loosely directed computational project: give it a set of evolving rules, make it produce interesting images, and use GitHub's CI infrastructure to do the heavy lifting. Artificial-life-like simulations turned out to be a rich source of visual material, but Ontogenesis was never intended as a formal investigation of biology or a claim to have created life.

What interests me is the whole contraption. A short idea turns into code; code turns into a simulation; the simulation turns into data; the data becomes a film; and then the machinery has to package, document, and publish it. Each layer creates new opportunities for complexity—and new ways for things to break.

## Human direction, AI implementation

I provided the directions, selected what seemed interesting, and paid particular attention to the visuals and presentation. AI contributed heavily to mathematical formulations, code, debugging, instrumentation, and documentation. GitHub Actions executed the jobs and produced the artifacts.

That division of labor was deliberate. I wanted to find out what could be built when I could direct technical work without personally implementing or independently understanding every mathematical component. It is an exercise in orchestration and judgment, not a claim of expertise in every discipline represented by the code.

The initial burst of work took place on November 19–20, 2026. The recorded interval from the first numerical CI run to a film-publication milestone was roughly 36 hours. That is elapsed time between two recorded events, not a measure of my working hours or a productivity benchmark.

## Three things keep evolving

**The simulated world** changes under its numerical rules. **The software** changes from one numbered experiment to the next. **The production process** changes as the workflows, renderers, checks, and documentation become more elaborate.

Those are three different forms of change. A generation is a newly initialized model experiment, not a biological descendant of the previous generation. The CI system does not magically establish what the numerical results mean. And a striking render is not proof of an interesting physical phenomenon.

## Why keep the records?

Because complexity is easier to enjoy when it is possible to tell what actually happened. Saved configurations, numerical diagnostics, source revisions, and clear distinctions between measured plots and artistic rendering help prevent the story from outrunning the evidence.

The goal is not to turn a hobby experiment into an academic paper. It is to make an engaging, technically inspectable record of an unusual creative process: keep inventing things to try, see what the machines produce, and figure out how to keep the whole increasingly absurd arrangement running.
