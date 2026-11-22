"""Fail if the repository contains things that look like real personal data.

Generic checks run everywhere. Personal words (names, places) are NOT stored in the
repository: put them, one per line, into the git-ignored file ``.privacy-terms`` or
the ``PRIVACY_TERMS`` environment variable / GitHub secret (comma-separated).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIX = {".png", ".gz", ".jpg", ".ico"}
PUBLIC_DATASETS = {"worldmap/app/worldmap/static/base.json", "worldmap/app/worldmap/static/regions.json"}  # Natural Earth / BFS, no personal data
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
ALLOWED_EMAIL = re.compile(r"(noreply|example)\.(com|org)|users\.noreply\.github\.com|anthropic\.com")
MAX_BYTES = 5_000_000


def files():
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True, check=True)  # noqa: S603,S607
    return [ROOT / f for f in out.stdout.splitlines() if f]


def terms():
    raw = os.environ.get("PRIVACY_TERMS", "")
    t = [x.strip() for x in raw.split(",") if x.strip()]
    f = ROOT / ".privacy-terms"
    if f.exists():
        t += [x.strip() for x in f.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    return t


def main() -> int:
    problems = []
    words = [re.compile(r"(?<![\w])" + re.escape(w) + r"(?![\w])", re.IGNORECASE) for w in terms()]
    for p in files():
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix in (".db", ".sqlite") or p.name in ("options.json", "Records.json"):
            problems.append(f"{rel}: data file must not be committed")
            continue
        if p.suffix in SKIP_SUFFIX or not p.is_file() or rel == ".privacy-terms":
            continue
        if p.stat().st_size > MAX_BYTES:
            problems.append(f"{rel}: unexpectedly large file")
        if rel in PUBLIC_DATASETS:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in EMAIL.finditer(text):
            if not ALLOWED_EMAIL.search(m.group(0)):
                problems.append(f"{rel}: e-mail address {m.group(0)!r}")
        for w in words:
            if w.search(text):
                problems.append(f"{rel}: contains a private term")
    for line in problems:
        print("PRIVACY:", line)
    print(f"privacy check: {len(problems)} problem(s), {len(words)} private term(s) checked")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
