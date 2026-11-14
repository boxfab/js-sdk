#!/usr/bin/env python3
"""Regenerate src/, tests/ and the build configs from an upstream E2B JS SDK release.

    python3 scripts/sync_upstream.py                    # clone the pinned tag below
    python3 scripts/sync_upstream.py --src <checkout>   # use an existing E2B monorepo checkout

The output is fully derived: never hand-edit src/ or tests/; change a rule here (or a file in
overlay/) and re-run. Every rule asserts how often it matched, so when upstream moves code around
the sync fails loudly instead of silently shipping an E2B default. See UPSTREAM.md for the why.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from sync_desktop import sync as sync_desktop  # noqa: E402
UPSTREAM_REPO = "https://github.com/e2b-dev/E2B.git"
UPSTREAM_TAG = "e2b@2.61.0"
UPSTREAM_COMMIT = "ee355b765ac0e884fbeaa69e4b44f4c7c58ed6b1"
SDK_SUBDIR = "packages/js-sdk"

DOCS = "https://boxfab.dev/docs"
DASHBOARD = "https://dashboard.boxfab.io"

COPY = ["src", "tests"]
RENAME = {"CHANGELOG.md": "CHANGELOG-E2B.md"}
# Runtime smoke suites for browsers, Cloudflare Workers, Bun and Deno: they need their own
# toolchains and deploy targets and are not run here.
DELETE_DIRS = ["tests/runtimes"]

# Every environment variable the SDK (and its test harness) reads gets a BOXFAB_ name, with no
# fallback to the E2B name. E2B_HEREDOC_* are shell variables inside generated build steps.
ENV_VARS = [
    "API_KEY", "API_URL", "DOMAIN", "SANDBOX_URL", "DEBUG", "HTTP_VERSION",
    "API_CONNECTIONS", "ENVD_RPC_CONNECTIONS", "VOLUME_API_URL", "TEST_MAX_WORKERS",
]
ENV_RX = r"\bE2B_(" + "|".join(ENV_VARS) + r")\b"

# (file, old, new, expected count)
EXACT = [
    ("src/connectionConfig.ts", "return getEnvVar('BOXFAB_DOMAIN') || 'e2b.app'", "return getEnvVar('BOXFAB_DOMAIN') || 'boxfab.io'", 1),
    ("src/volume/client.ts", "return getEnvVar('BOXFAB_DOMAIN') || 'e2b.app'", "return getEnvVar('BOXFAB_DOMAIN') || 'boxfab.io'", 1),
    ("src/connectionConfig.ts", "@default BOXFAB_DOMAIN // environment variable or `e2b.app`", "@default BOXFAB_DOMAIN // environment variable or `boxfab.io`", 1),
    ("src/volume/client.ts", "@default BOXFAB_DOMAIN // environment variable or `e2b.app`", "@default BOXFAB_DOMAIN // environment variable or `boxfab.io`", 1),
    ("src/sandbox/sandboxApi.ts", "@default ${PORT}-sandboxid.e2b.app", "@default ${PORT}-sandboxid.boxfab.io", 1),
    ("src/connectionConfig.ts", "sdkUserAgentPrefix = 'e2b-js-sdk/'", "sdkUserAgentPrefix = 'boxfab-js-sdk/'", 1),
    ("src/api/metadata.ts", "publisher: 'e2b',", "publisher: 'boxfab',", 1),
    (
        "src/api/index.ts",
        "'API key is required, please visit the API Keys tab at https://e2b.dev/dashboard?tab=keys to get your API key. ' +",
        f"'API key is required. Get one from your BoxFab administrator or the dashboard at {DASHBOARD}. ' +",
        1,
    ),
    ("src/sandbox/index.ts", "Check docs [here](https://e2b.dev/docs).", f"Check docs [here]({DOCS}).", 1),
    (
        "src/template/index.ts",
        "'Templates based on other templates can only be built using the E2B API.'",
        "'Templates based on other templates can only be built using the BoxFab API.'",
        1,
    ),
    # Client class: BoxFab, with the upstream names kept as aliases so existing code ports by
    # changing the import.
    ("src/client.ts", "export class E2B {", "export class BoxFab {", 1),
    ("src/client.ts", "import { E2B } from 'e2b'", "import { BoxFab } from 'boxfab'", 1),
    ("src/client.ts", "const client = new E2B({ apiKey: 'e2b_...', domain: 'e2b.dev' })", "const client = new BoxFab({ apiKey: 'e2b_...' })", 1),
    (
        "src/index.ts",
        "export { E2B, type BoxFabClientOpts } from './client'",
        "export {\n  BoxFab,\n  BoxFab as E2B,\n  type BoxFabClientOpts,\n  type BoxFabClientOpts as E2BClientOpts,\n} from './client'",
        1,
    ),
    ("tests/connectionConfig.test.ts", "assert.equal(config.apiUrl, 'https://api.e2b.app')", "assert.equal(config.apiUrl, 'https://api.boxfab.io')", 1),
    # Tests: published-package paths instead of the monorepo's.
    ("tests/bundle/edgeCompat.test.ts", "run \\`pnpm build\\` before testing", "run \\`npm run build\\` before testing", 1),
]

# (glob, pattern, replacement, expected total count or None)
REGEX = [
    ("src/**/*.ts", ENV_RX, r"BOXFAB_\1", 29),
    ("tests/**/*.ts", ENV_RX, r"BOXFAB_\1", None),
    ("src/**/*.ts", r"\bE2BClientOpts\b", "BoxFabClientOpts", None),
    ("src/**/*.ts", r"\{@link E2B(\.\w+)?\}", r"{@link BoxFab\1}", 7),
    # Product name in comments and doc comments (these become the .d.ts docs users read in their
    # editor). Lines with URLs are left alone. Count asserted below as changed lines.
    ("tests/**/*.ts", r"e2b-js-sdk/", "boxfab-js-sdk/", 4),
    # Tests of the default domain follow the new default; tests of E2B's own domains stay.
    ("tests/**/*.ts", r"\|\| 'e2b\.app'", "|| 'boxfab.io'", 3),
]

COMMENT_LINE = re.compile(r"^\s*(\*|//|/\*\*)")
# Comments about E2B's own hosted service, where BoxFab would be wrong.
PROSE_KEEP = [
    "only guaranteed for E2B prod",
    "Available on E2B Cloud and in BYOC",
    "control plane that knows this option: E2B Cloud",
]
PROSE_LINES = 31

# What may remain in src/ after the rewrites; anything else matching FORBIDDEN fails the sync.
# The known-domains list in connectionConfig.ts (E2B's hosted domains, which get a different URL
# scheme) is allowed explicitly.
FORBIDDEN = re.compile(r"e2b\.dev/|'e2b\.app'(?!,)|\bE2B_(" + "|".join(ENV_VARS) + r")\b|e2b-js-sdk")


def sh(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, help="existing E2B monorepo checkout at the pinned commit")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        src = a.src
        if src is None:
            src = Path(tmp) / "E2B"
            sh("git", "clone", "-q", "--filter=blob:none", "--no-checkout", UPSTREAM_REPO, str(src))
            sh("git", "checkout", "-q", UPSTREAM_COMMIT, cwd=src)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=src, capture_output=True, text=True).stdout.strip()
        if head != UPSTREAM_COMMIT:
            sys.exit(f"{src} is at {head}, expected {UPSTREAM_COMMIT} ({UPSTREAM_TAG})")
        sdk = src / SDK_SUBDIR
        for name in COPY:
            dst = ROOT / name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(sdk / name, dst)
        for old, new in RENAME.items():
            shutil.copy2(sdk / old, ROOT / new)
        # LICENSE is MIT with upstream's copyright line and ours; it must keep upstream's
        # copyright line and permission text word for word.
        up_lic = (sdk / "LICENSE").read_text()
        ours = (ROOT / "LICENSE").read_text()
        up_copyright = [line for line in up_lic.splitlines() if line.startswith("Copyright")]
        if not up_copyright or any(line not in ours.splitlines() for line in up_copyright):
            sys.exit(f"LICENSE lacks upstream's copyright line(s): {up_copyright}")
        if not ours.endswith(up_lic[up_lic.index("Permission is hereby granted"):]):
            sys.exit("LICENSE permission text differs from upstream's")
        sync_desktop(src)  # desktop/ from the same checkout (scripts/sync_desktop.py)

    for rel in DELETE_DIRS:
        p = ROOT / rel
        assert p.is_dir(), f"DELETE_DIRS: {rel} not found upstream"
        shutil.rmtree(p)

    overlay = ROOT / "overlay"
    for f in sorted(overlay.rglob("*")):
        if f.is_file():
            dst = ROOT / f.relative_to(overlay)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)

    # Regex rules first (EXACT rules are written against the renamed variables).
    for pattern, rx, repl, count in REGEX:
        total = 0
        for p in sorted(ROOT.glob(pattern)):
            if "overlay" in p.parts or not p.is_file():
                continue
            text = p.read_text()
            new_text, n = re.subn(rx, repl, text)
            if n:
                p.write_text(new_text)
                total += n
        if count is not None:
            assert total == count, f"REGEX {pattern} {rx!r}: {total} matches, expected {count}"
        print(f"  {total:3d}x {rx}  ({pattern})")

    for rel, old, new, count in EXACT:
        p = ROOT / rel
        text = p.read_text()
        n = text.count(old)
        assert n == count, f"EXACT {rel}: {old[:70]!r} found {n}x, expected {count}"
        p.write_text(text.replace(old, new))

    prose = 0
    for p in sorted((ROOT / "src").rglob("*.ts")):
        if p.name.endswith((".gen.ts", "_pb.ts", ".d.ts")):
            continue
        lines = p.read_text().split("\n")
        changed = False
        for i, line in enumerate(lines):
            if (
                COMMENT_LINE.match(line)
                and "http" not in line
                and not any(k in line for k in PROSE_KEEP)
                and re.search(r"\bE2B\b", line)
            ):
                line = re.sub(r"\bE2B's\b", "BoxFab's", re.sub(r"\bE2B\b(?!')", "BoxFab", line))
                lines[i] = line
                prose += 1
                changed = True
            fixed = re.sub(r"\b([Aa])n (`BoxFab`|\{@link BoxFab\})", r"\1 \2", lines[i])
            if fixed != lines[i]:
                lines[i] = fixed
                changed = True
        if changed:
            p.write_text("\n".join(lines))
    assert prose == PROSE_LINES, f"prose: {prose} comment lines changed, expected {PROSE_LINES}"
    print(f"  {prose:3d} comment lines E2B -> BoxFab")

    leftovers = []
    for p in sorted((ROOT / "src").rglob("*.ts")):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if FORBIDDEN.search(line):
                leftovers.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    if leftovers:
        sys.exit("E2B references left in src/:\n" + "\n".join(leftovers))
    print(f"synced {UPSTREAM_TAG} ({UPSTREAM_COMMIT[:12]})")


if __name__ == "__main__":
    main()
