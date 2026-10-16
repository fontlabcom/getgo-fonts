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

To regenerate the font catalogue and downloadable ZIP before building the site:

```sh
uv venv tools/.venv --python 3.12
uv pip install --python tools/.venv/bin/python -r tools/requirements.txt
tools/.venv/bin/python tools/build_getgo.py
tools/.venv/bin/python -m unittest discover -s tools/tests -v
./build.sh
```

Cairo must be available to CairoSVG. On Apple Silicon Homebrew installations,
set `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` if needed. Rust `usvg` is an
optional SVG optimizer; rendering also works without it.

The generator records SHA-256 source hashes in ignored `.cache/getgo-build.json`.
A fresh Git checkout bootstraps from committed input blob hashes, preserving the
released specimens, pages and ZIP while their sources are unchanged. Changed
TTF/OTF files rebuild their WOFF2 and specimens; `sample_text` edits refresh specimens,
article/illustration edits refresh pages, and archived source edits refresh the
ZIP. Missing outputs are recreated. Incremental builds preserve unchanged
output bytes and mtimes.
Use `--root /path/to/copy` to build a separate repository copy. `./build.sh`
then compiles the catalogue sources into the published `docs/` site.

The cache includes the generator's code hash, version and dependency versions.
A fingerprint mismatch refreshes pages and CSS; invalid cache JSON falls back
to a cold build. To refresh all derived outputs, including specimens and the
ZIP, run `tools/.venv/bin/python tools/build_getgo.py --force`. Authored sample
text and descriptions are preserved. New archives extract files with mode 0644.

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
