# Index Asset Library

This repository is the source-of-truth manifest for the Index engine's
in-launcher Asset Library. Anyone running Index sees the entries listed
here when they open the **Asset Library** tab.

## Repo layout

- `index.json` — the manifest the launcher fetches. Schema documented below.
- `CONTRIBUTING.md` — submission flow for adding a project.
- GitHub Releases — each downloadable project lives as a release asset
  (one zip per release). The release tag follows `<entry-id>-<version>`,
  e.g. `pong-1.0.0`.

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
        "url": "https://github.com/Ben-Scr/Index-AssetLibrary/releases/download/pong-1.0.0/pong.zip",
        "sha256": "<lowercase hex>",      // hard-pinned; verified on download
        "sizeBytes": 524288,
        "rootInZip": ""                   // empty = files at root, or "pong/" if wrapped
      },
      "engine": {
        "minVersion": "2026.1.0",         // inclusive
        "maxVersion": null                // optional
      },
      "requiredPackages": [],             // matches index-project.json `packages`
      "homepage": "https://...",          // optional
      "sourceUrl": "https://..."          // optional, link to source
    }
  ]
}
```

### Schema versioning

- Adding optional fields is **not** a schema bump.
- Removing or repurposing a field **is** a bump.
- Older launchers seeing a higher `schemaVersion` refuse to render the
  list (showing "update Index to view this library") rather than crash.

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
