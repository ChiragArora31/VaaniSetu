"""Artifact packaging helpers."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def create_artifact_zip(artifacts: dict[str, Path], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for key, path in sorted(artifacts.items()):
            if key == "bundle_zip" or not path.exists() or path == output_path:
                continue
            archive.write(path, arcname=path.name)
    return output_path
