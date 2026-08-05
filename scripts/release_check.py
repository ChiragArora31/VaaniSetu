"""Fast, model-free release policy checks for CI and local handoff."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOCS = ["README.md", "BAIF_ONBOARDING_RUNBOOK.html", "HANDOVER.md", "USER_GUIDE.md", "ADMIN_GUIDE.md", "PRIVACY.md", "TROUBLESHOOTING.md", "SUPPORT_MODEL.md", "UAT.md", "RELEASE_CHECKLIST.md", "TEST_EVIDENCE.md", "OPEN_SOURCE_COMPLIANCE.md"]
SECRET_PATTERNS = [re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), re.compile(rb"hf_[A-Za-z0-9]{30,}"), re.compile(rb"(?:sk|ghp)_[A-Za-z0-9]{30,}")]


def main() -> int:
    failures: list[str] = []
    for name in REQUIRED_DOCS:
        if not (ROOT / name).exists(): failures.append(f"Missing handover document: {name}")
    encoded_files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True).stdout.split(b"\0")
    forbidden_roots = {"models", "outputs", "temp", ".venv", ".venv310", ".venv39", "tmp"}
    for encoded in encoded_files:
        if not encoded: continue
        path = Path(encoded.decode())
        if path.parts and path.parts[0] in forbidden_roots and path.name != ".gitkeep": failures.append(f"Generated/private path is tracked: {path}")
        data = (ROOT / path).read_bytes()
        if any(pattern.search(data) for pattern in SECRET_PATTERNS): failures.append(f"Possible credential in tracked file: {path}")
    glossary = json.loads((ROOT / "config" / "agriculture_glossary.json").read_text(encoding="utf-8"))
    if not glossary.get("version") or len(glossary.get("terms", [])) < 10: failures.append("Agriculture glossary is not versioned or sufficiently populated.")
    if failures:
        print("Release policy checks FAILED")
        for failure in failures: print("-", failure)
        return 1
    print(f"Release policy checks PASSED ({len(encoded_files) - 1} tracked paths inspected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
