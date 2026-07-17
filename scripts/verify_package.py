"""Verify an offline VaaniSetu ZIP without extracting untrusted paths."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_MEMBER_BYTES = 512 * 1024 * 1024
MAX_PACKAGE_TOTAL_BYTES = 2 * 1024 * 1024 * 1024


def verify(path: Path) -> list[str]:
    failures: list[str] = []
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            names = {info.filename for info in infos}
            folded_names: dict[str, str] = {}
            for info in infos:
                folded = info.filename.casefold()
                if folded in folded_names:
                    failures.append(f"Duplicate archive member: {info.filename}")
                else:
                    folded_names[folded] = info.filename
            if sum(info.file_size for info in infos) > MAX_PACKAGE_TOTAL_BYTES:
                failures.append("Package is too large to verify safely.")
            for name in names:
                member = PurePosixPath(name)
                if member.is_absolute() or ".." in member.parts:
                    failures.append(f"Unsafe path: {name}")
            if "integrity_manifest.json" not in names:
                return failures + ["Missing integrity_manifest.json"]
            manifest_info = archive.getinfo("integrity_manifest.json")
            if manifest_info.file_size > MAX_MANIFEST_BYTES:
                return failures + ["Integrity manifest is too large to verify safely."]
            manifest = json.loads(archive.read("integrity_manifest.json"))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
                return failures + ["Integrity manifest has an invalid structure."]
            expected_names = {"integrity_manifest.json"}
            manifest_names: set[str] = set()
            for item in manifest["files"]:
                if not isinstance(item, dict):
                    failures.append("Integrity manifest contains an invalid file record.")
                    continue
                filename = str(item.get("filename", ""))
                folded = filename.casefold()
                if not filename or folded in manifest_names:
                    failures.append(f"Duplicate or empty manifest filename: {filename or '<empty>'}")
                    continue
                manifest_names.add(folded)
                expected_names.add(filename)
                if filename not in names:
                    failures.append(f"Missing file: {filename}")
                    continue
                info = archive.getinfo(filename)
                if info.file_size > MAX_PACKAGE_MEMBER_BYTES:
                    failures.append(f"File is too large to verify safely: {filename}")
                    continue
                declared_size = int(item.get("bytes", -1))
                if info.file_size != declared_size:
                    failures.append(f"Size mismatch: {filename}")
                    continue
                data = archive.read(info)
                if hashlib.sha256(data).hexdigest() != item.get("sha256"):
                    failures.append(f"Checksum mismatch: {filename}")
            for filename in sorted(names - expected_names):
                failures.append(f"Unexpected file: {filename}")
    except (OSError, BadZipFile, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
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
