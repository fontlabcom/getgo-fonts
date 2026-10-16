---
this_file: WORK.md
---

# Work

## 2026-10-16: incremental catalogue generator

Fixed `tools/build_getgo.py` against the committed ProperDocs layout. The
generator adds `this_file` headers to generated pages/index/CSS, uses
`illustrations/` in Markdown and published `docs/images/` URLs in fonts.json,
and preserves authored script order (including Pixa). Incremental builds
preserve unchanged output bytes and mtimes.

SHA-256 input hashes live in ignored `.cache/getgo-build.json`. A cold Git
checkout compares source bytes with committed blob hashes. Font/sample-text changes
invalidate specimens; font changes invalidate WOFF2; article/illustration
changes invalidate their pages. Archive input hashes also cover VFJs, licences
and other files under getgo-fonts/. Source mtime changes alone do nothing.
Missing outputs are rebuilt; new ZIPs use sorted entries, fixed timestamps and
0644 member permissions.
`--root` allows verification in a separate copy without changing its script.

Review of the release normalization found two historical details worth preserving:
newer Unicode data changes Pixa/Ptit character maps, and the released ZIP has
a different Pixa YAML script order from the source tree. Existing pages and
ZIPs are retained until their inputs change. A generator fingerprint (script
hash, version and dependency versions) refreshes pages and CSS on a cache
mismatch; a fresh checkout preserves the committed pages. `--force` refreshes
all derived outputs, including specimens and ZIPs.
The generator still refreshes the aggregate catalogue, comparing bytes before
writing. No font sources, specimens or published docs were changed here.

Verification (all final exit codes 0):

- `python -m unittest discover -s tools/tests -v`: 19 tests passed, covering
  a two-font fixture built twice, bytes and mtimes, headers, paths/URLs, script
  order, equal-mtime font edits, article/sample/VFJ edits, missing outputs,
  cold-cache hashes, archive deletions and optional usvg rendering. Additional
  cases check SVG viewports/Y-flips, PNG ink distribution against the committed
  specimen, generator/version/dependency invalidation, the force CLI, 0644 ZIP
  members, corrupt caches, description-only edits and generated sample text.
- `ruff check tools/build_getgo.py tools/tests/test_build_getgo.py`: passed.
- `git diff --check`: passed.
- Fresh import with usvg absent from PATH: passed.

The tools venv was installed from `tools/requirements.txt` using uv. On this
Apple Silicon host, Cairo used `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.
The no-diff proof used a local clone of main's tree at
`1631970060cd6afbcd2a8acf2f2b42531e21ddbb` (99 fonts):

```sh
proof=$(mktemp -d)
git clone --local --no-hardlinks --quiet . "$proof"
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
  tools/.venv/bin/python tools/build_getgo.py --root "$proof"
git -C "$proof" diff --exit-code
git -C "$proof" status --porcelain
```

The build and diff checks were run twice, first without a cache, then with it:
both returned 0, both status outputs were empty. A before/after stat comparison
of all 1,311 tracked files found zero changed mtimes in either run. The edited
generator ran from this checkout, so the proof clone itself had no code edits
to exclude from the diff. No commits were created.

The render review reproduced a vharfbuzz 0.3.1 viewport with a negative origin,
which the previous regex missed. SVG normalization now parses the viewport and
places the Y-flip on a group supported by CairoSVG, retaining glyph definitions
and references. Modern glyph coordinates receive the legacy 500-unit vertical
margins, so text stays within the same specimen area. Both legacy and current
origins are covered. The regenerated Baar viewport is `0 0 23872 3048`;
its 600×56 PNG has ink bounds `(2, 9, 439, 47)`, compared with the committed
specimen's `(2, 9, 438, 47)`. The sample render decision uses the final metadata
text after YAML normalization, so newly added
sample text is rendered immediately and description edits leave specimens alone.

## 2026-09-23: shared theme migration

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

## 2026-10-16: issue 106, VFJ export fixes

Done and verified. Re-exported natively; fontTools checks fvar/avar against each axis graph; outline geometry compared before and after; every fixed VFJ reopened in FontLab with the same glyphs and masters. Evidence and full report: fontlab-scripting/verification/issue-106/evidence/vfj-fixes/ and reports/F1-vfj-export-fixes.md.

Open, blocked outside this repository's scope (no executable task here):
- rafi-italic-var Variable PS: FontLab defect, direction correction applied in one master only (fontlab/fl#8507).
- mark/mkmk coverage (two causes, measured): the shipped variable TTFs were exported with a temporary FontLab profile that creates mark/mkmk (owner-approved; preferences restored, content proven equal). (1) rafi: composites without anchors of their own (Aacute = A + acutecomb.case, …) take no marks in any FontLab export; the 2021 binaries used the components' anchors. rafi-var VF bases 523 (static 562), 282 of the 371 2021 bases not covered. (2) scig: the variable export drops composite glyphs as mark bases even when they have their own anchors in every master (599 of 603; static export keeps them): VF bases 131 vs static 769 vs 2021 770. FontLab defect, reported as fontlab/fl#8511. Accepted for this release (owner decision D15); no anchors added, no post-processing.
- fonts.json, getgo-fonts-for-fontlab.zip and docs/: regenerated in the release step (tools/build_getgo.py, then ./build.sh).
- Owner notes: medi/vize overlapping zones; boto-var CondThin stem items; scig names follow the VFJ's default-master ffn/psn (no "Regular").
