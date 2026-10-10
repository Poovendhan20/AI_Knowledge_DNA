import os
import sys
import unittest
import json

tests_dir = os.path.dirname(os.path.abspath(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from test_base import BaseTestCase


class TestAuthSecurity(BaseTestCase):
    """
    Comprehensive tests for Authentication, Authorization, JWT tokens,
    and user isolation.
    """

    def test_register_success(self):
        """Valid registration creates user and returns JWT token"""
        res = self.client.post(
            "/api/auth/register",
            json={"name": "Alice Wonderland", "email": "alice@study.edu", "password": "securepassword123"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], "alice@study.edu")
        self.assertEqual(data["user"]["name"], "Alice Wonderland")

    def test_register_missing_fields(self):
        """Registration fails if name, email, or password missing"""
        # Missing name
        res = self.client.post("/api/auth/register", json={"email": "a@a.com", "password": "password"})
        self.assertEqual(res.status_code, 400)
        # Missing email
        res = self.client.post("/api/auth/register", json={"name": "Bob", "password": "password"})
        self.assertEqual(res.status_code, 400)
        # Missing password
        res = self.client.post("/api/auth/register", json={"name": "Bob", "email": "b@b.com"})
        self.assertEqual(res.status_code, 400)
        # Short password (< 6)
        res = self.client.post("/api/auth/register", json={"name": "Bob", "email": "b@b.com", "password": "123"})
        self.assertEqual(res.status_code, 400)

    def test_register_duplicate_email(self):
        """Registering duplicate email returns 409 Conflict"""
        self.create_user(name="Alice", email="duplicate@study.edu", password="password123")
        res = self.client.post(
            "/api/auth/register",
            json={"name": "Duplicate Alice", "email": "duplicate@study.edu", "password": "newpassword123"}
        )
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("already exists", data.get("message", "").lower())

    def test_login_success(self):
        """Login with correct credentials returns 200 and token"""
        self.create_user(name="Charlie Brown", email="charlie@peanuts.com", password="snoopy123")
        res = self.client.post(
            "/api/auth/login",
            json={"email": "charlie@peanuts.com", "password": "snoopy123"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertEqual(data["user"]["email"], "charlie@peanuts.com")

    def test_login_invalid_password(self):
        """Login with incorrect password returns 401"""
        self.create_user(name="Charlie", email="charlie@peanuts.com", password="correct_password")
        res = self.client.post(
            "/api/auth/login",
            json={"email": "charlie@peanuts.com", "password": "wrong_password"}
        )
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data.get("success"))

    def test_login_nonexistent_user(self):
        """Login with non-existent email returns 401"""
        res = self.client.post(
            "/api/auth/login",
            json={"email": "nobody@nonexistent.org", "password": "some_password"}
        )
        self.assertEqual(res.status_code, 401)

    def test_get_current_user_me(self):
        """GET /api/auth/me returns current user info with valid JWT"""
        user = self.create_user(name="Dana Scully", email="scully@fbi.gov", password="thetruthisoutthere")
        headers = self.auth_headers(user["id"])
        res = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data["user"]["email"], "scully@fbi.gov")

    def test_protected_route_without_token(self):
        """Protected routes reject requests without Authorization header"""
        res = self.client.get("/api/auth/me")
        self.assertIn(res.status_code, [401, 422])

    def test_protected_route_invalid_token(self):
        """Protected routes reject requests with invalid/tampered token"""
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        res = self.client.get("/api/auth/me", headers=headers)
        self.assertIn(res.status_code, [401, 422])


if __name__ == "__main__":
    unittest.main()
