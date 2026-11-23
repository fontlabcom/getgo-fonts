---
this_file: THEME.md
---

# GetGo Fonts catalogue theme

ProperDocs builds the catalogue with the published fly-january 0.1.1 theme.
The active configuration is `src_docs/mkdocs.yml`. The `fly` plugin supplies
the theme assets and maps the bare `search` plugin to MaterialX search.

## Chrome and typography

`extra.fly.chrome: fontlab` supplies the FontLab menu and footer. The sticky
menu displays “GetGo Fonts” and links to the catalogue home. Menu and search
use Fly’s MaterialX ownership defaults. The MaterialX palette provides the
light/dark switch. Fly sets the cherry accent and Outfit body text.

Edit specimen layout in `src_docs/md/css/site.css`. The catalogue generator
writes the individual specimen font faces to `src_docs/md/css/fonts.css`.
Fly rescales shipped MaterialX styles for its 14.4px root. Account for that
root when changing catalogue-specific rem lengths.

## Build and check

Run `./build.sh --strict` to rebuild the tracked GitHub Pages site in `docs/`.
Check the home page and a font page for the Fly stylesheet and scripts under
`assets/fly/`, one FontLab menu and footer, and the local search field.
Check the search index, editable specimen and VFJ download links.

Package documentation and supported options are in the
[fly-january 0.1.1 release](https://pypi.org/project/fly-january/0.1.1/).
