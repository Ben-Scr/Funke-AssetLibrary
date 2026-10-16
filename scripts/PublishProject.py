#!/usr/bin/env python3
"""Package a Funke project and produce an index.json entry for it.

Usage example
-------------
    python scripts/PublishProject.py \
        "C:\\Users\\benso\\Index\\Projects\\Pong" \
        --id pong --version 1.0.0 \
        --short "Two-paddle Pong starter." \
        --tags 2d,starter,arcade

This produces:
    <out-dir>/pong-1.0.0.zip
    <out-dir>/pong-1.0.0.entry.json    (paste into index.json's entries[])

It does NOT create the GitHub Release for you. After running this script:
    1. Go to https://github.com/<owner>/<repo>/releases/new
    2. Tag = "<id>-<version>" (e.g. "pong-1.0.0")
    3. Drag the zip in as a release asset.
    4. Optionally drag a thumb.png + screenshot-*.png next to it.
    5. Publish.
    6. Paste the printed entry into index.json (or use --append to write it directly).
    7. Commit + push index.json.

The script reads <project>/project.json to default `engineMinVersion`,
`requiredPackages`, and `name` if you don't pass them explicitly.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Default canonical library coordinates — used when the script can't
# detect git remotes (e.g. running outside a checkout). Community
# contributors should be running from their fork, in which case the
# auto-detection picks up their fork's owner/repo automatically.
DEFAULT_OWNER = "Ben-Scr"
DEFAULT_REPO = "Funke-AssetLibrary"


def detect_git_remote_owner_repo() -> tuple[str | None, str | None]:
    """Read `git remote get-url origin` and parse out (owner, repo).

    Handles both forms GitHub returns:
        https://github.com/<owner>/<repo>.git
        git@github.com:<owner>/<repo>.git

    Returns (None, None) if git isn't installed, the cwd isn't a repo,
    or origin doesn't point at a github.com URL. Failure is silent — the
    caller falls back to the default constants.
    """
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, None
    if proc.returncode != 0:
        return None, None
    url = proc.stdout.strip()
    # https://github.com/<owner>/<repo>(.git)?
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if m:
        return m.group(1), m.group(2)
    # git@github.com:<owner>/<repo>(.git)?
    m = re.match(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    return None, None

# Build / IDE artifacts that should never end up in a published archive.
# Matched against any path segment (file or directory name).
EXCLUDE_DIR_NAMES = {
    "bin", "obj", ".vs", ".vscode", "__pycache__", ".idea",
}
# File-name globs.
EXCLUDE_FILE_GLOBS = (
    "*.user",          # VS per-user
    "*.suo",           # VS per-user
    ".DS_Store",
    "Thumbs.db",
)


def is_excluded_dir(name: str) -> bool:
    return name in EXCLUDE_DIR_NAMES


def is_excluded_file(name: str) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDE_FILE_GLOBS)


def read_project_manifest(project_dir: Path) -> dict:
    """Read project.json from the project root. Returns {} if missing."""
    manifest_path = project_dir / "project.json"
    if not manifest_path.is_file():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"warning: project.json is malformed: {exc}", file=sys.stderr)
        return {}


def build_zip(project_dir: Path, out_zip: Path) -> None:
    """Zip `project_dir` into `out_zip` with files at the zip root.

    Excludes the standard build/IDE noise listed above. Walks the tree
    depth-first; symlinks are followed (Windows projects rarely use them).
    """
    if out_zip.exists():
        out_zip.unlink()
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for current, dirs, files in os.walk(project_dir):
            # Prune excluded dirs in-place so os.walk doesn't recurse into them.
            dirs[:] = [d for d in dirs if not is_excluded_dir(d)]
            for fname in files:
                if is_excluded_file(fname):
                    continue
                abspath = Path(current) / fname
                rel = abspath.relative_to(project_dir).as_posix()
                zf.write(abspath, rel)


def sha256_of(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_entry(args: argparse.Namespace, project_meta: dict,
                zip_path: Path, sha: str, size: int) -> dict:
    """Assemble the index.json entry dict from CLI flags + project manifest.

    The archive URL is rooted at github.com/<archive-repo>/releases/download/
    <archive-tag>/<archive-filename> — see resolve_archive_target() for how
    those defaults flow from CLI flags + git-remote autodetection.
    """
    archive_repo = args.archive_repo  # already resolved by resolve_archive_target()
    archive_tag = args.archive_tag
    archive_filename = args.archive_filename
    base_release_url = (f"https://github.com/{archive_repo}"
                        f"/releases/download/{archive_tag}")
    archive_url = f"{base_release_url}/{archive_filename}"

    name = args.name or project_meta.get("name") or args.id
    engine_min = args.engine_min or project_meta.get("engineVersion") or ""
    required_packages = (
        [p.strip() for p in args.packages.split(",") if p.strip()]
        if args.packages is not None
        else list(project_meta.get("packages", []) or [])
    )
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    entry = {
        "id": args.id,
        "name": name,
        "author": args.author,
        "shortDescription": args.short,
        "description": args.description,
        "tags": tags,
        "category": args.category,
        "version": args.version,
        "license": args.license,
        "thumbnail": f"{base_release_url}/thumb.png" if args.thumbnail else "",
        "screenshots": [
            f"{base_release_url}/{name}" for name in args.screenshots
        ] if args.screenshots else [],
        "archive": {
            "url": archive_url,
            "sha256": sha,
            "sizeBytes": size,
            "rootInZip": "",
        },
        "engine": {"minVersion": engine_min} if engine_min else {},
        "requiredPackages": required_packages,
    }
    if args.homepage:
        entry["homepage"] = args.homepage
    if args.source_url:
        entry["sourceUrl"] = args.source_url
    return entry


def append_to_index(index_path: Path, entry: dict) -> None:
    """Insert/replace an entry (by id) in <repo>/index.json. Creates the file
    if it doesn't exist. Bumps `generatedAt` to now."""
    if index_path.is_file():
        data = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        data = {"schemaVersion": 1, "entries": []}

    data.setdefault("schemaVersion", 1)
    data["generatedAt"] = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = data.setdefault("entries", [])

    # Replace by id if present, otherwise append.
    for i, existing in enumerate(entries):
        if existing.get("id") == entry["id"]:
            entries[i] = entry
            break
    else:
        entries.append(entry)

    index_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def resolve_archive_target(args: argparse.Namespace) -> None:
    """Fill in archive_repo / archive_tag / archive_filename defaults.

    Defaults flow:
        --archive-repo:    user-provided OR auto-detected from cwd's git remote
                           OR fall back to "<DEFAULT_OWNER>/<DEFAULT_REPO>".
        --archive-tag:     user-provided OR, when archive-repo is the canonical
                           library repo (or a fork of it), "<id>-<version>"
                           (matches the multi-project tag scheme); otherwise
                           "v<version>" (the natural convention for a single-
                           project repo).
        --archive-filename: user-provided OR "<id>-<version>.zip" (matches the
                           filename the zip-pack step writes to dist/).
    """
    if not args.archive_repo:
        detected_owner, detected_repo = detect_git_remote_owner_repo()
        if detected_owner and detected_repo:
            args.archive_repo = f"{detected_owner}/{detected_repo}"
        else:
            args.archive_repo = f"{DEFAULT_OWNER}/{DEFAULT_REPO}"

    # The canonical library repo (and any fork named like it) holds many
    # projects under one repo, so tags need to be disambiguated by id. A
    # contributor publishing from their own project repo would prefer the
    # single-project convention `vX.Y.Z`.
    if not args.archive_tag:
        _, archive_repo_name = (args.archive_repo.split("/", 1) + [""])[:2]
        if archive_repo_name == DEFAULT_REPO:
            args.archive_tag = f"{args.id}-{args.version}"
        else:
            args.archive_tag = f"v{args.version}"

    if not args.archive_filename:
        args.archive_filename = f"{args.id}-{args.version}.zip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package a Funke project for the Asset Library and emit a "
                    "ready-to-paste index.json entry.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("project", type=Path,
                        help="Path to the Funke project root (contains project.json)")
    parser.add_argument("--id", required=True,
                        help="Stable lowercase-kebab id, used in URLs and cache paths")
    parser.add_argument("--version", required=True, help="Semver version (e.g. 1.0.0)")
    parser.add_argument("--name", help="Display name (defaults to project.json name)")
    parser.add_argument("--short", default="", help="One-line short description")
    parser.add_argument("--description", default="", help="Long description (markdown OK)")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--category", default="Template",
                        choices=["Template", "Sample", "Demo"])
    parser.add_argument("--license", default="MIT", help="SPDX license expression")
    parser.add_argument("--author", default="@Ben-Scr",
                        help='Author handle (e.g. "@Ben-Scr")')
    parser.add_argument("--engine-min", default="",
                        help="Engine min version (defaults to project's engineVersion)")
    parser.add_argument("--packages", default=None,
                        help="Comma-separated required package list "
                             "(defaults to project's `packages` array)")
    parser.add_argument("--thumbnail", action="store_true",
                        help="Include thumb.png URL slot in the entry (you upload it to the release)")
    parser.add_argument("--screenshots", nargs="*", metavar="FILE",
                        help="Screenshot filenames you'll upload to the release "
                             "(URLs are generated)")
    parser.add_argument("--homepage", default="", help="Optional homepage URL")
    parser.add_argument("--source-url", default="", help="Optional source-code URL")
    # Archive hosting target. The release lives wherever you point this.
    # Three flows:
    #   1. Author hosts on their own project repo (recommended):
    #          --archive-repo jane-doe/cool-game
    #   2. Author hosts on a fork of Funke-AssetLibrary (for contributors
    #      without a dedicated project repo). The default auto-detect picks
    #      up the fork's origin remote.
    #   3. Maintainer hosts on the canonical Funke-AssetLibrary repo. Same
    #      auto-detect path, just running from a clone of the canonical.
    parser.add_argument(
        "--archive-repo",
        default=None,
        metavar="OWNER/REPO",
        help=("GitHub repo that hosts the release asset. Auto-detected from "
              "the cwd's origin remote if not set, otherwise defaults to "
              f"{DEFAULT_OWNER}/{DEFAULT_REPO}. Use this to publish from "
              "your own project repo instead of a fork of the library."),
    )
    parser.add_argument(
        "--archive-tag",
        default=None,
        help=("Git tag of the release on --archive-repo. Defaults to "
              "'<id>-<version>' when publishing to Funke-AssetLibrary, "
              "or 'v<version>' when publishing to a single-project repo."),
    )
    parser.add_argument(
        "--archive-filename",
        default=None,
        help=("Filename of the release asset. Defaults to "
              "'<id>-<version>.zip' (the filename the script writes to dist/)."),
    )
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parent.parent / "dist",
                        help="Output directory for the zip and entry JSON")
    parser.add_argument("--append", type=Path, metavar="INDEX_JSON",
                        help="If given, also append/replace the entry in this index.json file "
                             "(typically the repo root's index.json)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    project_dir = args.project.resolve()
    if not project_dir.is_dir():
        print(f"error: project dir not found: {project_dir}", file=sys.stderr)
        return 1
    if not (project_dir / "project.json").is_file():
        print(f"error: no project.json in {project_dir}", file=sys.stderr)
        return 1

    project_meta = read_project_manifest(project_dir)

    # Fill in archive-* defaults from CLI / git remote / hardcoded fallback.
    # Done after argparse so we can classify the target below.
    resolve_archive_target(args)

    # Classify the publication target so the next-steps output matches the
    # workflow the user has chosen. Three real cases:
    #   - canonical:  archive-repo == "Ben-Scr/Funke-AssetLibrary" (maintainer push)
    #   - library_fork: archive-repo is some_user/Funke-AssetLibrary (legacy fork flow)
    #   - project_repo: archive-repo is anything else (the recommended flow —
    #     author hosts on their own project's repo)
    canonical_repo = f"{DEFAULT_OWNER}/{DEFAULT_REPO}"
    if args.archive_repo == canonical_repo:
        target_kind = "canonical"
    elif args.archive_repo.endswith(f"/{DEFAULT_REPO}"):
        target_kind = "library_fork"
    else:
        target_kind = "project_repo"

    target_label = {
        "canonical":    "(canonical library — direct push)",
        "library_fork": "(fork of the library — PR flow)",
        "project_repo": "(your project repo — PR flow)",
    }[target_kind]
    print(f"Archive host: github.com/{args.archive_repo}  {target_label}")
    print(f"Release tag:  {args.archive_tag}")

    args.out.mkdir(parents=True, exist_ok=True)
    zip_name = f"{args.id}-{args.version}.zip"
    zip_path = args.out / zip_name
    print(f"Packing {project_dir.name} -> {zip_path} ...")
    build_zip(project_dir, zip_path)

    size = zip_path.stat().st_size
    sha = sha256_of(zip_path)
    print(f"  size:   {size:,} bytes")
    print(f"  sha256: {sha}")
    if size > 50 * 1024 * 1024:
        print(f"  WARNING: zip is over 50 MB. Consider trimming Assets/ before publishing.",
              file=sys.stderr)

    entry = build_entry(args, project_meta, zip_path, sha, size)

    entry_path = args.out / f"{args.id}-{args.version}.entry.json"
    entry_path.write_text(
        json.dumps(entry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nEntry JSON written to: {entry_path}")

    if args.append:
        append_to_index(args.append, entry)
        print(f"Entry inserted into: {args.append}")
    else:
        print("\n--- paste this into index.json's `entries` array ---")
        print(json.dumps(entry, indent=2, ensure_ascii=False))

    print("\nNext steps:")
    print(f"  1. Create release: https://github.com/{args.archive_repo}/releases/new")
    print(f"     - Tag: '{args.archive_tag}'")
    print(f"     - Target: main")
    print(f"     - Attach: {args.archive_filename}"
          + (" + thumb.png" if args.thumbnail else ""))
    if args.screenshots:
        for n in args.screenshots:
            print(f"     - Attach: {n}")
    print(f"     - Publish.")
    # The zip we built may have a different filename from the release-asset
    # name the user picked via --archive-filename. Remind them to rename if so.
    if zip_path.name != args.archive_filename:
        print(f"     (rename {zip_path.name} to {args.archive_filename} before uploading)")
    if args.append:
        print(f"  2. git add index.json && git commit -m 'Add {args.id} {args.version}' && git push")
    else:
        print(f"  2. Paste the entry above into index.json, then commit + push.")
    if target_kind == "project_repo":
        print(f"  3. Open a PR on github.com/{DEFAULT_OWNER}/{DEFAULT_REPO} adding the entry.")
        print(f"     The maintainer downloads the URL, verifies the SHA, confirms the")
        print(f"     project loads, and merges.")
    elif target_kind == "library_fork":
        print(f"  3. Open a PR from your fork to {DEFAULT_OWNER}/{DEFAULT_REPO}.")
        print(f"     The maintainer reviews and (optionally) re-hosts the release on")
        print(f"     the canonical repo before merging.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
