"""Build a privacy-safe, checksum-indexed VaaniSetu submission candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "VaaniSetu_Submission_Candidate.zip"

REQUIRED = [
    "submission/VaaniSetu_Final_Hackathon_Deck.pptx",
    "SUBMISSION_RUNBOOK.md",
    "BAIF_ONBOARDING_RUNBOOK.html",
    "BAIF_ONBOARDING_RUNBOOK.css",
    "README.md",
    "IMPLEMENTATION_ROADMAP.md",
    "HACKATHON_REQUIREMENTS_AUDIT.md",
    "RELEASE_CHECKLIST.md",
    "TEST_EVIDENCE.md",
    "DELIVERY_COMPATIBILITY.md",
    "BAIF_ARCHITECTURE_NOTE.md",
    "USER_GUIDE.md",
    "ADMIN_GUIDE.md",
    "HANDOVER.md",
    "UAT.md",
    "OPEN_SOURCE_COMPLIANCE.md",
    "PRIVACY.md",
    "SUPPORT_MODEL.md",
    "TROUBLESHOOTING.md",
    "samples/README.md",
    "samples/demo_agriculture.txt",
    "samples/demo_agriculture.csv",
    "outputs/release_evidence/source_manifest.json",
    "outputs/release_evidence/python_sbom.cdx.json",
    "outputs/quality_report.json",
    "outputs/translation_reviewer_worksheet.csv",
    "outputs/stress_report.json",
    "outputs/preflight_report.json",
    "outputs/model_inventory.json",
    "outputs/failure_drill_report.json",
    "outputs/demo_e2e_report.json",
    "outputs/demo_assets/Agriculture_First.webm",
    "outputs/VaaniSetu_Backup_Walkthrough.mp4",
    "tmp/vaanisetu-result-evidence.png",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if path.suffix.lower() != ".json":
        return data
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return data
    rendered = json.dumps(value, ensure_ascii=False, indent=2).replace(str(ROOT), ".")
    rendered = rendered.replace(str(Path.home()), "~") + "\n"
    return rendered.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build VaaniSetu submission candidate ZIP.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    paths = [ROOT / relative for relative in REQUIRED]
    demo_report = json.loads((ROOT / "outputs" / "demo_e2e_report.json").read_text(encoding="utf-8"))
    demo_package = Path(demo_report["artifacts"]["bundle_zip"])
    if not demo_package.is_absolute():
        demo_package = ROOT / demo_package
    demo_package = demo_package.resolve()
    if demo_package.suffix.lower() != ".zip" or not demo_package.is_relative_to((ROOT / "outputs").resolve()):
        raise SystemExit("Demo report points outside the generated outputs directory.")
    paths.append(demo_package)

    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("Submission inputs missing:\n- " + "\n- ".join(missing))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            if path == demo_package:
                archive_name = "demo/prepared_vaanisetu_outputs.zip"
            elif path.is_relative_to(ROOT):
                relative = path.relative_to(ROOT).as_posix()
                if relative == "tmp/vaanisetu-result-evidence.png":
                    archive_name = "evidence/browser/real_model_approved_reuse.png"
                elif relative == "outputs/demo_assets/Agriculture_First.webm":
                    archive_name = "demo/input/Agriculture_First.webm"
                elif relative == "outputs/VaaniSetu_Backup_Walkthrough.mp4":
                    archive_name = "demo/VaaniSetu_Backup_Walkthrough.mp4"
                elif relative.startswith("outputs/release_evidence/"):
                    archive_name = "evidence/release/" + path.name
                elif relative.startswith("outputs/"):
                    archive_name = "evidence/" + path.name
                else:
                    archive_name = relative
            else:
                raise SystemExit(f"Refusing file outside repository: {path}")
            data = safe_bytes(path)
            archive.writestr(archive_name, data)
            records.append({"path": archive_name, "bytes": len(data), "sha256": digest(data)})
        manifest = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "privacy": "No accounts, sessions, BAIF content, secrets, model weights or runtime logs.",
            "files": records,
        }
        archive.writestr("SUBMISSION_MANIFEST.json", json.dumps(manifest, indent=2).encode("utf-8"))

    print(f"Submission candidate created: {args.output} ({args.output.stat().st_size} bytes, {len(records)} evidence files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
