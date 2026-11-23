"""G0029 voxel cinema from archived full-domain numerical fields.

Reuses G0028's luminous voxel projector, mapping G0029's memory channel to
the G0028 pulse-color slot. The mapping is visual, not physical equivalence.
All orbiting, exposure, interpolation, phase text and fog are presentation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from adaptive_transport_render import at, load
from disturbance_cinematic_render import camera_frame, voxel_cloud

WHITE = (230, 240, 247)
MUTED = (144, 174, 191)
TEAL = (74, 229, 219)
AMBER = (254, 181, 94)


def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def chapter(progress: float) -> str:
    """Editorial time segments, NOT automatically detected biological phases."""
    if progress < .18:
        return "I  /  INITIAL CONDITIONS"
    if progress < .40:
        return "II  /  EMERGING PATTERNS"
    if progress < .65:
        return "III  /  MEMORY AND TRANSPORT"
    if progress < .87:
        return "IV  /  REORGANIZATION"
    return "V  /  FINAL CONFIGURATION"


def arranged_fields(volume: np.ndarray) -> np.ndarray:
    """Adapt G0029 M,V,W,E,network to G0028 M,V,W,pulse,E view slots.

    The fourth slot is G0029 MEMORY here, not G0028 pulse/excitation.
    """
    if volume.ndim != 4 or volume.shape[0] != 5 or len(set(volume.shape[1:])) != 1:
        raise ValueError("Expected five measured cubic G0029 channels")
    return volume[[0, 1, 2, 4, 3]]


def mapped_section(volume: np.ndarray, meta: dict, z: int) -> Image.Image:
    """Atmospheric image from one observed/interpolated z section."""
    raw = volume[:, z, :, :]
    reference = meta["recording"]["fixed_exposure_p995"]

    def normalized(i: int, name: str, floor: float) -> np.ndarray:
        return np.clip(raw[i] / max(float(reference[name]), floor), 0, 1)

    matrix = normalized(0, "matrix", .04)
    species_v = normalized(1, "species_v", .012)
    species_w = normalized(2, "species_w", .012)
    energy_deficit = np.clip((1. - raw[3]) / .20, 0, 1)
    memory = normalized(4, "network", .015)
    rgb = np.stack((
        .028 + .65 * matrix + .43 * species_v + .14 * energy_deficit,
        .048 + .53 * species_w + .25 * memory + .12 * matrix,
        .090 + .50 * memory + .44 * species_v + .13 * species_w,
    ), axis=-1)
    return Image.fromarray(np.uint8(np.round(np.clip(rgb, 0, 1) ** .82 * 255)), "RGB")


def cinematic_frame(volume: np.ndarray, meta: dict, *, step: float,
                    width: int, height: int) -> Image.Image:
    """Full-frame luminous G0028 projection with accurate G0029 captions."""
    progress = float(step) / float(meta["steps"])
    n = volume.shape[-1]
    depth = (n * .5 + n * .88 * math.sin(2 * math.pi * (progress * .67 + .08))) % n
    section = mapped_section(volume, meta, int(round(depth)) % n)
    fog = camera_frame(section, (width, height), progress)
    cloud = voxel_cloud(arranged_fields(volume), (width, height), progress)
    frame = Image.blend(fog, cloud, .94)

    veil = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    p = ImageDraw.Draw(veil, "RGBA")
    p.rectangle((0, 0, width, int(height * .15)), fill=(5, 11, 25, 154))
    p.rectangle((0, int(height * .84), width, height), fill=(5, 11, 25, 169))
    frame = Image.alpha_composite(frame.convert("RGBA"), veil).convert("RGB")
    d = ImageDraw.Draw(frame)
    pad = int(width * .038)
    d.text((pad, int(height * .035)), "ONTOGENESIS  /  0029",
           font=font(max(20, int(height * .038)), True), fill=WHITE)
    d.text((pad, int(height * .100)), chapter(progress),
           font=font(max(12, int(height * .022)), True), fill=TEAL)
    d.text((width - int(width * .28), int(height * .066)),
           "CIRCULATION WITH MEMORY",
           font=font(max(10, int(height * .018))), fill=MUTED)
    d.text((pad, int(height * .888)), f"STEP {step:04.0f} / {meta['steps']:04d}",
           font=font(max(12, int(height * .025)), True), fill=WHITE)
    d.text((pad, int(height * .948)),
           "OBSERVED M/V/W/MEMORY VOXELS  /  DISPLAY ROTATION AND BLENDING",
           font=font(max(9, int(height * .014))), fill=MUTED)
    x0, x1, y = int(width * .40), width - pad, int(height * .908)
    d.line((x0, y, x1, y), fill=(48, 75, 92), width=4)
    d.line((x0, y, x0 + int((x1 - x0) * progress), y), fill=AMBER, width=4)
    return frame


def render(archive: Path, metadata: Path, movie: Path, poster: Path,
           *, seconds: int = 60, fps: int = 24,
           width: int = 1280, height: int = 720) -> dict:
    if not 6 <= seconds <= 180 or not 12 <= fps <= 60:
        raise ValueError("Duration 6-180 seconds, frame rate 12-60 FPS")
    if width < 640 or height < 360 or width % 2 or height % 2:
        raise ValueError("Frame dimensions must be even and at least 640x360")
    states, times, omega, meta = load(archive, metadata)
    movie, poster = Path(movie), Path(poster)
    movie.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
              "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
              "-r", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264",
              "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
              "-movflags", "+faststart", str(movie)]
    total = seconds * fps
    hashes = set()
    proc = subprocess.Popen(ffmpeg, stdin=subprocess.PIPE)
    try:
        for index in range(total):
            progress = index / max(1, total - 1)
            step = progress * meta["steps"]
            # Omega is interpolated between the four *recorded* hyperplanes.
            volume = at(states, times, omega, step, progress * len(omega) * 1.45)
            image = cinematic_frame(volume, meta, step=step,
                                    width=width, height=height)
            if index == round(total * .70):
                image.save(poster, optimize=True)
            if index % max(1, total // 12) == 0:
                hashes.add(hashlib.sha256(image.tobytes()).hexdigest())
                print(f"Voxel frame {index}/{total}: step {step:.1f}", flush=True)
            proc.stdin.write(image.tobytes())
        proc.stdin.close()
        code = proc.wait()
        if code:
            raise RuntimeError(f"FFmpeg failed with exit code {code}")
    except Exception:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        raise
    if len(hashes) < 6 or not poster.is_file() or movie.stat().st_size < 4096:
        raise AssertionError("Insufficient motion or missing cinematic outputs")
    info = {"generation": "0029", "edition": "voxel-cinema-g0028-style",
            "source_sha": meta["source_sha"],
            "archive_sha256": meta["archive"]["sha256"],
            "frames": total, "fps": fps, "width": width, "height": height,
            "unique_sampled_frame_hashes": len(hashes),
            "camera_and_fourth_axis_interpolation_are_presentation_only": True,
            "channel_mapping": {"g0028_pulse_colored_channel": "G0029 memory",
                                "g0028_energy_channel": "G0029 energy"},
            "selected_featured_film": False}
    movie.with_suffix(".render.json").write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps(info, indent=2), flush=True)
    return info


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    for option in ("input", "metadata", "movie", "poster"):
        p.add_argument("--" + option, type=Path, required=True)
    for name, default in (("seconds", 60), ("fps", 24),
                          ("width", 1280), ("height", 720)):
        p.add_argument("--" + name, type=int, default=default)
    args = p.parse_args()
    render(args.input, args.metadata, args.movie, args.poster,
           seconds=args.seconds, fps=args.fps, width=args.width,
           height=args.height)


if __name__ == "__main__":
    main()
