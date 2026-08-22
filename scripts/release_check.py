"""Fast, model-free release policy checks for CI and local handoff."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = [
    "README.md",
    "SETUP.md",
    "USAGE.md",
    "OPERATIONS.md",
    "ACCEPTANCE.md",
    "TESTING.md",
    "ARCHITECTURE.md",
    "COMPATIBILITY.md",
    "PRIVACY.md",
    "LICENSING.md",
    "HANDOVER.md",
    "REQUIREMENTS.md",
    "DEMO.md",
    "AUDIT.md",
    "BAIF_ONBOARDING_RUNBOOK.html",
]
SECRET_PATTERNS = [re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), re.compile(rb"hf_[A-Za-z0-9]{30,}"), re.compile(rb"(?:sk|ghp)_[A-Za-z0-9]{30,}")]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HTML_LINK = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)


def _local_link_target(source: Path, raw_target: str) -> Path | None:
    target = unquote(raw_target.strip().split()[0].strip("<>"))
    if not target or target.startswith(("/", "#", "http://", "https://", "mailto:", "data:", "javascript:")):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return (source.parent / target).resolve() if target else None


def main() -> int:
    failures: list[str] = []
    for name in REQUIRED_DOCS:
        if not (ROOT / name).exists(): failures.append(f"Missing handover document: {name}")
    encoded_files = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    forbidden_roots = {"models", "outputs", "temp", ".venv", ".venv310", ".venv39", "tmp"}
    inspected = 0
    documentation_files: list[Path] = []
    for encoded in encoded_files:
        if not encoded: continue
        path = Path(encoded.decode())
        if not (ROOT / path).is_file():
            continue
        inspected += 1
        if path.suffix.lower() in {".md", ".html"}:
            documentation_files.append(path)
        if path.parts and path.parts[0] in forbidden_roots and path.name != ".gitkeep": failures.append(f"Generated/private path is tracked: {path}")
        data = (ROOT / path).read_bytes()
        if any(pattern.search(data) for pattern in SECRET_PATTERNS): failures.append(f"Possible credential in tracked file: {path}")
    for path in documentation_files:
        text = (ROOT / path).read_text(encoding="utf-8", errors="replace")
        pattern = MARKDOWN_LINK if path.suffix.lower() == ".md" else HTML_LINK
        for match in pattern.finditer(text):
            target = _local_link_target(ROOT / path, match.group(1))
            if target is not None and not target.exists():
                failures.append(f"Broken local documentation link in {path}: {match.group(1)}")
    glossary = json.loads((ROOT / "config" / "agriculture_glossary.json").read_text(encoding="utf-8"))
    if not glossary.get("version") or len(glossary.get("terms", [])) < 10: failures.append("Agriculture glossary is not versioned or sufficiently populated.")
    if failures:
        print("Release policy checks FAILED")
        for failure in failures: print("-", failure)
        return 1
    print(f"Release policy checks PASSED ({inspected} repository paths inspected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
