<!-- this_file: AGENTS.md -->

# getgo-fonts: agent guidance

<!-- shared-theme-integration:start -->
## Shared theme maintenance

Read [THEME.md](THEME.md) before changing the catalogue theme. Configure
fly-january in `src_docs/mkdocs.yml`. Keep the FontLab chrome, the bare `search`
plugin and local menu/search ownership. Shared theme behavior belongs in
`fontlab-www-docstheme`. Keep specimen styles in `src_docs/md/css/`.
Run `./build.sh --strict` and verify the generated `docs/` pages and assets.
Do not commit unrelated local edits or hand-edit generated CSS as the source fix.
Work directly unless the current user explicitly requests delegation.
<!-- shared-theme-integration:end -->
