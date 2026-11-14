#!/usr/bin/env bash
# Install the packed @boxfab/code-interpreter tarball (with the core `boxfab` from npm) into an empty
# project and check what a user gets: both module formats load, the BoxFab names are exported (E2B
# kept as an alias), the defaults point to BoxFab, and inherited E2B_* variables are ignored. Offline.
#   scripts/smoke_code_interpreter.sh code-interpreter/pkg/boxfab-code-interpreter-<version>.tgz
set -euo pipefail
tgz=$(realpath "$1")
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cd "$dir"
npm init -y >/dev/null
npm install --ignore-scripts --no-audit --no-fund "$tgz" >/dev/null
export E2B_API_KEY=e2b_0000000000000000000000000000000000000000 E2B_DOMAIN=e2b.app
unset BOXFAB_API_KEY BOXFAB_DOMAIN
check='
  if (typeof m.Sandbox?.create !== "function") throw new Error("Sandbox.create missing")
  if (typeof m.Sandbox.prototype.runCode !== "function") throw new Error("Sandbox.runCode missing")
  if (m.BoxFab !== m.E2B) throw new Error("E2B is not an alias of BoxFab")
  const c = new m.ConnectionConfig()
  if (c.domain !== "boxfab.io") throw new Error("domain " + c.domain)
  if (c.apiKey) throw new Error("picked up an API key from E2B_API_KEY")
'
node -e "const m = require('@boxfab/code-interpreter'); $check; console.log('cjs ok')"
node --input-type=module -e "import * as m from '@boxfab/code-interpreter'; $check; console.log('esm ok')"
