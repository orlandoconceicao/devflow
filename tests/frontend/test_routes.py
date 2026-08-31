import re
import unittest

from tests.config import ROOT


class FrontendRouteTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")

    def test_critical_routes_are_registered(self):
        required = (
            "/", "/login", "/register", "/dashboard", "/clients", "/projects",
            "/tasks", "/time", "/team", "/team/chat", "/finance", "/reports",
            "/settings", "/settings/billing",
        )
        paths = set(re.findall(r'<Route\s+path="([^"]+)"', self.source))
        self.assertTrue(set(required).issubset(paths), sorted(set(required) - paths))

    def test_page_imports_resolve_to_real_modules(self):
        imports = re.findall(r"from './pages/([^']+)'", self.source)
        self.assertTrue(imports)
        for module in imports:
            with self.subTest(module=module):
                self.assertTrue((ROOT / "frontend/src/pages" / f"{module}.tsx").is_file())

    def test_protected_routes_use_application_layout(self):
        self.assertIn("<Route element={<Protected />}>", self.source)
        layout = (ROOT / "frontend/src/layouts/AppLayout.tsx").read_text(encoding="utf-8")
        self.assertIn("<Outlet />", layout)

    def test_spa_deployment_rewrite_exists(self):
        vercel = (ROOT / "frontend/vercel.json").read_text(encoding="utf-8")
        self.assertIn('"destination": "/index.html"', vercel)
