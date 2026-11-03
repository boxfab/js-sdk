# Changelog

## 0.1.0-alpha.1 (unreleased)

First BoxFab release, derived from the E2B JavaScript SDK `e2b` 2.61.0 (see `UPSTREAM.md`).

- Package `boxfab`; client class `BoxFab` (`E2B` kept as an alias, as is `E2BClientOpts`).
- Reads `BOXFAB_*` environment variables only (`BOXFAB_API_KEY`, `BOXFAB_DOMAIN`, ...); default
  domain `boxfab.io`.
- User-Agent `boxfab-js-sdk/<version>`; error messages and doc comments point to BoxFab.
