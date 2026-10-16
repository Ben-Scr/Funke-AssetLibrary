# Funke Asset Library

This repository is the catalog for the Funke engine's in-launcher Asset
Library. It holds the **metadata** for every entry; the actual project
archives live on whatever GitHub repo the project author chose to host
them on. Anyone running Funke sees these entries when they open the
**Asset Library** tab in the launcher.

## Repo layout

- `index.json` — the manifest the launcher fetches. Schema documented below.
- `CONTRIBUTING.md` — submission flow for adding a project.
- `scripts/PublishProject.py` — helper that packs a project, computes the
  SHA-256, and emits a ready-to-paste entry.
- No release assets live here (typically). Authors host their archives
  on their own GitHub repos as Releases; `index.json` entries point at
  those release-asset URLs.

## `index.json` schema (v1)

```jsonc
{
  "schemaVersion": 1,                     // bump only for incompatible changes
  "generatedAt": "2026-05-23T00:00:00Z",  // ISO-8601, advisory
  "entries": [
    {
      "id": "pong",                       // stable, lowercase-kebab, unique
      "name": "Pong Starter",
      "author": "@your-github-handle",
      "shortDescription": "...",          // <=120 chars, shown on cards
      "description": "...",               // markdown allowed, shown in detail
      "tags": ["2d", "starter"],
      "category": "Template",             // Template | Sample | Demo
      "version": "1.0.0",
      "license": "MIT",                   // SPDX expression
      "thumbnail": "https://...png",      // single small PNG, release asset
      "screenshots": [                    // optional, currently shown in detail
        "https://...screenshot-1.png"
      ],
      "archive": {
        // Typical: the project's own repo. Could also point at this
        // repo's releases for authors without a dedicated project repo.
        "url": "https://github.com/your-handle/your-project/releases/download/v1.0.0/your-project-1.0.0.zip",
        "sha256": "<lowercase hex>",      // hard-pinned; verified on download
        "sizeBytes": 524288,
        "rootInZip": ""                   // empty = files at root, or "pong/" if wrapped
      },
      "engine": {
        "minVersion": "2026.1.0",         // inclusive
        "maxVersion": null                // optional
      },
      "requiredPackages": [],             // matches project.json `packages`
      "homepage": "https://...",          // optional
      "sourceUrl": "https://..."          // optional, link to source
    }
  ]
}
```

### `archive.url` can point anywhere on GitHub

The launcher accepts any URL on `github.com`, `objects.githubusercontent.com`,
`raw.githubusercontent.com`, or `codeload.github.com` — including release
assets on a contributor's own repo, not just this one. See
`CONTRIBUTING.md` for the recommended "host on your own project repo" flow.

### Schema versioning

- Adding optional fields is **not** a schema bump.
- Removing or repurposing a field **is** a bump.
- Older launchers seeing a higher `schemaVersion` refuse to render the
  list (showing "update Funke to view this library") rather than crash.

### Trust model

The SHA-256 in this `index.json` is the trust root. A reviewed PR fixes
the hash; if someone later swaps the release asset, the launcher's
verify step aborts the download with a "verification failed" error.

The launcher only accepts archive URLs on:
- `https://github.com/...`
- `https://objects.githubusercontent.com/...`
- `https://raw.githubusercontent.com/...`
- `https://codeload.github.com/...`

Entries pointing elsewhere are rejected client-side.

## Contributing

See `CONTRIBUTING.md`.
