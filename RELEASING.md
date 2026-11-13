# Releasing

npm is reached only through `.github/workflows/publish.yml`, which runs when a GitHub Release is
**published** (pre-releases included; saving a draft does nothing). Releases use npm trusted
publishing (OIDC): there is no npm token in the repository or its secrets.

## What protects a release

| Control | Where |
|---|---|
| tag must be `v<version in package.json>`; the tagged commit must be on `main` | `publish.yml` job `verify` + `scripts/check_release_tag.mjs` |
| full CI on the exact tagged commit; the tarball is built and checked there once | `publish.yml` job `ci` (calls `ci.yml`) |
| exact file list, name/version/license/entry points, no install scripts, local paths, API keys, private keys or (optional `DIST_EXTRA_DENY`) site-specific names; shipped code and declarations default to `boxfab.io` and `BOXFAB_*`; an empty project installs it, both module formats load, inherited `E2B_*` variables are ignored | `ci.yml` job `build` + `scripts/check_package.mjs` + `scripts/smoke_installed.sh` |
| that exact tarball is uploaded; only this job has `id-token: write`; provenance is attached | `publish.yml` job `publish` |
| dist-tag from the version: `1.2.3` → `latest`, `-alpha.N` → `alpha`, `-beta.N` → `beta`, `-rc.N` → `rc`; any other pre-release name is rejected | `scripts/check_release_tag.mjs` (job `verify`) and `publish.yml` job `publish` |
| a required reviewer approves each publication; admins cannot bypass it | environment `npm` |
| a published release's tag and assets cannot change | repository setting: immutable releases |
| one publication at a time, never cancelled | `concurrency: npm-publish` |
| actions pinned to commit SHAs | workflow files |

## One-time setup (owner)

1. npmjs.com: `boxfab` is an unscoped package, so it belongs to the account that first publishes
   it, not to the `boxfab` organization; 2FA required for publishing. Add co-maintainers with
   `npm owner add <user> boxfab`.
2. Repository (public; provenance requires a public source repository):
   - environment `npm` (Settings → Environments) with a required reviewer and deployment branches
     limited to `v*` tags. While there is a single maintainer, add yourself and leave
     *Prevent self-review* off, so every publish still waits for an explicit approval; with a
     second maintainer, add them and turn *Prevent self-review* on;
   - rulesets like `boxfab/python-sdk`: `main` only via squash-merged pull requests with the CI
     jobs as required checks (required approvals: 0 while single-maintainer), no force pushes or
     deletion; `v*` tags created by admins only and immutable.
3. npm trusted publisher for `boxfab` (package → Settings → Trusted publishing → GitHub
   Actions): organization `boxfab`, repository `js-sdk`, workflow `publish.yml`, environment `npm`.
   If npmjs.com only offers this for a package that already exists, do the first release by hand
   (below), then add the trusted publisher, and use the workflow from the next release on.
4. Optional: repository secret `DIST_EXTRA_DENY`, a regex of site-specific names the package
   check must reject.

## Release

1. Pull request: bump `version` in `package.json` (and `package-lock.json`: `npm install
   --package-lock-only`), add the `CHANGELOG.md` entry; merge after CI passes.
2. GitHub → Releases → *Draft a new release*: tag `v<version>` (*Create new tag on publish*),
   target `main`, tick *Set as a pre-release* for alpha/beta versions, then **Publish release**.
3. Watch the `Publish to npm` run: `verify` → `ci / …` → `publish`; when `publish` waits,
   *Review deployments* → `npm` → *Approve and deploy*. Then check https://www.npmjs.com/package/boxfab and
   `npm view boxfab dist-tags`.

### First release by hand (only if trusted publishing cannot be set up before the package exists)

0.1.0-alpha.1 was published this way (no provenance); 0.1.0-alpha.2 was the first release through
the workflow. A new trusted publisher shows *Pending validation* on npmjs.com until the workflow
publishes once, which must happen within npm's validation window (two days).

Publish the tarball that CI built, not a local build:

```bash
gh run download <CI run id on the release commit> -R boxfab/js-sdk -n package -D pkg
node scripts/check_package.mjs pkg/*.tgz
npm login                       # an account in the boxfab org, with 2FA
npm publish ./pkg/*.tgz --access public --tag alpha --provenance=false
```

`package.json` asks for provenance, which only CI can produce, hence `--provenance=false` for
this one manual release. npm also sets `latest` on a package's first publish; later pre-releases
move only their own dist-tag.
