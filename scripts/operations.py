"""Cross-platform BAIF worker preflight, maintenance, recovery and support commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.settings import MODEL_DIR, OUTPUT_DIR, TEMP_DIR, ensure_directories
from core.health import collect_health_checks


SCHEMA_VERSION = "1"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def _total_memory_gb() -> float | None:
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1024**3, 1)
    except ImportError:
        pass
    try:
        if platform.system() == "Windows":
            import ctypes
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong), ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong), ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong), ("available_extended", ctypes.c_ulonglong)]
            status = MemoryStatus(); status.length = ctypes.sizeof(status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return round(status.total / 1024**3, 1)
        if platform.system() == "Darwin":
            value = subprocess.run(["sysctl", "-n", "hw.memsize"], check=True, capture_output=True, text=True).stdout.strip()
            return round(int(value) / 1024**3, 1)
        return round((os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / 1024**3, 1)
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        return None


def preflight(output: Path | None = None, port: int = 8501) -> int:
    ensure_directories()
    disk = shutil.disk_usage(OUTPUT_DIR)
    checks = [check.__dict__ for check in collect_health_checks(allow_model_download=False)]
    memory_gb = _total_memory_gb()
    writable = True
    try:
        with tempfile.NamedTemporaryFile(dir=OUTPUT_DIR, delete=True):
            pass
    except OSError:
        writable = False
    port_available = False
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
            port_available = True
        except OSError:
            pass
    gates = {
        "python_3_10_or_3_11": (3, 10) <= sys.version_info[:2] <= (3, 11),
        "output_writable": writable,
        "free_disk_at_least_20_gb": disk.free >= 20 * 1024**3,
        "ram_at_least_16_gb": memory_gb is None or memory_gb >= 16,
        "port_available": port_available,
        "ffmpeg_ready": next((item["ok"] for item in checks if item["name"] == "FFmpeg"), False),
        "ffprobe_ready": next((item["ok"] for item in checks if item["name"] == "ffprobe"), False),
        "ocr_ready": next((item["ok"] for item in checks if item["name"] == "Automatic OCR"), False),
        "quality_models_ready": all(next((item["ok"] for item in checks if item["name"] == f"IndicTrans2 {direction}"), False) for direction in ("en-indic", "indic-en", "indic-indic")),
    }
    payload = {"generated_at": _utc(), "platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count(), "memory_gb": memory_gb, "disk_free_gb": round(disk.free / 1024**3, 1), "port": port, "gates": gates, "checks": checks, "ready": all(gates.values())}
    target = output or OUTPUT_DIR / "preflight_report.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "checks"}, indent=2))
    return 0 if payload["ready"] else 1


def cleanup(days: int, dry_run: bool) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    removed: list[str] = []
    for root in (TEMP_DIR, OUTPUT_DIR / ".jobs" / "uploads"):
        if not root.exists():
            continue
        for path in root.iterdir():
            modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            if modified >= cutoff or path.name == ".gitkeep":
                continue
            removed.append(str(path))
            if not dry_run:
                shutil.rmtree(path, ignore_errors=True) if path.is_dir() else path.unlink(missing_ok=True)
    print(json.dumps({"dry_run": dry_run, "older_than_days": days, "removed": removed}, indent=2))
    return 0


def backup(target: Path) -> int:
    ensure_directories()
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in OUTPUT_DIR.rglob("*"):
            if not path.is_file() or "logs" in path.relative_to(OUTPUT_DIR).parts or path.resolve() == target.resolve():
                continue
            relative = path.relative_to(OUTPUT_DIR).as_posix()
            data = path.read_bytes()
            archive.writestr(relative, data)
            manifest.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        archive.writestr("backup_manifest.json", json.dumps({"created_at": _utc(), "schema_version": SCHEMA_VERSION, "files": manifest}, indent=2))
    print(f"Backup created: {target} ({len(manifest)} files)")
    return 0


def restore(source: Path, force: bool) -> int:
    try:
        with ZipFile(source) as archive:
            names = archive.namelist()
            if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
                raise ValueError("Backup contains an unsafe path.")
            manifest = json.loads(archive.read("backup_manifest.json"))
            if str(manifest.get("schema_version")) != SCHEMA_VERSION:
                raise ValueError("Backup schema is not compatible with this release.")
            for item in manifest.get("files", []):
                data = archive.read(item["path"])
                if hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError(f"Checksum mismatch: {item['path']}")
                target = OUTPUT_DIR / item["path"]
                if target.exists() and not force:
                    raise ValueError(f"Refusing to overwrite {target}; rerun with --force after making a backup.")
            for item in manifest.get("files", []):
                target = OUTPUT_DIR / item["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(item["path"]))
    except (OSError, BadZipFile, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Restore failed: {exc}")
        return 1
    print("Restore completed. Restart VaaniSetu before accepting jobs.")
    return 0


def migrate() -> int:
    ensure_directories()
    marker = OUTPUT_DIR / ".schema_version"
    current = marker.read_text(encoding="utf-8").strip() if marker.exists() else "0"
    if current not in {"0", SCHEMA_VERSION}:
        print(f"Unsupported storage schema {current}; restore a compatible backup.")
        return 1
    marker.write_text(SCHEMA_VERSION + "\n", encoding="utf-8")
    print(f"Storage schema is current: {SCHEMA_VERSION}")
    return 0


def support_bundle(target: Path) -> int:
    ensure_directories()
    report = OUTPUT_DIR / "preflight_report.json"
    preflight(report)
    redactions = [(str(Path.home()), "<USER_HOME>"), (str(ROOT), "<APP_ROOT>")]
    token_pattern = re.compile(r"(?i)(token|password|secret|authorization)([\"'=:\s]+)[^\s\",}]+")
    logs = OUTPUT_DIR / "logs" / "vaanisetu.jsonl"
    log_text = ""
    if logs.exists():
        safe_lines = []
        for line in logs.read_text(encoding="utf-8", errors="replace").splitlines()[-500:]:
            try:
                event = json.loads(line)
                event.pop("exception", None)
                event.pop("message", None)
                safe_lines.append(json.dumps(event, ensure_ascii=False))
            except json.JSONDecodeError:
                continue
        log_text = "\n".join(safe_lines)
    for original, replacement in redactions:
        log_text = log_text.replace(original, replacement)
    log_text = token_pattern.sub(r"\1\2<REDACTED>", log_text)
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        archive.write(report, "preflight_report.json")
        archive.writestr("recent_events.redacted.jsonl", log_text)
        archive.writestr("README.txt", "Privacy-safe diagnostics only. Source text, translations, credentials, job artifacts, and model weights are intentionally excluded.\n")
    print(f"Support bundle created: {target}")
    return 0


def inventory(target: Path) -> int:
    manifest = json.loads((ROOT / "config" / "model_manifest.json").read_text(encoding="utf-8"))
    files = []
    for path in MODEL_DIR.rglob("*") if MODEL_DIR.exists() else []:
        if path.is_file() and path.name not in {".DS_Store"}:
            files.append({"path": path.relative_to(MODEL_DIR).as_posix(), "bytes": path.stat().st_size, "sha256": _sha256(path)})
    payload = {"generated_at": _utc(), "manifest": manifest, "installed_bytes": sum(item["bytes"] for item in files), "installed_files": files}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Model inventory created: {target} ({len(files)} files)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Operate and recover a VaaniSetu BAIF worker.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("preflight"); check.add_argument("--output", type=Path); check.add_argument("--port", type=int, default=8501)
    clean = commands.add_parser("cleanup"); clean.add_argument("--days", type=int, default=7); clean.add_argument("--dry-run", action="store_true")
    save = commands.add_parser("backup"); save.add_argument("target", type=Path)
    load = commands.add_parser("restore"); load.add_argument("source", type=Path); load.add_argument("--force", action="store_true")
    commands.add_parser("migrate")
    support = commands.add_parser("support-bundle"); support.add_argument("target", type=Path)
    models = commands.add_parser("model-inventory"); models.add_argument("target", type=Path, nargs="?", default=OUTPUT_DIR / "model_inventory.json")
    args = parser.parse_args()
    if args.command == "preflight": return preflight(args.output, args.port)
    if args.command == "cleanup": return cleanup(args.days, args.dry_run)
    if args.command == "backup": return backup(args.target)
    if args.command == "restore": return restore(args.source, args.force)
    if args.command == "migrate": return migrate()
    if args.command == "support-bundle": return support_bundle(args.target)
    return inventory(args.target)


if __name__ == "__main__":
    raise SystemExit(main())
