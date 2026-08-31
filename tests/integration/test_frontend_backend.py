import unittest

from tests.config import ROOT


class FrontendBackendContractTests(unittest.TestCase):
    def test_frontend_services_match_backend_resources(self):
        frontend = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "frontend/src").rglob("*.ts*")
        )
        backend = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "backend/apps").rglob("urls.py")
        )
        pairs = {
            "/auth/login/": "login/",
            "/organizations/": 'path("",',
            "/dashboard/": "dashboard/",
            "/projects/": 'register("projects"',
            "/clients/": 'register("clients"',
            "/tasks/": 'register("tasks"',
            "/notifications/unread-count/": 'register("notifications"',
            "/finance/dashboard/": "finance/dashboard/",
            "/reports/": "reports/",
        }
        for frontend_path, backend_fragment in pairs.items():
            with self.subTest(endpoint=frontend_path):
                self.assertIn(frontend_path, frontend)
                self.assertIn(backend_fragment, backend)

    def test_notification_polling_endpoint_and_transport_are_connected(self):
        hooks = (ROOT / "frontend/src/features/notifications/hooks.ts").read_text(encoding="utf-8")
        portal_urls = (ROOT / "backend/apps/portal/urls.py").read_text(encoding="utf-8")
        portal_views = (ROOT / "backend/apps/portal/views.py").read_text(encoding="utf-8")
        self.assertIn("/notifications/unread-count/", hooks)
        self.assertIn("refetchInterval: 30000", hooks)
        self.assertIn('register("notifications"', portal_urls)
        self.assertIn("def unread_count", portal_views)
