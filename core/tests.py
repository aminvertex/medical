from django.test import Client, TestCase
from django.urls import reverse

from tests_support import json_request, make_course, make_user
from .models import ContactMessage, NewsletterSubscription


class PublicPageSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = make_course(code="PAGE-101", slug="page-course")

    def test_every_public_page_renders_without_server_error(self):
        routes = [
            "home",
            "about",
            "team",
            "contact",
            "auth_page",
            "shop",
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
        detail = self.client.get(reverse("course_detail", kwargs={"slug": self.course.slug}))
        self.assertEqual(detail.status_code, 200)

    def test_favicon_and_static_route_do_not_return_application_404(self):
        response = self.client.get("/favicon.ico")
        self.assertIn(response.status_code, (301, 302))
        self.assertIn("/static/assets/", response.url)

    def test_swagger_and_openapi_schema_render(self):
        self.assertEqual(self.client.get("/api/docs").status_code, 200)
        schema = self.client.get("/api/openapi.json")
        self.assertEqual(schema.status_code, 200)
        self.assertIn("paths", schema.json())

    def test_custom_404_page(self):
        response = self.client.get("/route-that-does-not-exist/")
        self.assertEqual(response.status_code, 404)


class ContactApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_valid_guest_message_is_saved(self):
        response = json_request(
            self.client,
            "post",
            "/api/v1/core/contact",
            {
                "name": "مهدی امینی",
                "email": "Mahdi@Example.com",
                "subject": "سؤال درباره دوره",
                "message": "این یک پیام معتبر برای بخش پشتیبانی سامانه است.",
            },
        )
        self.assertEqual(response.status_code, 201)
        message = ContactMessage.objects.get()
        self.assertEqual(message.email, "mahdi@example.com")
        self.assertIsNone(message.user)

    def test_authenticated_message_is_linked_to_user(self):
        user = make_user(email="contact-user@example.com", phone="09120000301")
        self.client.force_login(user)
        response = json_request(
            self.client,
            "post",
            "/api/v1/core/contact",
            {
                "name": "کاربر سامانه",
                "email": user.email,
                "subject": "درخواست پشتیبانی",
                "message": "لطفاً وضعیت سفارش من را بررسی و اعلام کنید.",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.get().user, user)

    def test_contact_validation_matrix(self):
        base = {
            "name": "کاربر معتبر",
            "email": "valid@example.com",
            "subject": "موضوع معتبر",
            "message": "پیام معتبر با طول کافی برای ذخیره شدن.",
        }
        cases = [
            {"name": "ا"},
            {"name": "x" * 161},
            {"email": "invalid"},
            {"subject": "ab"},
            {"subject": "x" * 201},
            {"message": "کوتاه"},
            {"message": "x" * 5001},
        ]
        for changes in cases:
            with self.subTest(changes={k: len(v) if isinstance(v, str) else v for k, v in changes.items()}):
                response = json_request(self.client, "post", "/api/v1/core/contact", {**base, **changes})
                self.assertEqual(response.status_code, 400)
                self.assertIn("detail", response.json())
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_newsletter_is_idempotent_and_reactivates(self):
        first = json_request(self.client, "post", "/api/v1/core/newsletter", {"email": "NEWS@Example.com"})
        second = json_request(self.client, "post", "/api/v1/core/newsletter", {"email": "news@example.com"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(NewsletterSubscription.objects.count(), 1)
        subscription = NewsletterSubscription.objects.get()
        subscription.is_active = False
        subscription.save(update_fields=["is_active"])
        third = json_request(self.client, "post", "/api/v1/core/newsletter", {"email": "news@example.com"})
        self.assertEqual(third.status_code, 200)
        subscription.refresh_from_db()
        self.assertTrue(subscription.is_active)

    def test_invalid_newsletter_email_returns_400(self):
        response = json_request(self.client, "post", "/api/v1/core/newsletter", {"email": "bad-email"})
        self.assertEqual(response.status_code, 400)
