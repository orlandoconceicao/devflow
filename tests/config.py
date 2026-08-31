from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class TestConfig:
    mode: str
    backend_url: str
    frontend_url: str
    test_email: str | None
    test_password: str | None
    second_user_email: str | None
    second_user_password: str | None
    organization_id: str | None
    allow_production_writes: bool
    run_smoke: bool
    timeout: float

    @property
    def production(self) -> bool:
        return self.mode == "production"

    @classmethod
    def from_env(cls) -> "TestConfig":
        mode = os.getenv("DEVFLOW_TEST_MODE", "local").strip().lower()
        if mode not in {"local", "production"}:
            raise ValueError("DEVFLOW_TEST_MODE deve ser local ou production.")
        default_backend = (
            "https://devflow-backend-swart.vercel.app"
            if mode == "production"
            else "http://localhost:8000"
        )
        default_frontend = (
            "https://devflow-frontend-delta.vercel.app"
            if mode == "production"
            else "http://localhost:5173"
        )
        return cls(
            mode=mode,
            backend_url=os.getenv(
                "DEVFLOW_BACKEND_URL", default_backend
            ).rstrip("/"),
            frontend_url=os.getenv(
                "DEVFLOW_FRONTEND_URL", default_frontend
            ).rstrip("/"),
            test_email=os.getenv("DEVFLOW_TEST_EMAIL"),
            test_password=os.getenv("DEVFLOW_TEST_PASSWORD"),
            second_user_email=os.getenv("DEVFLOW_TEST_USER_2_EMAIL"),
            second_user_password=os.getenv("DEVFLOW_TEST_USER_2_PASSWORD"),
            organization_id=os.getenv("DEVFLOW_TEST_ORGANIZATION_ID"),
            allow_production_writes=_flag("DEVFLOW_ALLOW_PRODUCTION_WRITES"),
            run_smoke=_flag("DEVFLOW_RUN_SMOKE") or mode == "production",
            timeout=float(os.getenv("DEVFLOW_HTTP_TIMEOUT", "15")),
        )

    def validate(self) -> None:
        if self.production and self.allow_production_writes:
            raise ValueError(
                "Escritas em produção permanecem bloqueadas nesta suíte. "
                "Use um ambiente controlado de staging para testes destrutivos."
            )
        if self.production:
            for name, value in {
                "DEVFLOW_BACKEND_URL": self.backend_url,
                "DEVFLOW_FRONTEND_URL": self.frontend_url,
            }.items():
                if not value.startswith("https://"):
                    raise ValueError(f"{name} deve usar HTTPS em produção.")
