"""Run the six demo-day recovery scenarios and record machine-readable evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "failure_drill_report.json"

SCENARIOS = {
    "no_model": "tests.test_core.TranslationGuardTest.test_setup_error_is_local_and_privacy_clear",
    "low_disk": "tests.test_core.FileUtilsTest.test_low_disk_rejects_job_before_partial_directories_are_created",
    "cancelled_job": "tests.test_adversarial.JobQueueAdversarialTest.test_cancellation_wins_race_with_task_completion",
    "worker_restart": "tests.test_core.JobManagerTest.test_restart_marks_interrupted_job_failed",
    "corrupted_zip": "tests.test_core.OfflinePackageTest.test_integrity_verifier_detects_tampering",
    "offline_playback": "tests.test_core.OfflinePackageTest.test_offline_landing_page_links_and_plays_artifacts",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run VaaniSetu demo-day failure recovery drill.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    results = []
    for scenario, test_name in SCENARIOS.items():
        started = time.monotonic()
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", test_name],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "scenario": scenario,
                "test": test_name,
                "passed": completed.returncode == 0,
                "duration_seconds": round(time.monotonic() - started, 3),
                "output": (completed.stdout + completed.stderr).strip(),
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenarios": results,
        "passed": all(item["passed"] for item in results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"passed": payload["passed"], "scenarios": [{"scenario": item["scenario"], "passed": item["passed"]} for item in results]}, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
