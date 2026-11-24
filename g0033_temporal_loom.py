"""G0033 Temporal Loom: honest eight-seed, two-treatment 4D-interface time-lapse.

Film and compact interactive data are derived exclusively from actual 24-step
samples in the archived, independently run G0033 analysis JSON files.
Color interpolates between palette values, NEVER between numerical states.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from ecological_diagnostic_render import background, font

SEEDS = (42, 73, 101, 137, 211, 307, 401, 509)
ARMS = ("near_transition", "separated_070")
THRESHOLDS = ("0.05", "0.10", "0.20")
METRICS = ("four_dimensional_face_contacts", "v_active_cells",
           "w_active_cells", "both_active_cells", "contact_fraction_per_face",
           "continuous_shared_mass_ratio")
TIMES = tuple(range(0, 241, 24))
PANEL = ((36, 172, 629, 579), (651, 172, 1244, 579))


def load_evidence(files, summary):
    data = json.loads(Path(summary).read_text())
    if (data.get("generation"), data.get("n"), data.get("steps"),
        data.get("seeds")) != ("0033", 16, 240, list(SEEDS)):
        raise ValueError("Unexpected published G0033 numerical pilot")
    if len(files) != len(SEEDS):
        raise ValueError("Exactly eight seed analysis files are required")
    samples = {}
    for f in files:
        source = Path(f)
        doc = json.loads(source.read_text())
        seed = doc.get("seed")
        if seed not in SEEDS or seed in samples:
            raise ValueError("Unknown or duplicate G0033 seed")
        if (doc.get("generation"), doc.get("n"), doc.get("steps"),
            doc.get("sample_steps"), doc.get("thresholds"),
            doc.get("treatments")) != (
            "0033", 16, 240, list(TIMES), [0.05, 0.1, 0.2], list(ARMS)):
            raise ValueError("Mismatched numerical scope or arms")
        if doc["source_archive_sha256"] != data["source_archive_sha256_by_seed"][str(seed)]:
            raise ValueError("Native archive identity differs from published summary")
        for arm in ARMS:
            rows = doc["observations"][arm]
            if len(rows) != len(TIMES) or [x["step"] for x in rows] != list(TIMES):
                raise ValueError("Missing discrete observation times")
            for r in rows:
                if set(r["thresholds"]) != set(THRESHOLDS):
                    raise ValueError("Missing threshold")
                for threshold in THRESHOLDS:
                    m = r["thresholds"][threshold]
                    if any(k not in m or not math.isfinite(m[k]) or m[k] < 0
                           for k in METRICS):
                        raise ValueError("Missing / invalid observed numerical data")
                    if (sum(m[k] for k in (
                            "v_only_cells", "w_only_cells",
                            "both_active_cells", "neither_active_cells")) != 16**4):
                        raise ValueError("Native numerical classes fail to partition lattice")
            for threshold in THRESHOLDS:
                for metric in METRICS:
                    a = rows[-1]["thresholds"][threshold][metric]
                    b = data["individual_endpoints"][str(seed)][arm][threshold][metric]
                    if a != b:
                        raise ValueError("End-of-film measurement mismatches published evidence")
        samples[seed] = doc

    def metrics_for(arm, threshold, metric):
        return [[samples[seed]["observations"][arm][t]["thresholds"][threshold][metric]
                 for t in range(len(TIMES))] for seed in SEEDS]

    output = {
        "generation": "0033", "edition": "eight-seed-measured-temporal-loom-v1",
        "source": "Original G0033 analysis JSON, no reconstructed numerical states",
        "seeds": list(SEEDS), "arms": list(ARMS),
        "times": list(TIMES), "thresholds": list(THRESHOLDS),
        "metrics": list(METRICS),
        "n": 16, "steps": 240,
        "source_archive_sha256_by_seed": data["source_archive_sha256_by_seed"],
        "source_analysis_sha256_by_seed": {
            str(seed): hashlib.sha256(Path(next(f for f in files if
                json.loads(Path(f).read_text())["seed"] == seed)).read_bytes()).hexdigest()
            for seed in SEEDS
        },
        "values": {
            metric: {threshold: {arm: metrics_for(arm, threshold, metric) for arm in ARMS}
                     for threshold in THRESHOLDS} for metric in METRICS
        },
        "visual_limitations": [
            "Film advances only through actual discrete 24-step numerical snapshots",
            "Interpolation of film frames or display colors is not a new simulation state",
            "Contact faces represent thresholded periodic 4D neighbors, not cells or membranes",
            "Observed finite persistence is not proof of indefinite stable coexistence",
        ],
    }
    return output


def brightness(v, scale):
    # Log scale makes rare contacts and strong boundaries both visible.
    return math.log1p(max(0, v)) / math.log1p(max(1, scale))


def palette(x, arm):
    x = max(0, min(1, x))
    cold = (20, 39, 55)
    hot = (91, 229, 208) if arm == ARMS[1] else (252, 163, 104)
    x = x ** .72
    return tuple(round(cold[i] * (1-x) + hot[i] * x) for i in range(3))


def image_at(report, index, count, base=None):
    if count < 2 or not 0 <= index < count:
        raise ValueError("Invalid frame index")
    pct = index / (count - 1)
    ti = min(len(TIMES)-1, int(pct * len(TIMES)))
    vals = report["values"]["four_dimensional_face_contacts"]["0.10"]
    scale = max(max(max(line) for line in vals[arm]) for arm in ARMS)
    im = base.copy() if base is not None else background()
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1280, 7), fill="#69E2D5")
    d.text((39, 21), "ONTOGENESIS / G0033 / EIGHT REAL NUMERICAL HISTORIES",
           font=font(18, True), fill="#6DE0D7")
    d.text((39, 56), "THE TEMPORAL LOOM", font=font(46, True), fill="#F5F9FD")
    d.text((41, 118), "Eight seeds  ·  Two prescribed habitats  ·  Native four-axis interface contacts",
           font=font(16), fill="#BFD8E5")
    for arm, rect, heading in zip(ARMS, PANEL,
                                  ("NEAR-TRANSITION / NO NICHE",
                                   "COMPLEMENTARY NICHE / 0.70")):
        x0, y0, x1, y1 = rect
        d.text((x0 + 11, 145), heading, font=font(16, True),
               fill="#F3B88D" if arm == ARMS[0] else "#72E9D5")
        d.rounded_rectangle(rect, radius=13, fill="#11283A",
                            outline="#37586D", width=2)
        heat_x, heat_y = x0 + 73, y0 + 39
        cell_w, cell_h = 43, 36
        for row, seed in enumerate(SEEDS):
            d.text((x0 + 17, heat_y + row * 43 + 9), str(seed),
                   font=font(14, True), fill="#CBDDE9")
            for col, value in enumerate(vals[arm][row]):
                x, y = heat_x + col * cell_w, heat_y + row * 43
                color = palette(brightness(value, scale), arm)
                d.rounded_rectangle((x, y, x + 37, y + cell_h),
                                    radius=4, fill=color,
                                    outline="#EAF9F6" if col == ti else "#29465A",
                                    width=3 if col == ti else 1)
                # Literal recorded no-contact state receives a small dark dot.
                if value == 0:
                    d.ellipse((x+15, y+13, x+22, y+20), fill="#092030")
        for col, t in enumerate(TIMES):
            if col % 2 == 0:
                d.text((heat_x + col * cell_w + 5, y1 - 31), str(t),
                       font=font(11), fill="#9CBBC9")
        d.text((x0+17, y1-48), "seed", font=font(11), fill="#92ADBF")
        d.text((x1-103, y1-19), "recorded step", font=font(10), fill="#92ADBF")
    d.rounded_rectangle((38, 599, 1242, 675), radius=11, fill="#19384C")
    d.text((55, 607), f"REPLAYED NUMERICAL SNAPSHOT  {TIMES[ti]:03d} / 240",
           font=font(18, True), fill="#F4FAFD")
    n_contact = sum(vals[ARMS[1]][i][ti] > 0 for i in range(8))
    d.text((56, 639),
           f"Seeds with real niche-arm contact faces: {n_contact}/8   ·   4D periodic adjacency   ·   Threshold > 0.10",
           font=font(16), fill="#BFD9E5")
    d.text((40, 684), "EVERY CELL IS A STORED NUMERICAL OBSERVATION · COLOR ENCODING IS NOT STATE INTERPOLATION",
           font=font(11), fill="#BDD3E0")
    d.rectangle((0, 713, round(1280*pct), 720), fill="#69E2D5")
    return im


def render(report, movie, poster, *, seconds=24, fps=24):
    if seconds not in (2, 24, 36) or fps not in (8, 24):
        raise ValueError("Film duration exceeds bounded CI budget")
    import imageio_ffmpeg
    movie, poster = Path(movie), Path(poster)
    movie.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel",
               "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", "1280x720", "-r", str(fps), "-i", "-", "-an",
               "-c:v", "libx264", "-preset", "fast", "-crf", "21",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(movie)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    base = background()
    count = seconds * fps
    hashes = []
    try:
        for i in range(count):
            frame = image_at(report, i, count, base)
            if i in (0, count//3, 2*count//3, count-1):
                hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
            if i == count*3//4:
                frame.save(poster)
            proc.stdin.write(frame.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
    if proc.wait() != 0 or not movie.is_file() or movie.stat().st_size < 8192:
        raise RuntimeError("Temporal Loom MP4 failed")
    if len(set(hashes)) != 4 or not poster.exists() or poster.stat().st_size < 4096:
        raise RuntimeError("Temporal Loom has identical temporal frames or no poster")
    meta = {"generation": "0033", "edition": report["edition"],
            "source_analysis_sha256_by_seed": report["source_analysis_sha256_by_seed"],
            "source_archive_sha256_by_seed": report["source_archive_sha256_by_seed"],
            "threshold": "0.10", "metric": "four_dimensional_face_contacts",
            "arms": list(ARMS), "seeds": list(SEEDS), "times": list(TIMES),
            "numerical_interpolation": False,
            "frames": count, "seconds": seconds, "fps": fps,
            "width": 1280, "height": 720,
            "render_revision": os.getenv("GITHUB_SHA", "unversioned")}
    movie.with_suffix(".render.json").write_text(json.dumps(meta, indent=2)+"\n")
    return meta


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", nargs="+", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--movie", type=Path, required=True)
    p.add_argument("--poster", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--seconds", type=int, default=24)
    p.add_argument("--fps", type=int, default=24)
    a = p.parse_args()
    output = load_evidence(a.inputs, a.summary)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n")
    print(json.dumps(render(output, a.movie, a.poster,
                            seconds=a.seconds, fps=a.fps), indent=2))


if __name__ == "__main__":
    main()
