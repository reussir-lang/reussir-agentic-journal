"""Check that every `*agentic-note*: <address>` marker in a Reussir checkout
names a tree or section that exists in this forest.

    python3 scripts/check-markers.py ../reussir
"""

import pathlib
import re
import subprocess
import sys

journal = pathlib.Path(__file__).resolve().parent.parent
addresses = set()
for tree in (journal / "trees").rglob("*.tree"):
    addresses.add(tree.stem)
    addresses.update(re.findall(r"\\subtree\[([^\]]+)\]", tree.read_text()))

repo = sys.argv[1] if len(sys.argv) > 1 else "../reussir"
out = subprocess.run(
    ["git", "-C", repo, "grep", "-n", "-o", "-E", r"\*agentic-note\*: [A-Za-z0-9-]+", "--", ".", ":!AGENTS.md"],
    capture_output=True,
    text=True,
).stdout
missing = 0
lines = [line for line in out.splitlines() if line]
for line in lines:
    where, addr = line.rsplit(": ", 1)
    if addr not in addresses:
        missing += 1
        print(f"{where.rsplit(':', 1)[0]}: no tree or section named {addr}")
print(f"{len(lines)} markers checked, {missing} unresolved")
sys.exit(1 if missing else 0)
