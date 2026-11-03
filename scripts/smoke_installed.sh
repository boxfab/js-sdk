#!/usr/bin/env bash
# Install the packed tarball into an empty project and check what a user gets: both module formats
# load, the BoxFab names are exported (E2B kept as an alias), the defaults point to BoxFab, and
# inherited E2B_* variables are ignored. Offline: nothing is sent anywhere.
#   scripts/smoke_installed.sh pkg/boxfab-<version>.tgz
set -euo pipefail
tgz=$(realpath "$1")
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cd "$dir"
npm init -y >/dev/null
npm install --ignore-scripts --no-audit --no-fund "$tgz" >/dev/null
export E2B_API_KEY=e2b_0000000000000000000000000000000000000000 E2B_DOMAIN=e2b.app E2B_API_URL=https://api.e2b.app
unset BOXFAB_API_KEY BOXFAB_DOMAIN
check='
  if (typeof m.Sandbox?.create !== "function") throw new Error("Sandbox.create missing")
  if (m.BoxFab !== m.E2B) throw new Error("E2B is not an alias of BoxFab")
  const c = new m.ConnectionConfig()
  if (c.apiUrl !== "https://api.boxfab.io") throw new Error("apiUrl " + c.apiUrl)
  if (c.domain !== "boxfab.io") throw new Error("domain " + c.domain)
  if (c.apiKey) throw new Error("picked up an API key from E2B_API_KEY")
  if (!c.headers["User-Agent"]?.startsWith("boxfab-js-sdk/")) throw new Error("User-Agent " + c.headers["User-Agent"])
'
node -e "const m = require('boxfab'); $check; console.log('cjs ok')"
node --input-type=module -e "import * as m from 'boxfab'; $check; console.log('esm ok')"
node --input-type=module -e "
  import { Sandbox } from 'boxfab'
  try { await Sandbox.create(); throw new Error('created without a key') }
  catch (e) { if (!/BOXFAB_API_KEY/.test(e.message) || /e2b\.dev/.test(e.message)) throw e; console.log('missing-key message ok') }
"
