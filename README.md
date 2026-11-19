# Ontogenesis

An experiment in computational emergence. Each generation preserves its rules, seed, metrics and render.

## Latest animation — Generation 0004: Dynamics

[Download latest MP4 (inside artifact ZIP)](https://github.com/interrupt21h/ontogenesis/actions/runs/44457031645/artifacts/14497588149) · [Latest Dynamics workflow runs](https://github.com/interrupt21h/ontogenesis/actions/workflows/dynamics.yml)

Extract `evolution.mp4` from the ZIP. GitHub authentication is required; artifacts expire after 30 days. The workflow page provides newer successful runs.

## Generations

- Generation 0005: Matter-driven flow feedback — `feedback.py` ([CI renders and MP4](https://github.com/interrupt21h/ontogenesis/actions/workflows/feedback.yml); verification pending)

- Generation 0004: Dynamic transport — `dynamics.py`
- Generation 0003: Spatial niches — `symmetry.py`
- Generation 0002: Competing species — `diversification.py`
- Generation 0001: Gray–Scott reaction diffusion on a periodic lattice.

Run `pip install -r requirements.txt` then `python render.py`. Outputs are written to `gallery/`. GitHub Actions archives them.
