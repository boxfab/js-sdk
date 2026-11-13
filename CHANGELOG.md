# Changelog

## 0.1.0-alpha.3 (2026-11-13)

- One `LICENSE` file: the MIT text with the upstream copyright line (FOUNDRYLABS, INC.) and
  ContextFab's; `LICENSE-E2B` is merged into it.
- README: "Under the hood" section (Firecracker, the E2B open-source infrastructure and SDK, and how
  to use the E2B SDKs and CLI with BoxFab, with the versions tested); the License section names
  the upstream SDK.
- No code changes from the previous release.

## 0.1.0-alpha.2 (2026-11-03)

- First release published by the GitHub Actions workflow (npm trusted publishing, with
  provenance). No code changes from 0.1.0-alpha.1.

## 0.1.0-alpha.1 (2026-11-03)

First BoxFab release, derived from the E2B JavaScript SDK `e2b` 2.61.0 (see `UPSTREAM.md`).

- Package `boxfab`; client class `BoxFab` (`E2B` kept as an alias, as is `E2BClientOpts`).
- Reads `BOXFAB_*` environment variables only (`BOXFAB_API_KEY`, `BOXFAB_DOMAIN`, ...); default
  domain `boxfab.io`.
- User-Agent `boxfab-js-sdk/<version>`; error messages and doc comments point to BoxFab.
