# Changelog (@boxfab/code-interpreter)

Upstream E2B Code Interpreter SDK changes are in `CHANGELOG-E2B.md`.

## 0.1.0-alpha.2 (2026-11-16)

- Requires `boxfab` 0.1.0-alpha.5 or newer: its default domain is `us-west.boxfab.dev`, BoxFab's
  first region (the previous default `boxfab.io` does not serve the API), and it fixes the `glob`
  and `minimatch` advisories. The README, the doc examples and the `E2B_DOMAIN` instructions use
  `us-west.boxfab.dev`.
- Dashboard links point to `https://dashboard.us-west.boxfab.io`, docs links to `https://boxfab.io/docs`.

## 0.1.0-alpha.1 (2026-11-13)

- First alpha, generated from the E2B Code Interpreter SDK `@e2b/code-interpreter` 2.9.0 (E2B
  monorepo commit `ee355b765ac0`, the commit the core `boxfab` package is generated from).
- Package name `@boxfab/code-interpreter`; client class `BoxFab` (`E2B` kept as an alias).
  Configuration only through `BOXFAB_*` environment variables.
- Default template `code-interpreter-v1`, provided by BoxFab to every team.
