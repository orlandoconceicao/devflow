import unittest

from tests.config import TestConfig
from tests.utils import http_request

CONFIG = TestConfig.from_env()


@unittest.skipUnless(CONFIG.run_smoke, "Smoke remoto desabilitado")
class ProductionSmokeTests(unittest.TestCase):
    def test_backend_health_and_protected_endpoints_exist(self):
        status, _, _ = http_request(CONFIG, f"{CONFIG.backend_url}/health/")
        self.assertEqual(status, 200)
        for endpoint in (
            "/api/auth/me/", "/api/organizations/", "/api/dashboard/",
            "/api/notifications/unread-count/", "/api/projects/", "/api/clients/",
        ):
            with self.subTest(endpoint=endpoint):
                status, _, _ = http_request(CONFIG, f"{CONFIG.backend_url}{endpoint}")
                self.assertIn(status, {401, 403}, f"Endpoint ausente ou resposta inesperada: {status}")

    def test_production_cors_preflight(self):
        status, headers, _ = http_request(
            CONFIG,
            f"{CONFIG.backend_url}/api/dashboard/",
            method="OPTIONS",
            headers={
                "Origin": CONFIG.frontend_url,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type,x-organization-id",
            },
        )
        normalized = {key.lower(): value for key, value in headers.items()}
        self.assertEqual(status, 200)
        self.assertEqual(normalized.get("access-control-allow-origin"), CONFIG.frontend_url)
        allowed = normalized.get("access-control-allow-headers", "").lower()
        self.assertIn("x-organization-id", allowed, "CORS: x-organization-id não permitido")

    def test_frontend_direct_routes_do_not_return_404(self):
        for route in ("/", "/login", "/dashboard", "/projects", "/tasks", "/clients", "/settings"):
            with self.subTest(route=route):
                status, _, body = http_request(CONFIG, f"{CONFIG.frontend_url}{route}")
                self.assertEqual(status, 200)
                self.assertNotIn(b"404: NOT_FOUND", body)

    def test_write_methods_are_blocked_by_test_client(self):
        with self.assertRaises(RuntimeError):
            http_request(CONFIG, f"{CONFIG.backend_url}/api/organizations/", method="POST")
