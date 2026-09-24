---
this_file: THEME.md
---

# Shared theme integration: getgo-fonts

## GetGo font catalogue

The catalogue uses ProperDocs/MaterialX under `src_docs/md/` and retains its font/download generation. Shared components do not change font licences or payloads.

Documentation-first pages use **local MaterialX navigation and local search** when present. Archives, internal configs and source mirrors are not separate live sites.

## Configuration and destinations

| Configuration | Role | Destination |
|---|---|---|
| `src_docs/mkdocs.yml` | active publication configuration | https://fontlabcom.github.io/getgo-fonts/ |

## Build and publish responsibility

Run `./build.sh`; publish generated `docs/` through the existing GitHub Pages route. Verify downloadable font assets remain present when rebuilding catalogue pages.

## Shared runtime contract

The browser layer is published at `https://i.fontlab.com/fltheme26/1.0.0/`.
Load CSS in this order: `components.css`, then `theme.css`. Load scripts in this
order: `basecoat.js`, then `theme.js`. Do not duplicate bundles or edit generated
CDN CSS locally. The four assets are shared across consumers; compatible fixes
are currently published in place under `1.0.0/`, not as immutable snapshots.

Keep `theme.name: materialx`, native navigation/search markup, the search plugin,
and generated `search/search_index.json`. The shared bridge defaults documentation
pages to MaterialX menu/search when those targets exist. In the global bar, one
loupe sits left of one hamburger. The local drawer opens on the right with the
palette at the bottom. Below 76.25em, branding scrolls away and compact controls
dock when either control serves the local site. Escape closes local panels and
returns focus. Plain static/Webflow pages without MaterialX targets keep global
controls.

Choose ownership independently with `mobile-menu="materialx|global"` and
`mobile-search="materialx|global"` on `<fontlab-menu>` or `<vexy-menu>`. These
strings describe the allowed alternatives: use one value, not the literal pipe.
The corresponding config properties are `mobileMenu` and `mobileSearch`; explicit
attributes win. Search ownership applies at desktop widths too. Local search uses
the documentation index; global search uses the brand search service.

Reading shortcuts are Right / Alt+Right → next navigation page, Alt+Left → previous
navigation page, and Left → browser history back. Generated head rel links take
priority over primary-nav order. There is no wraparound. Editable fields, widgets,
open dialogs, selected text and other modifiers retain their normal behavior.

## Components and visual changes

Wrap Basecoat and daisyUI markup in a separate `.fltheme-components` container.
Basecoat keeps its classes; prefix every daisyUI component class with `du-`.
MaterialX keeps `md-` classes. Enable `attr_list` and `md_in_html` when using Markdown
attributes and `markdown="1"` inside HTML containers. The host retains its fonts
and theme picker; wrappers may opt into `data-fltheme-mode="light"` or `"dark"`.
Call `FLTheme.refresh()` after manual DOM replacement; native instant navigation
is already handled. Do not load another Basecoat runtime.

The September 2026 shared changes cover:

- One global/local hamburger and one search control, right-side local navigation,
  responsive docking, desktop local search and safe focus restoration.
- Navigation/history arrow keys with guards for interactive controls.
- Consistent form labels, fields, checkboxes, radios, switches, selects and sliders.
- Shared keycaps, tabs, tooltips, captions, alerts, pagination, drawers, skeletons,
  progress indicators, mockup frames, chart refresh, countdowns and filter reset.
- Standard MaterialX/Basecoat/daisyUI buttons: 2.5rem height, 1rem horizontal
  padding, .875rem text, weight 600 and 1.25rem line height. Explicit size/shape
  variants remain available.
- `article.md-typeset > p:last-of-type { padding-bottom: 25vh !important; }`.
  The old `.md-main .md-content` padding rule was removed.
- Vexy mobile search uses panel background/text colours, so a transparent global
  header does not make an explicitly opaque search panel transparent.

The optional Marketing/styleguide editorial layer is distinct from the scoped
component bundle. Do not add its legacy vendor CSS to an otherwise native site
without also adopting and testing its companion template and theme controls.

## Verification and future changes

For a shared CSS/runtime fix, change `fontlab-www-docstheme`, build it, run its
relevant tests, stage the CDN, push, wait for Pages, and verify live asset hashes.
For a site-specific config/template change, use this repository’s native build and
publish route, then inspect its final output. Cached Webflow/static overlays can
replace intermediate HTML, so checking a MkDocs build alone is insufficient.

Check desktop and mobile, light and dark, local/global ownership, drawer/search
open-close-focus behavior, key navigation and at least one component interaction.
Shared assets must load once. Keep unrelated working-tree edits, content, branding,
URLs, downloadable payloads and deployment credentials untouched.

## References

- [Complete setup and integration guide](https://i.fontlab.com/fltheme26/)
- [Downloadable tested MaterialX starter](https://i.fontlab.com/fltheme26/starter.zip)
- [Component catalogue with HTML and Markdown](https://fontlab.dev/Marketing/fl1992mk/start/)
- [Shared source and change history](https://github.com/Fontlab/fontlab-www-docstheme)
- [Consumer inventory](https://github.com/Fontlab/fontlab-www-docstheme/blob/main/consumers.json)
- [Issue 213 component corrections](https://github.com/Fontlab/fontlab-www-docstheme/blob/main/review/issue213.md)
