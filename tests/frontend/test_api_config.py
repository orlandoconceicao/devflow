import unittest

from tests.config import ROOT


class FrontendApiConfigurationTests(unittest.TestCase):
    def test_api_base_comes_from_vite_environment(self):
        source = (ROOT / "frontend/src/services/api.ts").read_text(encoding="utf-8")
        self.assertIn("import.meta.env.VITE_API_URL", source)
        self.assertNotIn("localhost:8000", source)

    def test_organization_context_has_dedicated_vitest_coverage(self):
        test_source = (ROOT / "frontend/src/services/api.test.ts").read_text(encoding="utf-8")
        for case in ("/auth/login/", "/auth/register/", "/auth/refresh/", "/dashboard/"):
            self.assertIn(case, test_source)

    def test_package_scripts_match_runner_commands(self):
        package = (ROOT / "frontend/package.json").read_text(encoding="utf-8")
        for script in ('"build"', '"test"', '"lint"'):
            self.assertIn(script, package)
