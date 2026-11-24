"""G0033 Contact Cartography: show real four-axis contact geometry, not particles.

Each panel is a 4x4 contact atlas over all 16 recorded omega hyperplanes.
Inside each tile, the 16x16 image is an orthographic z-projection of the
original 16x16x16 recorded slice. Pale boundary pixels mark native 4D
exclusive-V/W face contacts (including omega-direction faces). Camera HUD
motion is purely an editorial presentation, never interpolated chemistry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ecological_diagnostic_render import background, font
from g0033_native_cinema import sources

SIZE = 16
PALETTE = {
    "v": np.array([48, 216, 193], dtype=np.float32),
    "w": np.array([252, 166, 101], dtype=np.float32),
    "both": np.array([248, 238, 174], dtype=np.float32),
    "contact": np.array([255, 247, 211], dtype=np.float32),
    "matrix": np.array([78, 78, 126], dtype=np.float32),
}
RECTS = ((40, 181, 622, 604), (658, 181, 1240, 604))


def contact_masks(v, w, threshold=0.1):
    """Return 4D contact endpoints and exactly counted unique periodic faces."""
    if v.shape != w.shape or v.ndim != 4:
        raise ValueError("Expected matching 4D numerical volumes")
    if not (0 < threshold < 1):
        raise ValueError("Invalid threshold")
    a, b = v > threshold, w > threshold
    v_only, w_only = a & ~b, b & ~a
    visible = np.zeros(v.shape, dtype=bool)
    faces = 0
    by_axis = []
    for axis in range(4):
        pair = ((v_only & np.roll(w_only, -1, axis=axis)) |
                (w_only & np.roll(v_only, -1, axis=axis)))
        count = int(np.count_nonzero(pair))
        faces += count
        by_axis.append(count)
        # A face stored at i connects i to i+1 on this periodic axis.
        visible |= pair | np.roll(pair, 1, axis=axis)
    return visible, faces, by_axis


def tile(v, w, m, contacts, omega):
    """Encode observed chemistry and contact pixels by max/mean projection over z."""
    if any(a.shape != (SIZE,) * 4 for a in (v, w, m, contacts)):
        raise ValueError("Contact atlas expects 16^4 native arrays")
    active_v = (v[omega] > .1).sum(axis=0).astype(np.float32) / SIZE
    active_w = (w[omega] > .1).sum(axis=0).astype(np.float32) / SIZE
    struct = (m[omega] > .2).sum(axis=0).astype(np.float32) / SIZE
    boundary = contacts[omega].any(axis=0)
    # Dim layers convey z-column occupancy; not inferred sub-voxel geometry.
    rgb = np.broadcast_to(np.array([10, 22, 35], dtype=np.float32),
                          (SIZE, SIZE, 3)).copy()
    rgb += struct[..., None] * PALETTE["matrix"][None, None] * .48
    rgb += active_v[..., None] * PALETTE["v"][None, None] * .90
    rgb += active_w[..., None] * PALETTE["w"][None, None] * .90
    # The bright contact contour is mapped from exact 4D adjacent sites.
    rgb[boundary] = PALETTE["contact"]
    return Image.fromarray(np.uint8(np.clip(rgb, 0, 255)), "RGB")


def snapshot_visuals(pair):
    """Precompute each independently archived time sample; no synthetic times."""
    times = pair[0][1]["sample_steps"]
    outputs = []
    for data, info, sha in pair:
        arm = "separated_070"
        frames = []
        for i, step in enumerate(times):
            v, w, m = (data[f"{arm}_{ch}"][i] for ch in ("v", "w", "m"))
            masks, faces, by_axis = contact_masks(v, w)
            cells_v, cells_w = int((v > .1).sum()), int((w > .1).sum())
            tiles = [tile(v, w, m, masks, omega).resize((83, 83), Image.Resampling.NEAREST)
                     for omega in range(SIZE)]
            frames.append({"step": int(step), "tiles": tiles,
                           "faces": faces, "faces_by_axis": by_axis,
                           "cells_v": cells_v, "cells_w": cells_w})
        outputs.append({"seed": info["seed"], "archive_sha256": sha,
                        "snapshots": frames})
    return outputs


def frame(visuals, index, count, times, base=None):
    if not 0 <= index < count or count < 2:
        raise ValueError("Invalid film frame")
    pct = index / (count - 1)
    sampled = min(len(times) - 1, int(pct * len(times)))
    # The moving focus visits all fourth-axis planes; actual samples never blend.
    focused = min(15, int(pct * 16))
    im = base.copy() if base is not None else background()
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1280, 7), fill="#6DE7D3")
    d.text((40, 21), "ONTOGENESIS / G0033 / FOUR-DIMENSIONAL CONTACT CARTOGRAPHY",
           font=font(19, True), fill="#6CE4D6")
    d.text((40, 60), "WHERE TWO WORLDS TOUCH",
           font=font(43, True), fill="#F2F7FD")
    d.text((42, 120),
           f"Recorded step {times[sampled]:03d}/240   |   16 hyperplanes per seed   |   focused omega {focused:02d}",
           font=font(17), fill="#BED2E2")
    for view, rect in zip(visuals, RECTS):
        x0, y0, x1, y1 = rect
        record = view["snapshots"][sampled]
        d.rounded_rectangle(rect, radius=12, fill="#11283A",
                            outline="#446376", width=2)
        d.text((x0 + 7, 151), f"SEED {view['seed']}  ·  STRONG NICHE",
               font=font(16, True), fill="#EFF7FC")
        for omega, cell in enumerate(record["tiles"]):
            col, row = omega % 4, omega // 4
            ox = x0 + 35 + col * 129
            oy = y0 + 8 + row * 103
            d.rounded_rectangle((ox - 3, oy - 3, ox + 92, oy + 91),
                                radius=5, fill="#091C2B",
                                outline="#FFE6A8" if omega == focused else "#284559",
                                width=3 if omega == focused else 1)
            im.paste(cell, (ox + 3, oy + 3))
            d.text((ox + 30, oy + 86), f"{omega:02d}", font=font(10),
                   fill="#FCEFC5" if omega == focused else "#91AFBD")
        d.text((x0 + 12, 610),
               f"Contact faces: {record['faces']:,}   V sites: {record['cells_v']:,}   W sites: {record['cells_w']:,}",
               font=font(13), fill="#DDEAF4")
    d.rounded_rectangle((41, 640, 1238, 674), radius=8, fill="#224358")
    d.text((54, 646),
           "TEAL V   /   AMBER W   /   VIOLET MATRIX   /   PALE GOLD = ACTUAL 4D CONTACT ENDPOINT",
           font=font(14), fill="#ECF5FA")
    d.text((42, 688),
           "ORTHOGRAPHIC Z-PROJECTIONS OF STORED 4D STATES · HIGHLIGHTED OMEGA PLANE IS DISPLAY-ONLY",
           font=font(11), fill="#BBD3E1")
    d.rectangle((0, 713, round(1280 * pct), 720), fill="#65DECB")
    return im


def render(a, am, b, bm, movie, poster, *, seconds=24, fps=24):
    if seconds not in (2, 24, 36) or fps not in (8, 24):
        raise ValueError("Outside bounded contact-cartography cinema budget")
    pair = sources(a, am, b, bm)
    visuals = snapshot_visuals(pair)
    times = pair[0][1]["sample_steps"]
    import imageio_ffmpeg
    movie, poster = Path(movie), Path(poster)
    movie.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel",
               "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "1280x720", "-r", str(fps), "-i", "-", "-an",
               "-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(movie)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    count = seconds * fps
    fingerprints = []
    base = background()  # Expensive static gradient calculated once, not 576 times.
    try:
        for i in range(count):
            im = frame(visuals, i, count, times, base=base)
            if i in (0, count // 3, 2 * count // 3, count - 1):
                fingerprints.append(hashlib.sha256(im.tobytes()).hexdigest())
            if i == count * 3 // 4:
                im.save(poster)
            proc.stdin.write(im.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait() != 0 or not movie.is_file() or movie.stat().st_size < 8192:
        raise RuntimeError("Contact cartography MP4 encoding failed")
    if len(set(fingerprints)) != 4 or poster.stat().st_size < 4096:
        raise RuntimeError("Duplicate temporal frames or missing poster")
    result = {
        "generation": "0033",
        "edition": "native-four-axis-contact-cartography-v1",
        "seeds": [v["seed"] for v in visuals],
        "sources_sha256": {str(v["seed"]): v["archive_sha256"] for v in visuals},
        "arm": "separated_070", "n": 16, "steps": 240,
        "sample_steps": times,
        "contacts_definition": "Exclusive V/W periodic face adjacency in all 4 native axes",
        "contact_visual": "Endpoints of exactly measured periodic 4D faces",
        "spatial_projection": "z occupancy projected to native y/x for each omega plane",
        "threshold_v_w": 0.1, "matrix_threshold": 0.2,
        "all_omega_hyperplanes": list(range(16)),
        "numerical_interpolation": False,
        "focus_animation_is_display_only": True,
        "endpoint_contacts_by_seed": {str(v["seed"]): v["snapshots"][-1]["faces"]
                                       for v in visuals},
        "frames": count, "seconds": seconds, "fps": fps,
        "width": 1280, "height": 720,
        "render_revision": os.getenv("GITHUB_SHA", "unversioned"),
    }
    movie.with_suffix(".render.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("a", "am", "b", "bm", "movie", "poster"):
        p.add_argument("--" + name, required=True, type=Path)
    p.add_argument("--seconds", type=int, default=24)
    p.add_argument("--fps", type=int, default=24)
    args = p.parse_args()
    print(json.dumps(render(args.a, args.am, args.b, args.bm, args.movie,
                            args.poster, seconds=args.seconds, fps=args.fps), indent=2))
