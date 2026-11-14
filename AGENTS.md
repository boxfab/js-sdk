# Notes for AI agents and reviewers

## Review guidelines

This repository republishes the open-source E2B JavaScript SDK under the BoxFab name. Most of the
code is copied from upstream by `scripts/sync_upstream.py` (and `scripts/sync_desktop.py`,
`scripts/sync_code_interpreter.py`) and then changed by a fixed set of asserted rewrites (see
`UPSTREAM.md`).

- **Generated paths are out of scope for behaviour review:** `src/`, `tests/`, `CHANGELOG-E2B.md`,
  `desktop/src/`, `desktop/tests/`, `desktop/CHANGELOG-E2B.md`, `desktop/README.md`,
  `desktop/LICENSE`, and the same paths in `code-interpreter/`. Their logic is upstream's; bugs in
  it are not fixed here (known ones are listed in `UPSTREAM.md`). Do not report them.
- **Do review:** the sync scripts and their rules (a rewrite that changes behaviour beyond a rename,
  a rule that can match the wrong text, an audit that can miss an upstream name or variable), the
  repository's own files (`overlay/`, `scripts/`, the build and test configs, `package.json`,
  `desktop/package.json`, `code-interpreter/package.json`), the workflows in `.github/workflows/`
  (release safety, permissions, secrets, triggers, dist-tags) and the hand-written docs.
- Report concrete P1/P2 defects with the triggering input and effect; skip style.
