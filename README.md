# Ontogenesis

An experiment in computational emergence. Each generation preserves its rules, seed, metrics and render.

## Latest verified animation — Generation 0017: Ecosystem

[Download evolution.mp4 directly](https://github.com/interrupt21h/ontogenesis/actions/runs/44616522872/artifacts/14575716178) (334.5 KiB, no ZIP) · [Workflow runs](https://github.com/interrupt21h/ontogenesis/actions/workflows/ecosystem.yml)

GitHub authentication required. Artifacts expire after 30 days.

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
| 0018 | [Morphogenesis](docs/generations/0018.md) | [Python](morphogenesis.py) | [Runs](.github/workflows/morphogenesis.yml) · Pending verification |
| 0019 | [Compartmentalization](docs/generations/0019.md) | [Python](compartmentalization.py) | [Runs](.github/workflows/compartmentalization.yml) · Pending verification |

## Reproduce locally

Use Python 3.12 and a virtual environment. Install `requirements.txt`; generations 0007 onward additionally need `scipy==1.15.3`. Run the corresponding script from the repository root. Outputs are written to `gallery/`. Each workflow specifies its actual dependencies and FFmpeg encoding settings. Generated animations are separate raw MP4 artifacts where configured; diagnostics are archived separately. GitHub artifacts expire after 30 days and can be regenerated using the workflow.

## Scientific scope

The system is a phenomenological artificial-life experiment. Observed structures, signals and inherited chemistry are not evidence of consciousness or biological organisms. Reported outcomes are single-seed observations unless explicitly stated otherwise.
