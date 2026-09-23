---
this_file: WORK.md
---

# Work

## 2026-09-23: task422

Migrating Jekyll sources to ProperDocs + MaterialX and the shared fltheme26
assets. Original Markdown and public assets copied to src_docs/md before any
build replaces docs/. URLs and downloads must be verified before deployment.
Git objects recovered with git fetch --refetch; no working content discarded.

## Verification

ProperDocs build succeeded on 2026-09-23. SHA-256 comparison verified all 321
original font/image assets in both src_docs/md and built docs. Chromium checked
desktop/mobile rendering, no horizontal overflow, images and download targets.
GetGo's editable GG Pixa specimen and search passed. Extend's TypeRig screenshot
carousel passed. build.sh writes docs/.nojekyll after a successful build.
Deployment/live verification is tracked by fontlab-www-docstheme/consumers.json.
