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
        rows = "".join(
            f"<tr><td>{html.escape(str(item['key']))}</td>"
            f"<td><a href='{html.escape(str(item['filename']), quote=True)}'>{html.escape(str(item['filename']))}</a></td>"
            f"<td>{item['bytes']}</td></tr>"
            for item in entries
        )
        players = []
        for item in entries:
            filename = str(item["filename"])
            safe_name = html.escape(filename)
            safe_href = html.escape(filename, quote=True)
            suffix = Path(filename).suffix.lower()
            if suffix in {".mp3", ".wav", ".ogg", ".m4a"}:
                players.append(f"<article><h3>{safe_name}</h3><audio controls preload='metadata' src='{safe_href}'></audio></article>")
            elif suffix in {".mp4", ".webm"}:
                players.append(f"<article><h3>{safe_name}</h3><video controls preload='metadata' src='{safe_href}'></video></article>")
        playback = "".join(players) or "<p>No playable audio or video was requested for this package.</p>"
        contents_html = (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VaaniSetu offline package</title><style>"
            ":root{color-scheme:light}body{font:16px system-ui;color:#17312f;background:#f5f7f3;max-width:960px;margin:0 auto;padding:2rem 1rem 4rem}"
            "header,section{background:white;border:1px solid #dfe6df;border-radius:14px;padding:1.25rem;margin-bottom:1rem}"
            "h1{margin:.2rem 0}p{line-height:1.55}.badge{display:inline-block;background:#e2f2e8;color:#185b37;border-radius:999px;padding:.35rem .65rem;font-weight:700}"
            "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #dfe6df;padding:.7rem;text-align:left}a{color:#096b67;font-weight:650}"
            "article{border-top:1px solid #dfe6df;padding-top:.8rem;margin-top:.8rem}audio,video{width:100%;max-height:520px}code{overflow-wrap:anywhere}"
            "</style></head><body><header><span class='badge'>Works offline</span><h1>VaaniSetu field package</h1>"
            "<p>Play or open the translated material below. Keep this folder together so every link continues to work without internet or a VaaniSetu server.</p></header>"
            f"<section><h2>Play translated media</h2>{playback}</section>"
            f"<section><h2>All package files</h2><table><thead><tr><th>Type</th><th>Open file</th><th>Bytes</th></tr></thead><tbody>{rows}</tbody></table></section>"
            "<section><h2>Integrity</h2><p>An administrator can verify that no file changed with <code>python scripts/verify_package.py PACKAGE.zip</code>. Checksums are stored in <code>integrity_manifest.json</code>.</p></section>"
            "</body></html>"
        )
        contents_data = contents_html.encode("utf-8")
        archive.writestr("CONTENTS.html", contents_data)
        entries.append(
            {
                "key": "offline_contents",
                "filename": "CONTENTS.html",
                "bytes": len(contents_data),
                "sha256": hashlib.sha256(contents_data).hexdigest(),
            }
        )
        manifest = {"schema_version": 1, "algorithm": "sha256", "files": entries}
        archive.writestr("integrity_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return output_path
