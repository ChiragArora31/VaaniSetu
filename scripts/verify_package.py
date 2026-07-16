"""Verify an offline VaaniSetu ZIP without extracting untrusted paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


def verify(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        with ZipFile(path) as archive:
            names = set(archive.namelist())
            for name in names:
                member = PurePosixPath(name)
                if member.is_absolute() or ".." in member.parts:
                    failures.append(f"Unsafe path: {name}")
            if "integrity_manifest.json" not in names:
                return failures + ["Missing integrity_manifest.json"]
            manifest = json.loads(archive.read("integrity_manifest.json"))
            for item in manifest.get("files", []):
                filename = str(item.get("filename", ""))
                if filename not in names:
                    failures.append(f"Missing file: {filename}")
                    continue
                data = archive.read(filename)
                if len(data) != int(item.get("bytes", -1)):
                    failures.append(f"Size mismatch: {filename}")
                if hashlib.sha256(data).hexdigest() != item.get("sha256"):
                    failures.append(f"Checksum mismatch: {filename}")
    except (OSError, BadZipFile, json.JSONDecodeError, ValueError) as exc:
        failures.append(f"Unreadable package: {exc}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a VaaniSetu offline package.")
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    failures = verify(args.package)
    if failures:
        print("Package verification FAILED")
        for failure in failures:
            print("-", failure)
        return 1
    print("Package verification PASSED:", args.package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
