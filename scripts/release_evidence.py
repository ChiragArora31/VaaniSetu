"""Generate a source manifest and CycloneDX-style installed dependency SBOM."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from importlib.metadata import distributions
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "release_evidence"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / value.decode() for value in result.stdout.split(b"\0") if value and (ROOT / value.decode()).is_file()]


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    sources = [
        {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in repository_files()
    ]
    (OUTPUT / "source_manifest.json").write_text(json.dumps({"generated_at": generated_at, "git_commit": commit, "files": sources}, indent=2), encoding="utf-8")
    components = []
    for distribution in sorted(distributions(), key=lambda item: (item.metadata.get("Name") or "").casefold()):
        name = distribution.metadata.get("Name")
        if name:
            components.append({"type": "library", "name": name, "version": distribution.version, "purl": f"pkg:pypi/{name.lower()}@{distribution.version}"})
    sbom = {"bomFormat": "CycloneDX", "specVersion": "1.5", "serialNumber": f"urn:uuid:vaanisetu-{commit[:12]}", "version": 1, "metadata": {"timestamp": generated_at, "component": {"type": "application", "name": "VaaniSetu", "version": commit[:12]}}, "components": components}
    (OUTPUT / "python_sbom.cdx.json").write_text(json.dumps(sbom, indent=2), encoding="utf-8")
    print(f"Release evidence created in {OUTPUT}: {len(sources)} source files, {len(components)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
