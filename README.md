# Ontogenesis

An experiment in computational emergence. Each generation preserves its rules, seed, metrics and render.

## Artistic vision and creative methodology

Ontogenesis investigates emergence both within a simulated world and within the recursive human–AI process that constructs it. I direct the artistic inquiry while AI participates extensively in mathematical synthesis, software implementation, interpretation and documentation. The delegation of complexity is itself part of the medium.

**[Recursive creation: human intention, machine intelligence and computational emergence](docs/RECURSIVE_CREATION.md)** — an essay on the artistic method, distributed authorship and the relationship between simulated evolution and creative development.

## Latest verified animation — Generation 0023: Factorial niche controls

[Download standalone MP4](https://github.com/interrupt21h/ontogenesis/actions/runs/44687054986/artifacts/14609910431) (2.03 MiB) · [Workflow](https://github.com/interrupt21h/ontogenesis/actions/workflows/niche.yml)

Authentication required; artifacts expire after 30 days.

## Scientific and engineering monograph

**[Download current verified PDF](https://github.com/interrupt21h/ontogenesis/releases/download/atlas-media/ontogenesis.pdf)** · [Latest successful report build](https://github.com/interrupt21h/ontogenesis/actions/workflows/report.yml?query=is%3Asuccess) · [Report source](report/) · [All report builds](https://github.com/interrupt21h/ontogenesis/actions/workflows/report.yml)

Open the newest successful run and select the standalone `ontogenesis.pdf` artifact. The report samples early, middle and final frames from indexed MP4 artifacts when available. The independent LaTeX pipeline automatically rebuilds on documentation changes; the generated TeX is also archived separately. To reproduce locally, install Pandoc, latexmk, TeX Live (latex-extra, pictures, fonts-recommended) and librsvg2-bin, install NumPy and Matplotlib, then run `python3 report/build.py`.

## Experimental history

Ontogenesis investigates emergence in continuous, periodic reaction–diffusion systems, progressing from chemical differentiation through transport, energy, structural memory, signaling, four-dimensional geometry, lineage tracking, heredity and ecological interactions. Each generation is a fresh seeded experiment, not a checkpoint continuation.

**[Read the complete scientific and engineering history](docs/HISTORY.md)** · [Methodology and documentation policy](docs/METHODOLOGY.md)

| Generation | Experiment | Source | CI |
|---|---|---|---|
| 0001 | [Differentiation](docs/generations/0001.md) | [Python](render.py) | [Runs](.github/workflows/render.yml) · Verified |
| 0002 | [Diversification](docs/generations/0002.md) | [Python](diversification.py) | [Runs](.github/workflows/diversification.yml) · Verified |
| 0003 | [Symmetry breaking](docs/generations/0003.md) | [Python](symmetry.py) | [Runs](.github/workflows/symmetry.yml) · Verified |
| 0004 | [Dynamics](docs/generations/0004.md) | [Python](dynamics.py) | [Runs](.github/workflows/dynamics.yml) · Verified |
| 0005 | [Feedback](docs/generations/0005.md) | [Python](feedback.py) | [Runs](.github/workflows/feedback.yml) · Verified |
| 0006 | [Volumetric emergence](docs/generations/0006.md) | [Python](volume.py) | [Runs](.github/workflows/volume.yml) · Verified |
| 0007 | [Circulation](docs/generations/0007.md) | [Python](circulation.py) | [Runs](.github/workflows/circulation.yml) · Verified |
| 0008 | [Energetics](docs/generations/0008.md) | [Python](energetics.py) | [Runs](.github/workflows/energetics.yml) · Verified |
| 0009 | [Organization](docs/generations/0009.md) | [Python](organization.py) | [Runs](.github/workflows/organization.yml) · Verified |
| 0010 | [Communication](docs/generations/0010.md) | [Python](communication.py) | [Runs](.github/workflows/communication.yml) · Verified |
| 0011 | [Adaptation](docs/generations/0011.md) | [Python](adaptation.py) | [Runs](.github/workflows/adaptation.yml) · Verified |
| 0012 | [Hypervolume](docs/generations/0012.md) | [Python](hypervolume.py) | [Runs](.github/workflows/hypervolume.yml) · Verified |
| 0013 | [Entities](docs/generations/0013.md) | [Python](entities.py) | [Runs](.github/workflows/entities.yml) · Verified |
| 0014 | [Observatory](docs/generations/0014.md) | [Python](observatory.py) | [Runs](.github/workflows/observatory.yml) · Verified |
| 0015 | [Evolution](docs/generations/0015.md) | [Python](evolution.py) | [Runs](.github/workflows/evolution.yml) · Verified |
| 0016 | [Genetics](docs/generations/0016.md) | [Python](genetics.py) | [Runs](.github/workflows/genetics.yml) · Verified |
| 0017 | [Ecosystem](docs/generations/0017.md) | [Python](ecosystem.py) | [Runs](.github/workflows/ecosystem.yml) · Verified |
| 0018 | [Morphogenesis](docs/generations/0018.md) | [Python](morphogenesis.py) | [Runs](.github/workflows/morphogenesis.yml) · Verified |
| 0019 | [Compartmentalization](docs/generations/0019.md) | [Python](compartmentalization.py) | [Runs](.github/workflows/compartmentalization.yml) · Verified |
| 0020 | [Topological complexity](docs/generations/0020.md) | [Python](topology.py) | [Runs](.github/workflows/topology.yml) · Verified |
| 0021 | [Multiscale topological persistence](docs/generations/0021.md) | [Python](persistence.py) | [Runs](.github/workflows/persistence.yml) · Verified |
| 0022 | [Structural heredity](docs/generations/0022.md) | [Python](niche.py) | [Runs](.github/workflows/niche.yml) · Verified |
| 0023 | [Factorial niche controls](docs/generations/0023.md) | [Python](controls.py) | [Runs](.github/workflows/controls.yml) · Pending verification |
| 0024 | [Independent construction specialization](docs/generations/0024.md) | [Python](specialization.py) | [Runs](.github/workflows/specialization.yml) · Pending verification |

| 0025 | [Energy-funded structural maintenance](docs/generations/0025.md) | [Python](maintenance.py) | [Runs](.github/workflows/maintenance.yml) · Pending verification |

## Reproduce locally

Use Python 3.12 and a virtual environment. Install `requirements.txt`; generations 0007 onward additionally need `scipy==1.15.3`. Run the corresponding script from the repository root. Outputs are written to `gallery/`. Each workflow specifies its actual dependencies and FFmpeg encoding settings. Generated animations are separate raw MP4 artifacts where configured; diagnostics are archived separately. GitHub artifacts expire after 30 days and can be regenerated using the workflow.

## Scientific scope

The system is a phenomenological artificial-life experiment. Observed structures, signals and inherited chemistry are not evidence of consciousness or biological organisms. Reported outcomes are single-seed observations unless explicitly stated otherwise.
