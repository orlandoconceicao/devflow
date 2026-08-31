import re
import unittest

from tests.config import ROOT
from tests.utils import tracked_files


class SecurityConfigurationTests(unittest.TestCase):
    def test_cors_csrf_and_throttling_are_explicit(self):
        settings = (ROOT / "backend/config/settings.py").read_text(encoding="utf-8")
        self.assertIn('"corsheaders.middleware.CorsMiddleware"', settings)
        self.assertIn('"django.middleware.csrf.CsrfViewMiddleware"', settings)
        self.assertIn('"x-organization-id"', settings)
        self.assertIn('"DEFAULT_THROTTLE_CLASSES"', settings)
        self.assertNotIn("CORS_ALLOW_ALL_ORIGINS = True", settings)

    def test_real_tenant_isolation_is_covered_for_critical_resources(self):
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "backend/apps").rglob("tests.py")
        )
        for resource in ("clients", "projects", "tasks", "expenses", "invoices", "reports"):
            with self.subTest(resource=resource):
                self.assertIn(resource, sources.lower())
        self.assertIn("HTTP_X_ORGANIZATION_ID", sources)
        self.assertIn("HTTP_403_FORBIDDEN", sources)

    def test_environment_files_with_secrets_are_not_tracked(self):
        tracked = {path.relative_to(ROOT).as_posix() for path in tracked_files()}
        forbidden = {
            path
            for path in tracked
            if path.split("/")[-1].startswith(".env") and not path.endswith(".example")
        }
        self.assertEqual(forbidden, set(), f"Arquivos env versionados: {sorted(forbidden)}")
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", gitignore)
        self.assertIn(".env.production", gitignore)

    def test_no_obvious_live_credentials_are_versioned(self):
        patterns = {
            "OpenAI key": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
            "Mercado Pago token": re.compile(r"APP_USR-[A-Za-z0-9_-]{20,}"),
            "JWT": re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
        }
        findings: list[str] = []
        for path in tracked_files():
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ico", ".lock"}:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for kind, pattern in patterns.items():
                if pattern.search(content):
                    findings.append(f"{kind}: {path.relative_to(ROOT)}")
        self.assertEqual(findings, [], "Possíveis segredos encontrados (valores ocultos): " + ", ".join(findings))

    def test_tokens_are_not_logged_by_frontend(self):
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in (ROOT / "frontend/src").rglob("*.ts*")
        )
        unsafe = re.compile(r"console\.(?:log|debug|info|warn|error)\([^\n]*(?:access|refresh|token|wsUrl)", re.I)
        self.assertIsNone(unsafe.search(source))
