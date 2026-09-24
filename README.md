---
this_file: README.md
---

# GetGo Fonts for FontLab

The GetGo Fonts for FontLab is a collection of font files, which are suitable for starting your own font project in [FontLab](https://www.fontlab.com/font-editor/fontlab/).

The fonts are licensed under CC-0 (public domain), Apache or OFL, and are available for download in the FontLab VFJ format. They support a variety of writing systems and design styles, and the collection is growing!

### Visit the [project website](https://fontlabcom.github.io/getgo-fonts/).


## Build the website

Run `./build.sh` with uv installed. ProperDocs and MaterialX build the Markdown
in `src_docs/md/` into `docs/`, which GitHub Pages publishes. The shared theme
loads from `https://i.fontlab.com/fltheme26/1.0.0/`. Edit source files, then
rebuild; generated HTML in `docs/` is not the authoring source.

The migration preserves public page paths and downloadable assets. The
`fontlab-www-docstheme` sibling repository records source and output asset
hashes and browser verification.

<!-- shared-theme-integration:start -->
## Shared FontLab theme integration

This repository is part of the FontLab theme 2026 rollout: getgo font catalogue.
[THEME.md](THEME.md) documents its source/output boundaries, configuration,
publication route, control ownership, shared visual changes and verification.
Use the [public setup guide](https://i.fontlab.com/fltheme26/) and
[MaterialX starter](https://i.fontlab.com/fltheme26/starter.zip) for new sites.
<!-- shared-theme-integration:end -->
