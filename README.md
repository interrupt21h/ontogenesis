# Ontogenesis

![Ontogenesis — conceptual visual identity, not raw simulation imagery](docs/assets/ontogenesis-hero.svg)

**An unnecessarily elaborate experiment in computational complexity.**

*Part generative art, part evolving simulation, part GitHub Actions endurance test.*

[**Watch the latest film**](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-0028-cinematic.mp4) · [**Complete evolution**](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-evolution.mp4) · [**Visual gallery**](docs/VISUAL_GALLERY.md) · [**Illustrated field journal (PDF)**](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis.pdf) · [**Experiment index**](docs/EXPERIMENTS.md)

## Things got out of hand

Ontogenesis started with a fairly simple idea: build something complicated, let it evolve, make interesting visuals, and see how far GitHub's CI infrastructure could be pushed.

Naturally, it got out of hand.

The result is a growing collection of numerical worlds, rendering pipelines, automated experiments, videos, reports, and the machinery needed to keep them all cooperating. The simulation generates complexity. The production pipeline generates another kind of complexity. Keeping both running is half the project.

**This is not a scientific research program or a claim about artificial life.** The math and measurements are real parts of the software, but the point is exploration, generative art, automation, and the occasional surprise—not establishing biological discoveries.

## Watch the latest experiment

[![G0028 — evolving structures from a 24⁴ numerical simulation](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-0028-cinematic.png)](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-0028-cinematic.mp4)

### G0028 · Poking the universe

A 24⁴ numerical domain, 4,800 simulation steps, and a localized disturbance. The 60-second film follows what happens before and after the intervention. It is a cinematic interpretation of numerical fields, not footage of living organisms or proof of recovery.

[**Full-resolution film**](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-0028-cinematic.mp4) · [Complete evolution](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-evolution.mp4) · [Gallery](docs/VISUAL_GALLERY.md)

## What is actually happening?

| Part | What it does |
|:--|:--|
| **29 numbered experiments** | G0001–G0029 have CI-verified numerical results, including G0029's full paired study. They explore patterns, transport, energy, structure, inheritance, measurement, and disturbance |
| **Numerical worlds** | Local rules update dimensionless fields on periodic grids; some recent experiments use a 24⁴ domain |
| **Generative visuals** | Field data becomes images, sections, projections, and films |
| **GitHub Actions** | Runs experiments, builds artifacts, and helps turn the repository into a tiny computational production studio |
| **The field journal** | An illustrated PDF of what we tried, what happened, and what the machinery produced |
| **The ongoing challenge** | More elaborate simulations, better visuals, bounded compute, and fewer things falling over |

![The computational production pipeline](docs/assets/production-pipeline.svg)

*Conceptual production diagram, not a numerical simulation result.*

## A tour of the rabbit hole

| Experiments | What we played with |
|:--|:--|
| [G0001–G0005](docs/EXPERIMENTS.md#i--chemical-differentiation) | Patterns, competition, and feedback |
| [G0006–G0011](docs/EXPERIMENTS.md#ii--transport-energy-and-signaling) | Motion, resources, and signals |
| [G0012–G0017](docs/EXPERIMENTS.md#iii--higher-dimensions-and-inheritance) | Extra dimensions, identity, and inherited variation |
| [G0018–G0023](docs/EXPERIMENTS.md#iv--structure-persistence-and-controls) | Structures, connectivity, and what actually persists |
| [G0024–G0025](docs/EXPERIMENTS.md#v--structural-specialization) | Construction and maintenance |
| [G0026–G0027](docs/EXPERIMENTS.md#vi--measurement-and-instrumentation) | Better ways to observe and measure the mess |
| [G0028](docs/EXPERIMENTS.md#vii--environmental-intervention) | Disturbing the system and watching its response |
| [G0029](docs/EXPERIMENTS.md#viii--transport-with-memory) | Persistent circulation memory, with a same-seed matched control |

G0029's matched full-resolution numerical study and separate master film passed CI. G0028 remains the selected featured film; G0030–G0032 remain proposals.

## G0029 · Giving circulation a memory

The latest implementation adds structure-informed curl feedback to the existing four-dimensional flow. [See the experiment](docs/generations/0029.md) and [its workflow](.github/workflows/adaptive-transport.yml). The 12⁴ pilot becomes nearly inactive, whereas the [verified full 24⁴ paired study](https://github.com/interrupt21h/ontogenesis/actions/runs/45232504379) shows more W activity but reduced V and structural-matrix coverage in the adaptive arm. [Watch the G0029 full-resolution alternative](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis-0029-master.mp4). G0028 remains the selected cinematic artwork.

## Try it yourself

~~~bash
git clone https://github.com/interrupt21h/ontogenesis.git
cd ontogenesis
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python render.py
~~~

Later experiments have additional dependencies and can require substantial CPU time, memory, and storage. See the [pipeline and reproduction guide](docs/PIPELINE.md) before launching the heavier runs.

## The notebooks and machinery

| Read | Why |
|:--|:--|
| [Documentation hub](docs/README.md) | Find your way around |
| [Visual gallery](docs/VISUAL_GALLERY.md) | Watch the results |
| [Experiment atlas](docs/EXPERIMENTS.md) | Browse all generations |
| [Experiment history](docs/HISTORY.md) | See what changed and what was measured |
| [Numerical notes](docs/METHODOLOGY.md) | Understand the math and its limitations |
| [CI and production guide](docs/PIPELINE.md) | Keep the machinery running |
| [On delegating complexity](docs/RECURSIVE_CREATION.md) | How human direction and AI assistance shaped the project |
| [About the creator](docs/AUTHOR.md) | Background |

**Created and directed by Scott Muller.** AI-assisted implementation, GitHub-hosted execution, and a great deal of babysitting complexity. The numerical records remain available so the pretty pictures don't have to carry the burden of proof.
