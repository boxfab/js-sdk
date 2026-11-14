# Changelog (@boxfab/desktop)

Upstream E2B Desktop SDK changes are in `CHANGELOG-E2B.md`.

## 0.1.0-alpha.1 (unreleased)

- First alpha, generated from the E2B Desktop SDK `@e2b/desktop` 2.5.0 (E2B monorepo commit
  `ee355b765ac0`, the commit the core `boxfab` package is generated from).
- Package name `@boxfab/desktop`; client class `BoxFab` (`E2B` kept as an alias). Configuration
  only through `BOXFAB_*` environment variables.
- Live tests take the template from `BOXFAB_DESKTOP_TEMPLATE` (default: the SDK's `desktop`).
