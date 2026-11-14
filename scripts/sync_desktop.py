"""Regenerate desktop/ (the @boxfab/desktop package) from the pinned E2B monorepo commit.

Called by scripts/sync_upstream.py with the same checkout as the core SDK, so both packages are
always generated from one upstream commit:

    packages/desktop-js/src, tests   -> desktop/src, desktop/tests (without tests/runtimes)
    packages/desktop-js/README.md    -> desktop/README.md (from "### 3. Create Desktop Sandbox")

desktop/package.json and the build and test configs are this repository's own. Generated paths
are never edited by hand. Every rule asserts how often it matched, so when upstream moves code the
sync fails instead of shipping an upstream default.
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "desktop"
HERE = ROOT / "scripts" / "desktop"
DOMAIN = "boxfab.io"
TEMPLATE_URL = "https://github.com/boxfab/desktop/tree/main/template"

ENV_VARS = ["API_KEY", "DOMAIN", "DEBUG", "API_URL", "SANDBOX_URL"]
ENV_RX = re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b")

DELETE = ["tests/runtimes"]  # Cloudflare Workers smoke suite: its own toolchain, not run here

EXACT = [
    ("src/client.ts", "  E2BClientOpts,\n  E2B as CoreE2B,\n", "  BoxFabClientOpts,\n  BoxFab as CoreBoxFab,\n", 1),
    ("src/client.ts", "export type { E2BClientOpts }", "export type { BoxFabClientOpts }", 1),
    ("src/client.ts", " * E2B client with an explicitly bound connection configuration.",
     " * BoxFab client with an explicitly bound connection configuration.", 1),
    ("src/client.ts", " * import { E2B } from '@e2b/desktop'", " * import { BoxFab } from '@boxfab/desktop'", 1),
    ("src/client.ts", " * const client = new E2B({ apiKey: 'e2b_...', domain: 'e2b.dev' })",
     f" * const client = new BoxFab({{ apiKey: 'e2b_...', domain: '{DOMAIN}' }})", 1),
    ("src/client.ts", "export class E2B {", "export class BoxFab {", 1),
    ("src/client.ts", "constructor(opts?: E2BClientOpts)", "constructor(opts?: BoxFabClientOpts)", 1),
    ("src/client.ts", "const boundOpts: E2BClientOpts =", "const boundOpts: BoxFabClientOpts =", 1),
    ("src/client.ts", "const core = new CoreE2B(boundOpts)", "const core = new CoreBoxFab(boundOpts)", 1),
    ("src/index.ts", "export { E2B } from './client'\nexport type { E2BClientOpts } from './client'",
     "export { BoxFab, BoxFab as E2B } from './client'\n"
     "export type { BoxFabClientOpts, BoxFabClientOpts as E2BClientOpts } from './client'", 1),
    # live tests: the template can be overridden (BOXFAB_DESKTOP_TEMPLATE, default `desktop`).
    ("tests/setup.ts", "const template = 'desktop'", "const template = process.env.BOXFAB_DESKTOP_TEMPLATE || 'desktop'", 1),
]

README_RULES = [
    (r"'@e2b/desktop'", "'@boxfab/desktop'", 13),
    (r"create an `E2B` client", "create a `BoxFab` client", 1),
    (r"import \{ E2B \} from", "import { BoxFab } from", 1),
    (r"new E2B\(\{ apiKey: 'e2b_\*\*\*', domain: 'e2b\.dev' \}\)",
     f"new BoxFab({{ apiKey: 'e2b_***', domain: '{DOMAIN}' }})", 1),
    (r"Check out the sandbox template's code \[here\]\(https://github\.com/e2b-dev/desktop/tree/main/template\)\.",
     f"BoxFab's template is in [boxfab/desktop]({TEMPLATE_URL}), generated from "
     "[e2b-dev/desktop](https://github.com/e2b-dev/desktop/tree/main/template).", 1),
]
README_START = "### 3. Create Desktop Sandbox\n"

FORBIDDEN = [
    (re.compile(r"from 'e2b'"), "e2b import"),
    (re.compile(r"@e2b/desktop"), "upstream package name"),
    (re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b"), "E2B_* variable"),
    (re.compile(r"e2b\.dev|e2b\.app"), "E2B domain"),
]


def sync(src: Path):
    """Generate desktop/ from `src`, an E2B monorepo checkout at the pinned commit."""
    up = src / "packages/desktop-js"
    if not (up / "src").is_dir():
        sys.exit(f"{up}/src not found")
    for d in ("src", "tests"):
        shutil.rmtree(OUT / d, ignore_errors=True)
        shutil.copytree(up / d, OUT / d)
    shutil.copy2(up / "CHANGELOG.md", OUT / "CHANGELOG-E2B.md")
    for rel in DELETE:
        p = OUT / rel
        if not p.is_dir():
            sys.exit(f"desktop DELETE: {rel} not found upstream")
        shutil.rmtree(p)
    shutil.copy2(HERE / "boxfab-env.setup.ts", OUT / "tests/boxfab-env.setup.ts")
    # MIT like the core; the package ships the repository's LICENSE, which must carry the desktop
    # package's upstream copyright line and permission text.
    up_lic = (up / "LICENSE").read_text()
    ours = (ROOT / "LICENSE").read_text()
    for line in (ln for ln in up_lic.splitlines() if ln.startswith("Copyright")):
        if line not in ours.splitlines():
            sys.exit(f"LICENSE lacks the desktop package's upstream copyright line: {line}")
    if not ours.rstrip().endswith(up_lic[up_lic.index("Permission is hereby granted"):].rstrip()):
        sys.exit("LICENSE permission text differs from the desktop package's")
    shutil.copy2(ROOT / "LICENSE", OUT / "LICENSE")

    counts = {"imports": 0, "env": 0, "links": 0}
    for p in sorted([*OUT.joinpath("src").rglob("*.ts"), *OUT.joinpath("tests").rglob("*.ts")]):
        if p.name == "boxfab-env.setup.ts":
            continue
        text = p.read_text()
        new, n1 = re.subn(r"from 'e2b'", "from 'boxfab'", text)
        new, n2 = ENV_RX.subn(r"BOXFAB_\1", new)
        new, n3 = re.subn(r"\{@link E2B(\.\w+)?\}", r"{@link BoxFab\1}", new)
        counts["imports"] += n1
        counts["env"] += n2
        counts["links"] += n3
        if new != text:
            p.write_text(new)
    expect = {"imports": 4, "env": 6, "links": 4}
    if counts != expect:
        sys.exit(f"desktop renames: {counts}, expected {expect}")
    for rel, old, new, expected in EXACT:
        p = OUT / rel
        text = p.read_text()
        if text.count(old) != expected:
            sys.exit(f"desktop/{rel}: expected {expected} x {old[:70]!r}, found {text.count(old)}")
        p.write_text(text.replace(old, new))
    if (OUT / "src/index.ts").read_text().count("export * from 'boxfab'") != 1:
        sys.exit("desktop/src/index.ts: core re-export changed upstream")

    text = (up / "README.md").read_text()
    if text.count(README_START) != 1:
        sys.exit("desktop-js/README.md: section 3 heading changed upstream")
    body = text[text.index(README_START):]
    for rx, repl, count in README_RULES:
        body, n = re.subn(rx, repl, body)
        if n != count:
            sys.exit(f"desktop README {rx!r}: {n} matches, expected {count}")
    left = [ln for ln in body.splitlines() if re.search(r"@e2b/desktop|e2b\.dev|E2B_", ln)]
    if left:
        sys.exit(f"desktop README: upstream references left: {left}")
    header = (HERE / "README-header.md").read_text()
    footer = (HERE / "README-footer.md").read_text()
    (OUT / "README.md").write_text(header + body.rstrip("\n") + "\n" + footer)

    problems = []
    for p in OUT.joinpath("src").rglob("*.ts"):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            for rx, what in FORBIDDEN:
                if rx.search(line):
                    problems.append(f"{p.relative_to(ROOT)}:{i}: {what}: {line.strip()}")
    if problems:
        sys.exit("desktop audit failed:\n  " + "\n  ".join(problems))
    print(f"  desktop: {counts}")
