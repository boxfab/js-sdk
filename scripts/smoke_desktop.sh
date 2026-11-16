#!/usr/bin/env bash
# Install the packed @boxfab/desktop tarball (with the core `boxfab` from npm) into an empty project
# and check what a user gets: both module formats load, the BoxFab names are exported (E2B kept as
# an alias), the defaults point to BoxFab, and inherited E2B_* variables are ignored. Offline.
#   scripts/smoke_desktop.sh desktop/pkg/boxfab-desktop-<version>.tgz
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
  if (typeof m.Sandbox.prototype.screenshot !== "function") throw new Error("desktop Sandbox.screenshot missing")
  if (m.BoxFab !== m.E2B) throw new Error("E2B is not an alias of BoxFab")
  const c = new m.ConnectionConfig()
  // The add-on follows the core installed next to it (its own check is in smoke_installed.sh),
  // so the domain is compared with the core default rather than written down here.
  const coreDomain = new core.ConnectionConfig().domain
  if (c.domain !== coreDomain) throw new Error("domain " + c.domain + " differs from the core default " + coreDomain)
  if (/(^|\.)e2b\.(app|dev)$/.test(c.domain)) throw new Error("E2B domain " + c.domain)
  if (c.apiKey) throw new Error("picked up an API key from E2B_API_KEY")
'
node -e "const m = require('@boxfab/desktop'); const core = require('boxfab'); $check; console.log('cjs ok')"
node --input-type=module -e "import * as m from '@boxfab/desktop'; import * as core from 'boxfab'; $check; console.log('esm ok')"
