from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.config import ROOT, TestConfig
from tests.utils import StageResult, python_executable, run_command, write_report

SEPARATOR = "=" * 60


def npm_command() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def discover(category: str) -> StageResult:
    return run_command(
        category.upper(),
        [
            python_executable(),
            "-m",
            "unittest",
            "discover",
            "-s",
            str(ROOT / "tests" / category),
            "-t",
            str(ROOT),
            "-v",
        ],
        ROOT,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa a suíte completa do DevFlow.")
    parser.add_argument(
        "--category",
        choices=["all", "backend", "frontend", "integration", "security", "smoke"],
        default="all",
    )
    parser.add_argument("--fast", action="store_true", help="Ignora build e suíte Django completa.")
    args = parser.parse_args()

    print(SEPARATOR)
    print("DEVFLOW - TESTE COMPLETO")
    print(SEPARATOR)
    try:
        config = TestConfig.from_env()
        config.validate()
    except ValueError as error:
        print(f"[ERRO] CONFIGURAÇÃO: {error}")
        return 1

    results: list[StageResult] = []
    selected = args.category
    local_env = {"DEBUG": "True", "DATABASE_URL": "sqlite:///devflow-test.sqlite3"}

    def add(result: StageResult) -> None:
        results.append(result)
        print(f"[{result.status}] {result.name}")
        if result.failed:
            encoding = sys.stdout.encoding or "utf-8"
            safe_detail = result.detail[-4000:].encode(encoding, errors="replace").decode(encoding)
            print(safe_detail)

    if selected in {"all", "backend"}:
        add(discover("backend"))
        add(
            run_command(
                "BACKEND CHECK",
                [python_executable(), "manage.py", "check"],
                ROOT / "backend",
                local_env,
            )
        )
        add(
            run_command(
                "MIGRATIONS",
                [python_executable(), "manage.py", "showmigrations", "--plan"],
                ROOT / "backend",
                local_env,
            )
        )
        if not args.fast:
            add(
                run_command(
                    "BACKEND DJANGO",
                    [python_executable(), "manage.py", "test"],
                    ROOT / "backend",
                    local_env,
                )
            )

    if selected in {"all", "frontend"}:
        add(discover("frontend"))
        add(run_command("FRONTEND TESTS", [npm_command(), "test", "--", "--run"], ROOT / "frontend"))
        add(run_command("TYPESCRIPT", [npm_command(), "exec", "tsc", "--", "--noEmit", "-p", "tsconfig.app.json"], ROOT / "frontend"))
        add(run_command("LINT", [npm_command(), "run", "lint"], ROOT / "frontend"))
        if not args.fast:
            add(run_command("FRONTEND BUILD", [npm_command(), "run", "build"], ROOT / "frontend"))

    if selected in {"all", "integration"}:
        add(discover("integration"))

    if selected in {"all", "security"}:
        add(discover("security"))

    if selected in {"all", "smoke"}:
        if config.run_smoke:
            add(discover("smoke"))
        else:
            add(StageResult("SMOKE PRODUÇÃO", "IGNORADO", skipped=1, detail="Defina DEVFLOW_RUN_SMOKE=1."))

    write_report(results)
    passed = sum(row.passed for row in results)
    failed = sum(row.failed for row in results)
    skipped = sum(row.skipped for row in results)
    print(SEPARATOR)
    print("RESULTADO")
    print(f"Passaram: {passed}")
    print(f"Falharam: {failed}")
    print(f"Ignorados: {skipped}")
    print(f"STATUS: {'FALHOU' if failed else 'PASSOU'}")
    print(SEPARATOR)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
