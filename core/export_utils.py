"""Artifact packaging helpers."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def create_artifact_zip(artifacts: dict[str, Path], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, str | int]] = []
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for key, path in sorted(artifacts.items()):
            if key == "bundle_zip" or not path.exists() or path == output_path:
                continue
            data = path.read_bytes()
            archive.writestr(path.name, data)
            entries.append({"key": key, "filename": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest = {"schema_version": 1, "algorithm": "sha256", "files": entries}
        archive.writestr("integrity_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        rows = "".join(
            f"<tr><td>{html.escape(str(item['key']))}</td><td>{html.escape(str(item['filename']))}</td><td>{item['bytes']}</td></tr>"
            for item in entries
        )
        archive.writestr(
            "CONTENTS.html",
            "<!doctype html><meta charset='utf-8'><title>VaaniSetu offline package</title>"
            "<style>body{font:16px system-ui;max-width:900px;margin:3rem auto;padding:0 1rem}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:.6rem;text-align:left}</style>"
            "<h1>VaaniSetu offline package</h1><p>These files work without a VaaniSetu server. Verify them with <code>python scripts/verify_package.py PACKAGE.zip</code>.</p>"
            f"<table><thead><tr><th>Type</th><th>File</th><th>Bytes</th></tr></thead><tbody>{rows}</tbody></table>",
        )
    return output_path
