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

## 2026-10-16: issue 106, VFJ export fixes (lane F1)

Done and verified. Re-exported natively; fontTools checks fvar/avar against each axis graph; outline geometry compared before and after; every fixed VFJ reopened in FontLab with the same glyphs and masters. Evidence and full report: fontlab-scripting/verification/issue-106/evidence/vfj-fixes/ and reports/F1-vfj-export-fixes.md.

Open, blocked outside this repository's scope (no executable task here):
- club-var Lcaron: 3 masters have no layer; the rest use caroncomb (16) or commaaccentcomb (6). Needs an owner design decision. Until then club-var's Variable TT/PS fail and club-var.ttf stays the 2021 build.
- rafi-italic-var Variable PS: a FontLab defect, the direction correction applied in only one master (fontlab/fl#8507).
- fonts.json, getgo-fonts-for-fontlab.zip and docs/ still contain the old VFJs. Rebuilding them is the controller's release step; this lane was told not to rebuild the website.
- Owner notes: cosm graph "800":900; the no-op wdth axis in rafi; club-var SELE range.
