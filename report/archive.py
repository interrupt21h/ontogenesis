"""Store native frame samples as durable release assets.

Retries transient GitHub Releases API errors without masking hard failures.
Existing bundles are left alone; archive names are immutable source-run IDs.
"""
from pathlib import Path
import json
import os
import subprocess
import tempfile
import time
import zipfile

root = Path(__file__).resolve().parent
repository = os.environ.get("GITHUB_REPOSITORY")
if not repository:
    raise RuntimeError("GITHUB_REPOSITORY must be defined to safely target the release")


def run_gh(*args, attempts=5):
    """Retry transient release API errors; raise on exhausted attempts."""
    for attempt in range(attempts):
        proc = subprocess.run(
            ["gh", *args], text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False,
        )
        if proc.returncode == 0:
            return proc.stdout
        detail = proc.stderr.strip() or proc.stdout.strip()
        if attempt == attempts - 1:
            raise RuntimeError(
                f"GitHub release command failed after {attempts} attempts: "
                f"{' '.join(args)}: {detail}"
            )
        delay = min(30, 2 ** (attempt + 1))
        print(f"Release API attempt {attempt + 1}/{attempts} failed "
              f"({detail[:300]}). Retrying in {delay}s...", flush=True)
        time.sleep(delay)


def existing_assets():
    # Fetch all pages: gh release view may return only a limited asset list
    # for a heavily used shared media tag.
    release = json.loads(run_gh("api", f"repos/{repository}/releases/tags/atlas-media"))
    release_id = release["id"]
    output = run_gh("api", "--paginate",
                    f"repos/{repository}/releases/{release_id}/assets?per_page=100")
    # gh api --paginate may concatenate JSON arrays. Use --jq to return one
    # asset name per line, preserving filenames with spaces if ever present.
    names = run_gh("api", "--paginate",
                   f"repos/{repository}/releases/{release_id}/assets?per_page=100",
                   "--jq", ".[].name")
    return set(names.splitlines())


present = existing_assets()
for gen, artifact in json.loads((root / "videos.json").read_text()).items():
    folder = root / "build" / "frames" / f"{gen}-{artifact}"
    meta = folder / "frames.json"
    if not meta.exists() or not json.loads(meta.read_text()).get("native_resolution"):
        continue
    name = f"frames-{gen}-{artifact}.zip"
    if name in present:
        print(f"Retaining existing immutable frame archive: {name}", flush=True)
        continue
    with tempfile.TemporaryDirectory() as tmp:
        asset = Path(tmp) / name
        with zipfile.ZipFile(asset, "w", zipfile.ZIP_DEFLATED) as bundle:
            for item in ("0.jpg", "1.jpg", "2.jpg", "frames.json"):
                bundle.write(folder / item, item)
        run_gh("release", "upload", "atlas-media", str(asset),
               "--repo", repository, "--clobber")
    present.add(name)
    print(f"Published frame archive: {name}", flush=True)
