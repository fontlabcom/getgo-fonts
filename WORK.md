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
- rafi-italic-var Variable PS: FontLab defect, direction correction applied in one master only (fontlab/fl#8507).
- mark/mkmk coverage (two causes, measured): the shipped variable TTFs were exported with a temporary FontLab profile that creates mark/mkmk (owner-approved; preferences restored, content proven equal). (1) rafi: composites without anchors of their own (Aacute = A + acutecomb.case, …) take no marks in any FontLab export; the 2021 binaries used the components' anchors. rafi-var VF bases 523 (static 562), 282 of the 371 2021 bases not covered. (2) scig: the variable export drops composite glyphs as mark bases even when they have their own anchors in every master (599 of 603; static export keeps them): VF bases 131 vs static 769 vs 2021 770. FontLab defect, reported as fontlab/fl#8511. Accepted for this release (owner decision D15); no anchors added, no post-processing.
- fonts.json, getgo-fonts-for-fontlab.zip and docs/: regenerated in the release step (tools/build_getgo.py, then ./build.sh).
- Owner notes: medi/vize overlapping zones; boto-var CondThin stem items; scig names follow the VFJ's default-master ffn/psn (no "Regular").
