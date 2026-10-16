# Submitting a project to the Funke Asset Library

The library is a curated catalog. The `index.json` in this repo holds
the metadata for every entry; the actual project archives live on
whatever GitHub repo the project author hosts them in. Submissions land
via PR to this repo; the maintainer reviews, validates the SHA-256, and
merges.

## TL;DR for community contributors

Publish your project to a release on **your own GitHub repo**, then open
a small PR here that adds an entry pointing at it.

```powershell
# 1. Fork Ben-Scr/Funke-AssetLibrary on github.com, then locally:
git clone https://github.com/<your-handle>/Funke-AssetLibrary.git
cd Funke-AssetLibrary
git checkout -b add-<your-id>

# 2. Pack the project + generate an entry whose URLs point at YOUR
#    project repo (where you'll upload the release).
python scripts/PublishProject.py "C:\path\to\YourProject" `
    --id your-project --version 1.0.0 `
    --archive-repo <your-handle>/<your-project-repo> `
    --short "One-line description." `
    --tags "2d,starter" `
    --thumbnail `
    --append index.json

# 3. Upload the release assets to YOUR project repo.
#    Go to https://github.com/<your-handle>/<your-project-repo>/releases/new
#    Tag = "v1.0.0", target = main
#    Drag in dist/your-project-1.0.0.zip (and thumb.png if used).
#    Publish.

# 4. Push the index.json change + open the PR.
git add index.json
git commit -m "Add your-project 1.0.0"
git push -u origin add-your-id
# Open a PR on github.com targeting Ben-Scr/Funke-AssetLibrary:main.
```

When the script runs you should see:

```
Archive host: github.com/<your-handle>/<your-project-repo>  (your project repo — PR flow)
Release tag:  v1.0.0
```

That confirms the URLs in the generated entry point at *your* repo's
release, not at this library.

### Why host on your own repo?

- Your project keeps its own version history and tags.
- You can update it (new release tag, new entry version) without forking
  this library every time.
- The library stays small — just `index.json` plus the helper script.
- It matches how Godot's asset library is set up: catalog here, content
  on the author's repo.

## What the maintainer does on review

1. Pull the PR.
2. Download the archive from the URL in the entry:
   `curl -L <archive.url> -o /tmp/x.zip`
3. Verify the SHA matches the one in the PR:
   `sha256sum /tmp/x.zip` should equal `archive.sha256`.
4. Load the project in a stock Funke install at the declared
   `engine.minVersion` to confirm it actually runs.
5. Merge.

No re-hosting. The trust root is the SHA-256 in the merged `index.json` —
if the author later swaps the zip on their release, the launcher's verify
stage aborts the download. The author *can* delete the release (making
the entry unavailable) but cannot substitute different content.

## Fallback: host on a fork of this library

If you don't have a project repo and don't want to make one, you can
host the release on your **fork of Funke-AssetLibrary** instead. Just
omit `--archive-repo` and let the script auto-detect:

```powershell
git clone https://github.com/<your-handle>/Funke-AssetLibrary.git
cd Funke-AssetLibrary
python scripts/PublishProject.py "C:\path\to\YourProject" `
    --id your-project --version 1.0.0 `
    --short "..." --tags "..." --thumbnail `
    --append index.json
```

The script picks up your fork from `git remote get-url origin` and
generates URLs like
`https://github.com/<your-handle>/Funke-AssetLibrary/releases/download/your-project-1.0.0/your-project-1.0.0.zip`.

The maintainer's review process is the same. The trade-off is that this
adds an extra release on your fork of the library (cluttering your fork)
in exchange for not needing to set up a separate project repo.

## Manual flow (no script)

If you don't want to use the helper script:

1. **Author your project as a normal Funke project.**
   - `project.json` at the root.
   - Scripts, scenes, assets under the standard `Assets/`, `Scripts/`,
     `Scenes/`, `Packages/` layout.
   - Aim for under ~50 MB total. Hard cap is 2 GB per file, ~5 GB per
     release.

2. **Zip the project directory** — files at the zip root, no wrapper
   folder. Exclude `bin/`, `obj/`, `.vs/`, `.vscode/`, `*.user`.

3. **Create a release on your project repo** (or a fork of this library)
   with a tag like `v1.0.0`. Attach the zip and any thumbnails.

4. **Compute the SHA-256** (lowercase hex):
   - PowerShell: `(Get-FileHash project.zip -Algorithm SHA256).Hash.ToLower()`
   - Bash: `sha256sum project.zip`

5. **Fork this repo**, add an entry to `index.json` following the schema
   in `README.md`. `archive.url` points at the release asset on your
   chosen host; `archive.sha256` is the hash from the previous step.

6. **Commit, push, open a PR** targeting `main` on this repo.

## Field guidance

| Field | Notes |
|---|---|
| `id` | Lowercase kebab. Stable forever — used in cache paths. |
| `category` | `Template` = starter to fork; `Sample` = self-contained showcase; `Demo` = complete polished game. |
| `tags` | Lowercase, single-word, narrow. Good: `2d`, `arcade`, `tutorial`. Bad: `Game`, `MyAwesomeProject`. |
| `engine.minVersion` | Lowest Funke version known to work. Test before submitting. |
| `requiredPackages` | Match the names in your project's `project.json` `packages` array. Users missing these see a red pill in the detail modal. |
| `license` | SPDX expression (`MIT`, `Apache-2.0`, `MIT OR Apache-2.0`, etc.). |

## Trust model

- `archive.sha256` in the merged `index.json` is the trust root. The
  launcher computes the SHA after downloading and refuses to import if
  the bytes don't match.
- Only this repo's maintainers can edit `index.json`. Authors host their
  own archives but cannot substitute different content without producing
  a SHA mismatch.
- The launcher's archive-URL allow-list accepts any `github.com`,
  `objects.githubusercontent.com`, `raw.githubusercontent.com`, or
  `codeload.github.com` URL. Non-GitHub hosts are rejected client-side.

## Code execution disclosure

Downloaded projects compile and run C# (and possibly native C++) when
the user clicks Open in the launcher. The launcher shows a one-time
"community content" disclosure modal before the first download from this
library; submissions don't bypass that.
