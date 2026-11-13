// Usage: node scripts/check_package.mjs <path to the npm pack tarball>
// Checks the exact file list, the package metadata, that no file carries local paths, credentials
// or (via the optional DIST_EXTRA_DENY regex) site-specific names, and that the shipped code and
// type declarations default to BoxFab.
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

const tgz = process.argv[2]
const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
const problems = []

const files = execFileSync('tar', ['-tzf', tgz], { encoding: 'utf8' }).trim().split('\n').sort()
const expected = [
  'package/LICENSE',
  'package/README.md',
  'package/dist/index.d.mts',
  'package/dist/index.d.ts',
  'package/dist/index.js',
  'package/dist/index.js.map',
  'package/dist/index.mjs',
  'package/dist/index.mjs.map',
  'package/package.json',
].sort()
if (JSON.stringify(files) !== JSON.stringify(expected)) {
  problems.push(`file list differs:\n  got      ${files.join(' ')}\n  expected ${expected.join(' ')}`)
}

const read = (f) => execFileSync('tar', ['-xzOf', tgz, f], { maxBuffer: 64 << 20 }).toString('utf8')
const meta = JSON.parse(read('package/package.json'))
for (const [k, v] of [['name', 'boxfab'], ['version', pkg.version], ['license', 'MIT'], ['main', 'dist/index.js'], ['module', 'dist/index.mjs'], ['types', 'dist/index.d.ts']]) {
  if (meta[k] !== v) problems.push(`package.json ${k} is ${meta[k]}, expected ${v}`)
}
if (meta.scripts?.postinstall || meta.scripts?.install || meta.scripts?.preinstall) problems.push('package.json has install scripts')

const deny = [
  [/\/home\/(?!user\b|azureuser\b)[a-z_][a-z0-9_-]*\//, 'local home path'], // azureuser: upstream MCP doc example
  [/\/tmp\/claude-\d+/, 'local temp path'],
  [/\be2b_[0-9a-f]{40}\b/, 'API key'],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----/, 'private key'],
]
if (process.env.DIST_EXTRA_DENY) deny.push([new RegExp(process.env.DIST_EXTRA_DENY, 'i'), 'site-specific name'])
for (const f of files) {
  const text = read(f)
  for (const [rx, what] of deny) {
    const m = text.match(rx)
    if (m) problems.push(`${f}: ${what} (${m[0].slice(0, 12)}…)`)
  }
}

// The defaults users get: BoxFab domain and variable names, no E2B dashboard or docs links.
for (const f of ['package/dist/index.js', 'package/dist/index.mjs']) {
  const js = read(f)
  if (!js.includes("getEnvVar(\"BOXFAB_DOMAIN\") || \"boxfab.io\"") && !js.includes("getEnvVar('BOXFAB_DOMAIN') || 'boxfab.io'")) problems.push(`${f}: default domain is not boxfab.io`)
  for (const rx of [/getEnvVar\(["']E2B_/, /e2b\.dev\/(docs|dashboard)/, /e2b-js-sdk\//]) {
    if (rx.test(js)) problems.push(`${f}: matches ${rx}`)
  }
}
for (const f of ['package/dist/index.d.ts', 'package/dist/index.d.mts']) {
  const dts = read(f)
  for (const rx of [/E2B_(API_KEY|DOMAIN|API_URL|SANDBOX_URL|DEBUG)\b/, /e2b\.dev\/docs/, /or `e2b\.app`/]) {
    if (rx.test(dts)) problems.push(`${f}: matches ${rx}`)
  }
}

if (problems.length) {
  console.error('package check failed:\n  ' + problems.join('\n  '))
  process.exit(1)
}
console.log(`${tgz}: ${files.length} files, ${meta.name}@${meta.version}: OK`)
