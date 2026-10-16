---
this_file: DEPENDENCIES.md
---

# Website dependencies

uv.lock pins ProperDocs 1.6.7, MaterialX 10.1.5 and Python Markdown extensions.
ProperDocs builds the pages; MaterialX supplies navigation, search and palettes.
pymdown-extensions supplies fenced code support. Shared Basecoat, prefixed
daisyUI and browser theme assets come from the versioned FontLab CDN.

`tools/requirements.txt` supplies the catalogue generator's separate venv:
fontTools reads font metadata and creates WOFF2, vharfbuzz shapes specimen text,
CairoSVG and Pillow render/crop PNGs, yaplon preserves YAML/JSON formatting,
and sh invokes the optional Rust usvg optimizer. Tests use Python's unittest.
Content hashing and ZIP handling use the standard library; no dependencies
were added for incremental builds.
