import unittest

from tests.config import ROOT


class BackendArchitectureTests(unittest.TestCase):
    def test_real_django_apps_are_installed_and_routed(self):
        settings = (ROOT / "backend/config/settings.py").read_text(encoding="utf-8")
        urls = (ROOT / "backend/config/urls.py").read_text(encoding="utf-8")
        for app in ("accounts", "organizations", "subscriptions", "work", "finance", "portal", "core"):
            with self.subTest(app=app):
                self.assertIn(f'"apps.{app}"', settings)
        for prefix in ("api/auth/", "api/organizations/", "api/", "health/"):
            with self.subTest(prefix=prefix):
                self.assertIn(f'path("{prefix}"', urls)

    def test_critical_api_contracts_have_backend_implementations(self):
        contracts = {
            "apps/accounts/urls.py": ("login/", "refresh/", "logout/", "me/"),
            "apps/work/urls.py": ("clients", "projects", "tasks", "dashboard/"),
            "apps/finance/urls.py": ("expenses", "revenues", "invoices", "reports/"),
            "apps/portal/urls.py": ("notifications", "client-portal/dashboard/"),
            "apps/organizations/urls.py": ("members/", "team-chat/"),
        }
        for relative, fragments in contracts.items():
            source = (ROOT / "backend" / relative).read_text(encoding="utf-8")
            for fragment in fragments:
                with self.subTest(file=relative, endpoint=fragment):
                    self.assertIn(fragment, source)

    def test_every_model_app_has_migrations(self):
        for app in ("accounts", "organizations", "subscriptions", "work", "finance", "portal"):
            migrations = list((ROOT / "backend/apps" / app / "migrations").glob("[0-9]*.py"))
            with self.subTest(app=app):
                self.assertTrue(migrations, f"{app} não possui migrations versionadas")

    def test_mercado_pago_is_mocked_by_existing_backend_tests(self):
        finance_tests = (ROOT / "backend/apps/finance/tests.py").read_text(encoding="utf-8")
        subscription_tests = (ROOT / "backend/apps/subscriptions/tests.py").read_text(encoding="utf-8")
        self.assertIn('@patch("apps.finance.payments.get_pix_service")', finance_tests)
        self.assertIn('@patch("apps.payments.mercado_pago.requests.request")', subscription_tests)
        self.assertNotIn("stripe", (finance_tests + subscription_tests).lower())
