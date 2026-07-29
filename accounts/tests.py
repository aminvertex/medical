import json

from django.test import Client, TestCase
from django.urls import reverse

from .models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_public_registration_creates_student_and_logs_in(self):
        response = self.client.post(
            "/api/v1/auth/register",
            data=json.dumps(
                {
                    "first_name": "کاربر",
                    "last_name": "آزمایشی",
                    "email": "new@example.com",
                    "phone": "09121112233",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertNotIn("password", response.json().get("user", {}))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_invalid_registration_returns_json_400_instead_of_server_error(self):
        response = self.client.post(
            "/api/v1/auth/register",
            data=json.dumps(
                {
                    "first_name": "کاربر",
                    "last_name": "آزمایشی",
                    "email": "new@example.com",
                    "phone": "09121112233",
                    "password": "StrongPass123!",
                    "password_confirm": "DifferentPass123!",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response["content-type"], "application/json; charset=utf-8")
        self.assertIn("detail", response.json())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email="taken@example.com",
            password="StrongPass123!",
            first_name="A",
            last_name="B",
            phone="09120000000",
        )
        response = self.client.post(
            "/api/v1/auth/register",
            data=json.dumps(
                {
                    "first_name": "C",
                    "last_name": "D",
                    "email": "taken@example.com",
                    "phone": "09120000009",
                    "password": "StrongPass123!",
                    "password_confirm": "StrongPass123!",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)

    def test_student_gets_real_403_on_admin_page_and_api(self):
        student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            first_name="دانشجو",
            last_name="نمونه",
            phone="09120000005",
        )
        self.client.force_login(student)
        page_response = self.client.get(reverse("dashboard_home"))
        api_response = self.client.get("/api/v1/admin/stats")
        self.assertEqual(page_response.status_code, 403)
        self.assertEqual(api_response.status_code, 403)

    def test_anonymous_admin_page_redirects_to_login(self):
        response = self.client.get(reverse("dashboard_home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("auth_page"), response.url)
