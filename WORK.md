---
this_file: WORK.md
---

# Work

GetGo uses fly-january 0.2.1 with FontLab chrome (`93ea24c`). The release
build (`./build.sh --strict`) finished with zero warnings. All 101 generated
HTML routes reference the rebuilt Fly assets. The catalogue test suite passed
all 19 tests in the housekeeping run.

## Pending verification

- Fly 0.2.1 browser check (orchestrator): at phone width, check the tab labels,
  table-of-contents drawer and code-copy gutter.

## Upstream blockers

- rafi-italic-var Variable PS export is blocked by fontlab/fl#8507. After the
  upstream fix, re-export and check direction correction in every master.
- The shipped mark/mkmk coverage was accepted for the release (decision D15).
  Rafi composites lack their own anchors. Scig variable export drops composite
  bases even when they have anchors. After fontlab/fl#8511 is fixed, re-export
  Scig and compare the variable mark bases with the static export.

Historical generator checks and issue 106 measurements are in `bb4443f:WORK.md`
and `47aea80:WORK.md`.
