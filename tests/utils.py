from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from tests.config import ROOT, TestConfig

READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass
class StageResult:
    name: str
    status: str
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    detail: str = ""


def run_command(name: str, command: list[str], cwd: Path, env: dict[str, str] | None = None) -> StageResult:
    process = subprocess.run(
        command,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    output = process.stdout.strip()
    count = 1
    for pattern in (r"Ran (\d+) tests?", r"Tests\s+(\d+) passed", r"(\d+) passed"):
        match = re.search(pattern, output)
        if match:
            count = int(match.group(1))
            break
    passed_count = count if process.returncode == 0 else len(
        re.findall(r"\.\.\. ok$", output, flags=re.MULTILINE)
    )
    skipped_count = len(re.findall(r"\.\.\. skipped ", output))
    failure_count = 0 if process.returncode == 0 else max(
        1,
        sum(int(value) for value in re.findall(r"(?:failures|errors)=(\d+)", output)),
    )
    return StageResult(
        name=name,
        status="OK" if process.returncode == 0 else "ERRO",
        passed=passed_count,
        failed=failure_count,
        skipped=skipped_count,
        detail=output,
    )


def http_request(
    config: TestConfig,
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    method = method.upper()
    if config.production and method not in READ_ONLY_METHODS:
        raise RuntimeError(f"Método {method} bloqueado em produção.")
    request = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=config.timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def tracked_files() -> list[Path]:
    process = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        check=True,
    )
    return [ROOT / item.decode() for item in process.stdout.split(b"\0") if item]


def write_report(results: Iterable[StageResult]) -> None:
    rows = list(results)
    report_dir = ROOT / "tests" / "reports"
    report_dir.mkdir(exist_ok=True)
    totals = {
        "total": sum(row.passed + row.failed + row.skipped for row in rows),
        "passed": sum(row.passed for row in rows),
        "failed": sum(row.failed for row in rows),
        "skipped": sum(row.skipped for row in rows),
        "status": "FAILED" if any(row.failed for row in rows) else "PASSED",
        "stages": [asdict(row) for row in rows],
    }
    (report_dir / "latest-report.json").write_text(
        json.dumps(totals, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = ["DEVFLOW - RELATÓRIO DE TESTES", "=" * 60]
    lines.extend(f"[{row.status}] {row.name}: {row.detail}" for row in rows)
    lines.extend(
        [
            "=" * 60,
            f"Passaram: {totals['passed']}",
            f"Falharam: {totals['failed']}",
            f"Ignorados: {totals['skipped']}",
            f"STATUS: {totals['status']}",
        ]
    )
    (report_dir / "latest-report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def python_executable() -> str:
    candidates = [
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / "venv" / "Scripts" / "python.exe",
    ]
    return str(next((path for path in candidates if path.exists()), Path(sys.executable)))
