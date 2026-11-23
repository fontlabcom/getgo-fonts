---
this_file: DEPENDENCIES.md
---

# Website dependencies

`uv.lock` pins fly-january 0.1.1, ProperDocs 1.6.7, MkDocs 1.6.1,
MaterialX 10.1.8 and pymdown-extensions 11.0.1. ProperDocs builds the pages.
Fly supplies the theme assets and FontLab chrome, MaterialX supplies local
navigation and search, and pymdown-extensions supplies fenced code support.

`tools/requirements.txt` supplies the catalogue generator's separate venv:
fontTools reads font metadata and creates WOFF2, vharfbuzz shapes specimen text,
CairoSVG and Pillow render/crop PNGs, yaplon preserves YAML/JSON formatting,
and sh invokes the optional Rust usvg optimizer. Tests use Python's unittest.
Content hashing and ZIP handling use the standard library; no dependencies
were added for incremental builds.
