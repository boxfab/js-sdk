// Usage: node scripts/check_release_tag.mjs v0.1.0-alpha.1                            (boxfab)
//        node scripts/check_release_tag.mjs --project desktop desktop-v0.1.0-alpha.1  (@boxfab/desktop)
//        node scripts/check_release_tag.mjs --project code-interpreter code-interpreter-v0.1.0-alpha.1
//                                                              (@boxfab/code-interpreter)
// Exits non-zero unless the tag is exactly "v" + the version in package.json, and that version is
// MAJOR.MINOR.PATCH or MAJOR.MINOR.PATCH-(alpha|beta|rc).N (the pre-release name is the npm
// dist-tag publish.yml uses).
import { readFileSync } from 'node:fs'

const args = process.argv.slice(2)
const project = args[0] === '--project' ? args[1] : ''
const tag = (project ? args[2] : args[0]) ?? ''
const prefix = project ? `${project}-v` : 'v'
const { version } = JSON.parse(readFileSync(new URL(`../${project ? project + '/' : ''}package.json`, import.meta.url), 'utf8'))
const semver = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-(alpha|beta|rc)\.(0|[1-9]\d*))?$/
if (!semver.test(version)) {
  console.error(`package.json version ${version} is not a valid release version`)
  process.exit(1)
}
if (version === '0.0.0') {
  console.error('version 0.0.0 is not releasable')
  process.exit(1)
}
if (tag !== `${prefix}${version}`) {
  console.error(`tag ${tag} does not match package.json version (expected ${prefix}${version})`)
  process.exit(1)
}
console.log(`tag ${tag} OK`)
