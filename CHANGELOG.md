---
this_file: CHANGELOG.md
---

# Changelog

## Release

First tagged release. Includes the issue 106 VFJ export fixes (cosm, rafi, scig, club, stroke-chan), FontLab-generated mark/mkmk in rafi and scig, and the regenerated catalogue, ZIP and website.

## 2026-10-16: release build (issue 106)

Merged issue-106-vfj-export-fixes and rebuilt the site with tools/build_getgo.py and ./build.sh. fonts.json, getgo-fonts-for-fontlab.zip (99 VFJ + 99 TTF, hashes equal the tree) and docs/ are regenerated. The seven regenerated TTFs have fresh WOFF2 files and specimen images; other fonts' images, specimens and Markdown are unchanged. The family name of scig-var is now "GG Scig OFL" (it follows the VFJ default master). rafi-var and rafi-italic-var list Cyrillic in their script summary.

## 2026-10-16: VFJ export fixes (issue 106, branch issue-106-vfj-export-fixes)

All 99 VFJs were exported natively in FontLab 9.0.9780 (static TTF and OTF, plus Variable TT and Variable PS where a font has axes). 7 failed.

- cosm-var, cosm-italic-var: axisGraph keys are now written as decimals. FontLab's VFJ reader dropped integer keys such as "100" and "500" (fontlab/fl#8506). Variable exports now pass, and cosm-var.ttf and cosm-italic-var.ttf are regenerated.
- stroke-chan: removed the Alegreya Sans feature code, which could not compile against this glyph set, and the single-master weight axis. Static exports pass, and stroke-chan.ttf is regenerated.
- scig-var: the conditional-substitution tags now name their base glyphs (q.sc, uni051B.sc); axis keys are decimals; dollar.alt2's contours in master "Lt Cnd Ctr S" are re-wound. All exports pass, and scig-var.ttf is regenerated.
- rafi-var, rafi-italic-var: axis keys are decimals; the italic weight graph is now monotonic; components scaled differently per master are flattened (geometry unchanged). rafi-var passes every format, and rafi-italic-var all but Variable PS. Both TTFs are regenerated.
- club-var: restored the missing Y in Yacute/Ygrave (3 masters) and made AE master-compatible.
- scig-var, rafi-var, rafi-italic-var: mark/mkmk restored in the shipped variable TTFs (FontLab-generated, variable anchors). Fewer glyphs take marks than in the 2021 binaries: composites without anchors of their own (rafi), and in the variable fonts composites in general (scig, FontLab defect fontlab/fl#8511); see WORK.md.
- club-var: removed a stray second tail element ("Q1", left of the bowl) from Q in the BlackItalicModern, ItalicModern, ItalicOptical and BlackItalic masters; every other master uses only the tail component.
- club-var: Lcaron rebuilt as Ľ in all masters, L_l completed, Ldot/franc flattened, SELE widened to -20..10 (italic masters enabled), XOPQ kept on the 2021 user scale 100-900; all formats export. cosm: Heavy axis point and named instances at 100-900. rafi: width axis removed, italic weight scale matches upright, licence names restored.


## 2026-09-23

- Migrated the website from Jekyll to ProperDocs and MaterialX.
- Preserved Markdown content, page routes, downloadable files and specimen assets.
- Added shared FontLab chrome, light/dark mode, search and scoped Basecoat/daisyUI.
- Added uv build dependencies and a reproducible `./build.sh` entry point.
