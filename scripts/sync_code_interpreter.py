"""Regenerate code-interpreter/ (the @boxfab/code-interpreter package) from the pinned E2B commit.

Called by scripts/sync_upstream.py with the same checkout as the core SDK, so all packages are
always generated from one upstream commit:

    packages/code-interpreter-js/src, tests  -> code-interpreter/src, code-interpreter/tests
                                                (without tests/runtimes)
    packages/code-interpreter-js/README.md   -> code-interpreter/README.md (sections 3 and 4)

code-interpreter/package.json and the build and test configs are this repository's own. Generated
paths are never edited by hand. Every rule asserts how often it matched, so when upstream moves
code the sync fails instead of shipping an upstream default.
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "code-interpreter"
HERE = ROOT / "scripts" / "code-interpreter"
DOMAIN = "boxfab.io"
DOCS_URL = "https://boxfab.dev/docs"

ENV_VARS = ["API_KEY", "DOMAIN", "DEBUG", "API_URL", "SANDBOX_URL", "TESTS_TEMPLATE", "INTEGRATION_TEST"]
ENV_RX = re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b")

DELETE = ["tests/runtimes"]  # Cloudflare Workers smoke suite: its own toolchain, not run here

EXACT = [
    ("src/client.ts", "  E2BClientOpts,\n  E2B as CoreE2B,\n", "  BoxFabClientOpts,\n  BoxFab as CoreBoxFab,\n", 1),
    ("src/client.ts", "export type { E2BClientOpts }", "export type { BoxFabClientOpts }", 1),
    ("src/client.ts", " * E2B client with an explicitly bound connection configuration.",
     " * BoxFab client with an explicitly bound connection configuration.", 1),
    ("src/client.ts", " * import { E2B } from '@e2b/code-interpreter'", " * import { BoxFab } from '@boxfab/code-interpreter'", 1),
    ("src/client.ts", " * const client = new E2B({ apiKey: 'e2b_...', domain: 'e2b.dev' })",
     f" * const client = new BoxFab({{ apiKey: 'e2b_...', domain: '{DOMAIN}' }})", 1),
    ("src/client.ts", "export class E2B {", "export class BoxFab {", 1),
    ("src/client.ts", "constructor(opts?: E2BClientOpts)", "constructor(opts?: BoxFabClientOpts)", 1),
    ("src/client.ts", "const boundOpts: E2BClientOpts =", "const boundOpts: BoxFabClientOpts =", 1),
    ("src/client.ts", "const core = new CoreE2B(boundOpts)", "const core = new CoreBoxFab(boundOpts)", 1),
    ("src/index.ts", "export { E2B } from './client'\nexport type { E2BClientOpts } from './client'",
     "export { BoxFab, BoxFab as E2B } from './client'\n"
     "export type { BoxFabClientOpts, BoxFabClientOpts as E2BClientOpts } from './client'", 1),
    # the Sandbox docstring: product name, docs link, import
    ("src/sandbox.ts", " * E2B cloud sandbox is a secure and isolated cloud environment.",
     " * BoxFab cloud sandbox is a secure and isolated cloud environment.", 1),
    ("src/sandbox.ts", " * Check docs [here](https://e2b.dev/docs).", f" * Check docs [here]({DOCS_URL}).", 1),
    ("src/sandbox.ts", " * import { Sandbox } from '@e2b/code-interpreter'", " * import { Sandbox } from '@boxfab/code-interpreter'", 1),
]

README_START = "### 3. Execute code with code interpreter inside Sandbox\n"
README_END = "### 5. Check docs\n"
README_RULES = [
    (r"'@e2b/code-interpreter'", "'@boxfab/code-interpreter'", 2),
    (r"create an `E2B` client", "create a `BoxFab` client", 1),
    (r"import \{ E2B \} from", "import { BoxFab } from", 1),
    (r"new E2B\(\{ apiKey: 'e2b_\*\*\*', domain: 'e2b\.dev' \}\)",
     f"new BoxFab({{ apiKey: 'e2b_***', domain: '{DOMAIN}' }})", 1),
]

# What must not remain in shipped code. The `e2b_` API-key prefix and the `E2B-Traffic-Access-Token`
# header are protocol, not branding.
FORBIDDEN = [
    (re.compile(r"from 'e2b'"), "e2b import"),
    (re.compile(r"@e2b/code-interpreter"), "upstream package name"),
    (re.compile(r"\bE2B_(" + "|".join(ENV_VARS) + r")\b"), "E2B_* variable"),
    (re.compile(r"e2b\.dev|e2b\.app"), "E2B domain"),
]


def sync(src: Path):
    """Generate code-interpreter/ from `src`, an E2B monorepo checkout at the pinned commit."""
    up = src / "packages/code-interpreter-js"
    if not (up / "src").is_dir():
        sys.exit(f"{up}/src not found")
    for d in ("src", "tests"):
        shutil.rmtree(OUT / d, ignore_errors=True)
        shutil.copytree(up / d, OUT / d)
    shutil.copy2(up / "CHANGELOG.md", OUT / "CHANGELOG-E2B.md")
    for rel in DELETE:
        p = OUT / rel
        if not p.is_dir():
            sys.exit(f"code-interpreter DELETE: {rel} not found upstream")
        shutil.rmtree(p)
    shutil.copy2(HERE / "boxfab-env.setup.ts", OUT / "tests/boxfab-env.setup.ts")
    # MIT like the core; the package ships the repository's LICENSE, which must carry the code
    # interpreter's upstream copyright line and permission text.
    up_lic = (up / "LICENSE").read_text()
    ours = (ROOT / "LICENSE").read_text()
    for line in (ln for ln in up_lic.splitlines() if ln.startswith("Copyright")):
        if line not in ours.splitlines():
            sys.exit(f"LICENSE lacks the code interpreter's upstream copyright line: {line}")
    if not ours.rstrip().endswith(up_lic[up_lic.index("Permission is hereby granted"):].rstrip()):
        sys.exit("LICENSE permission text differs from the code interpreter's")
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
    if counts != EXPECT_COUNTS:
        sys.exit(f"code-interpreter renames: {counts}, expected {EXPECT_COUNTS}")
    for rel, old, new, expected in EXACT:
        p = OUT / rel
        text = p.read_text()
        if text.count(old) != expected:
            sys.exit(f"code-interpreter/{rel}: expected {expected} x {old[:70]!r}, found {text.count(old)}")
        p.write_text(text.replace(old, new))
    if (OUT / "src/index.ts").read_text().count("export * from 'boxfab'") != 1:
        sys.exit("code-interpreter/src/index.ts: core re-export changed upstream")

    text = (up / "README.md").read_text()
    if text.count(README_START) != 1 or text.count(README_END) != 1:
        sys.exit("code-interpreter-js/README.md: section headings changed upstream")
    body = text[text.index(README_START):text.index(README_END)]
    for rx, repl, count in README_RULES:
        body, n = re.subn(rx, repl, body)
        if n != count:
            sys.exit(f"code-interpreter README {rx!r}: {n} matches, expected {count}")
    left = [ln for ln in body.splitlines() if re.search(r"@e2b/|e2b\.dev|E2B_|\bE2B\b", ln)]
    if left:
        sys.exit(f"code-interpreter README: upstream references left: {left}")
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
        sys.exit("code-interpreter audit failed:\n  " + "\n  ".join(problems))
    print(f"  code-interpreter: {counts}")


EXPECT_COUNTS = {"imports": 6, "env": 8, "links": 4}  # at the pinned commit; a change means upstream moved
