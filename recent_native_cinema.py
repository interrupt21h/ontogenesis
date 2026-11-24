"""Native 4D cinematic editions for the bounded G0030/G0031 matched studies.

The visualization uses real recorded 3D hyperplanes from sampled 4D fields.
Temporal and omega slice selection is discrete, and the smooth camera is
presentation-only. Film is not evidence of artificial organisms.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from ecological_diagnostic_render import background, font
from niche_spatial_render import scatter

TITLES = {
    "0030": ("THE SEASON CHANGES", ("UNCHANGED SUPPLY", "INVERT AT STEP 24")),
    "0031": ("THE SURVIVAL FRONTIER", ("ORIGINAL V LOSS RATE", "V LOSS RATE ×0.95")),
}


def load(archive, metadata):
    archive = Path(archive)
    info = json.loads(Path(metadata).read_text())
    sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    if sha != info.get("archive_sha256") or info.get("generation") not in TITLES:
        raise ValueError("Native archive identity or SHA-256 mismatch")
    n, times = info["n"], info["sample_steps"]
    arms = info["arms"]
    if not 8 <= n <= 16 or len(arms) != 2 or len(times) < 3:
        raise ValueError("Unexpected bounded cinematic archive")
    if info["axis_order"] != "omega,z,y,x" or info["dtype"] != "float32":
        raise ValueError("Missing native spatial axis or dtype declaration")
    if sorted(set(times)) != times or times[0] != 0 or times[-1] != info["steps"]:
        raise ValueError("Invalid native numerical sampling timeline")
    with np.load(archive, allow_pickle=False) as raw:
        if raw["steps"].tolist() != times:
            raise ValueError("Native numerical step data mismatch")
        data = {}
        for arm in arms:
            for ch in ("v", "w", "m"):
                key = f"{arm}_{ch}"
                a = raw[key]
                if a.dtype != np.float32 or a.shape != (len(times),) + (n,) * 4:
                    raise ValueError(f"Invalid original numerical field: {key}")
                if not np.isfinite(a).all() or a.min() < -1e-6:
                    raise ValueError("Corrupt native numerical concentrations")
                data[key] = np.array(a, copy=True)
    return data, info, sha


def frame(data, info, index, count, base=None):
    if count < 2 or not 0 <= index < count:
        raise ValueError("Invalid cinematic frame index")
    progress = index / (count - 1)
    times = info["sample_steps"]
    sample = min(len(times) - 1, int(progress * len(times)))
    omega = min(info["n"] - 1, int(progress * info["n"]))
    angle = .18 + math.pi * 1.7 * progress
    gen = info["generation"]
    title, labels = TITLES[gen]
    im = base.copy() if base is not None else background()
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, 1280, 8), fill="#53D9CB")
    draw.text((40, 22), f"ONTOGENESIS / G{gen} / RECORDED NATIVE FOUR-DIMENSIONAL FIELDS",
              font=font(19, True), fill="#68E9D3")
    draw.text((40, 62), title, font=font(43, True), fill="#F0F8FC")
    draw.text((42, 123),
              f"Seed {info['seed']}  ·  step {times[sample]}/{info['steps']}  ·  omega={omega}",
              font=font(18), fill="#C7D8E6")
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer)
    for arm, label, rect in zip(info["arms"], labels,
                                ((40, 174, 624, 574), (656, 174, 1240, 574))):
        draw.text((rect[0] + 8, 146), label, font=font(16, True), fill="#EDF4F9")
        draw.rounded_rectangle(rect, radius=14, fill="#192D41",
                               outline="#45647A", width=2)
        fields = {ch: data[f"{arm}_{ch}"] for ch in ("v", "w", "m")}
        v, w, both = scatter(pen, fields, sample, omega, angle, rect)
        draw.text((rect[0] + 9, 586),
                  f"Active slice cells: V {v:,}  /  W {w:,}  /  both {both:,}",
                  font=font(14), fill="#D6E6F0")
    im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    draw = ImageDraw.Draw(im)
    draw.rounded_rectangle((42, 623, 1238, 667), radius=8, fill="#254257")
    for x, color, label in ((59, "#46E7C5", "V > 0.1"),
                            (257, "#FFB16D", "W > 0.1"),
                            (457, "#7571CC", "Matrix > 0.22")):
        draw.ellipse((x, 637, x + 16, 653), fill=color)
        draw.text((x + 23, 636), label, font=font(15), fill="#E4F0F8")
    draw.text((42, 681),
              "REAL RECORDED HYPERPLANES · DISCRETE TIME/SLICES · CAMERA MOTION IS PRESENTATION",
              font=font(12), fill="#BDD4E1")
    draw.rectangle((0, 711, round(1280 * progress), 720), fill="#53D9CB")
    return im


def render(archive, metadata, movie, poster, *, seconds=30, fps=24):
    if seconds not in (2, 24, 30, 36) or fps not in (8, 24):
        raise ValueError("Unbounded cinematic render")
    data, info, sha = load(archive, metadata)
    import imageio_ffmpeg
    movie, poster = Path(movie), Path(poster)
    movie.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
        "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
        "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "fast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(movie),
    ]
    count = seconds * fps
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    bg = background()
    hashes = []
    try:
        for idx in range(count):
            im = frame(data, info, idx, count, bg)
            if idx in (0, count // 3, 2 * count // 3, count - 1):
                hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
            if idx == count * 3 // 4:
                im.save(poster)
            process.stdin.write(im.tobytes())
    finally:
        if process.stdin:
            process.stdin.close()
    if process.wait() != 0 or movie.stat().st_size < 8192:
        raise RuntimeError("Native-field video encode failed")
    if len(set(hashes)) != 4 or poster.stat().st_size < 4096:
        raise RuntimeError("Static output or invalid source poster")
    result = {
        "generation": info["generation"],
        "edition": "matched-native-4d-cinematic-v1",
        "source_archive_sha256": sha,
        "reference_pilot_sha256": info["reference_pilot_sha256"],
        "source_numerical_revision": info["source_sha"],
        "render_revision": os.getenv("GITHUB_SHA", "unversioned"),
        "seed": info["seed"], "arms": info["arms"],
        "native_axes": info["axis_order"], "native_shape": [info["n"]] * 4,
        "native_sample_steps": info["sample_steps"],
        "omega_selection": "discrete-stored-hyperplanes",
        "temporal_interpolation": False,
        "camera_motion_presentation_only": True,
        "not_organisms": True,
        "frames": count, "seconds": seconds, "fps": fps,
        "width": 1280, "height": 720,
    }
    movie.with_suffix(".render.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", required=True, type=Path)
    p.add_argument("--metadata", required=True, type=Path)
    p.add_argument("--movie", required=True, type=Path)
    p.add_argument("--poster", required=True, type=Path)
    p.add_argument("--seconds", type=int, default=30)
    p.add_argument("--fps", type=int, default=24)
    a = p.parse_args()
    print(json.dumps(render(a.data, a.metadata, a.movie, a.poster,
                            seconds=a.seconds, fps=a.fps), indent=2))
