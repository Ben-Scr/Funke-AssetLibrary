# Submitting a project to the Index Asset Library

The library is a curated index. Every entry lands via PR; the
maintainer reviews the project, validates the archive, and merges.

## Author flow

1. **Author your project as a normal Index project.**
   - `index-project.json` at the root.
   - Scripts, scenes, assets under the standard `Assets/`, `Scripts/`,
     `Scenes/`, `Packages/` layout.
   - Keep it under ~50 MB total (GitHub release-asset etiquette;
     hard cap is 2 GB per file, ~5 GB per release).

2. **Zip the project directory.**
   - Files at the zip root (don't wrap in an extra folder). The
     launcher tolerates a single wrapper folder if it has to, but
     keeping it flat avoids ambiguity.

3. **Fork this repo, create a release on the fork.**
   - Tag: `<your-id>-<semver>`, e.g. `pong-1.0.0`.
   - Upload `<id>.zip`, `thumb.png`, and any screenshots as release assets.

4. **Open a PR** adding an entry to `index.json`.
   - Fill every required field; see the schema in `README.md`.
   - `archive.sha256` is the SHA-256 of the zip (lowercase hex).
     Compute with `sha256sum project.zip` or `Get-FileHash`.

5. **Wait for review.** The maintainer will:
   - Validate the archive downloads, the hash matches, the project
     loads in a stock Index install at the declared `engine.minVersion`.
   - Re-upload the release assets to this repo (so trust stays here)
     and update the URLs in the PR.
   - Merge.

## Field guidance

| Field | Notes |
|---|---|
| `id` | Lowercase kebab. Stable forever — used in cache paths. |
| `category` | `Template` = starter to fork; `Sample` = self-contained showcase; `Demo` = complete polished game. |
| `tags` | Lowercase, single-word, narrow. Good: `2d`, `arcade`, `tutorial`. Bad: `Game`, `MyAwesomeProject`. |
| `engine.minVersion` | Lowest Index version known to work. Test before submitting. |
| `requiredPackages` | Match the names in your project's `index-project.json` `packages` array. Users missing these see a red pill in the detail modal. |
| `license` | SPDX expression (`MIT`, `Apache-2.0`, `MIT OR Apache-2.0`, etc.). |

## Code execution disclosure

Downloaded projects compile and run C# (and possibly native C++)
when the user clicks Open in the launcher. The launcher shows a
one-time "community content" disclosure modal before the first
download from this library; submissions don't bypass that.
