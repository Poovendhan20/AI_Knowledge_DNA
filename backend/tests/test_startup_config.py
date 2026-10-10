import os
import sys
import unittest

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase


class TestStartupConfig(BaseTestCase):
    def test_root_endpoint(self):
        """GET / should return 200 and running status"""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("running", data.get("message", "").lower())

    def test_health_check(self):
        """GET /api/health should return 200 with status ok"""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "healthy")

    def test_cors_headers(self):
        """Responses should include standard CORS headers"""
        res = self.client.get("/api/health")
        self.assertIn("Access-Control-Allow-Origin", res.headers)

    def test_404_handler(self):
        """Unknown endpoints should return 404"""
        res = self.client.get("/api/nonexistent_route_404")
        self.assertEqual(res.status_code, 404)

    def test_database_table_metadata(self):
        """Database metadata should define all expected tables"""
        from models import db
        table_names = list(db.metadata.tables.keys())
        expected = ["users", "documents", "subjects", "quizzes", "quiz_attempts", "learning_progress"]
        for t in expected:
            self.assertIn(t, table_names, f"Expected table {t} to be in metadata")


if __name__ == "__main__":
    unittest.main()
