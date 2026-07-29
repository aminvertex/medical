import json

from django.contrib.auth.models import AnonymousUser
from django.core import checks
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from ninja.errors import HttpError

from tests_support import DEFAULT_PASSWORD, csrf_token, json_request, make_user
from .models import User
from .security import RoleSessionAuth, admin_auth, instructor_auth, student_auth


class RoleSessionAuthTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.student = make_user(email="student@example.com", phone="09120000001")
        self.instructor = make_user(
            email="instructor@example.com",
            phone="09120000002",
            role=User.Role.INSTRUCTOR,
        )
        self.admin = make_user(
            email="admin@example.com",
            phone="09120000003",
            role=User.Role.ADMIN,
        )

    def request_for(self, user):
        request = self.factory.get("/")
        request.user = user
        return request

    def test_custom_auth_initializes_parent_csrf_metadata(self):
        for auth in (student_auth, instructor_auth, admin_auth):
            self.assertTrue(hasattr(auth, "csrf"))
            self.assertTrue(auth.csrf)
            self.assertEqual(auth.param_name, "sessionid")

    def test_student_auth_accepts_all_application_roles(self):
        for user in (self.student, self.instructor, self.admin):
            self.assertEqual(student_auth.authenticate(self.request_for(user), "key"), user)

    def test_instructor_auth_rejects_student_with_403(self):
        with self.assertRaises(HttpError) as ctx:
            instructor_auth.authenticate(self.request_for(self.student), "key")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_admin_auth_rejects_non_admin_with_403(self):
        with self.assertRaises(HttpError) as ctx:
            admin_auth.authenticate(self.request_for(self.instructor), "key")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_anonymous_auth_returns_none(self):
        request = self.request_for(AnonymousUser())
        self.assertIsNone(student_auth.authenticate(request, ""))

    def test_django_system_check_validates_auth_objects(self):
        errors = [error for error in checks.run_checks() if error.id.startswith("accounts.E")]
        self.assertEqual(errors, [])

    def test_subclass_signature_accepts_cookie_key(self):
        auth = RoleSessionAuth(User.Role.STUDENT)
        self.assertEqual(auth.authenticate(self.request_for(self.student), "session-cookie"), self.student)


class AuthenticationApiTests(TestCase):
    register_payload = {
        "first_name": "کاربر",
        "last_name": "آزمایشی",
        "email": "new@example.com",
        "phone": "09121112233",
        "password": DEFAULT_PASSWORD,
        "password_confirm": DEFAULT_PASSWORD,
    }

    def setUp(self):
        self.client = Client()

    def test_public_registration_creates_student_hashes_password_and_logs_in(self):
        response = json_request(self.client, "post", "/api/v1/auth/register", self.register_payload)
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password(DEFAULT_PASSWORD))
        self.assertNotEqual(user.password, DEFAULT_PASSWORD)
        self.assertNotIn("password", response.json().get("user", {}))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_registration_normalizes_email_phone_and_names(self):
        payload = {**self.register_payload, "email": "  NEW@EXAMPLE.COM  ", "phone": "09121112233"}
        response = json_request(self.client, "post", "/api/v1/auth/register", payload)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="new@example.com", phone="09121112233").exists())

    def test_registration_validation_matrix_returns_json_not_500(self):
        cases = [
            ({"first_name": "ا"}, 400),
            ({"last_name": "ب"}, 400),
            ({"email": "not-email"}, 400),
            ({"phone": "abc"}, 400),
            ({"phone": "123"}, 400),
            ({"password_confirm": "DifferentPass123!"}, 400),
            ({"password": "12345678", "password_confirm": "12345678"}, 400),
        ]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                payload = {**self.register_payload, **changes}
                payload["email"] = f"{abs(hash(str(changes)))}@example.com" if "email" not in changes else changes["email"]
                payload["phone"] = f"09{abs(hash(str(changes))) % 10**9:09d}" if "phone" not in changes else changes["phone"]
                response = json_request(self.client, "post", "/api/v1/auth/register", payload)
                self.assertEqual(response.status_code, expected)
                self.assertEqual(response.headers["Content-Type"], "application/json; charset=utf-8")
                self.assertIn("detail", response.json())

    def test_duplicate_email_and_phone_are_rejected(self):
        make_user(email="taken@example.com", phone="09120000020")
        email_response = json_request(
            self.client,
            "post",
            "/api/v1/auth/register",
            {**self.register_payload, "email": "TAKEN@example.com", "phone": "09120000021"},
        )
        phone_response = json_request(
            self.client,
            "post",
            "/api/v1/auth/register",
            {**self.register_payload, "email": "other@example.com", "phone": "09120000020"},
        )
        self.assertEqual(email_response.status_code, 409)
        self.assertEqual(phone_response.status_code, 409)

    def test_login_success_failure_and_inactive_account(self):
        user = make_user(email="login@example.com", phone="09120000022")
        ok = json_request(self.client, "post", "/api/v1/auth/login", {"email": user.email, "password": DEFAULT_PASSWORD})
        self.assertEqual(ok.status_code, 200)
        self.client.logout()
        wrong = json_request(self.client, "post", "/api/v1/auth/login", {"email": user.email, "password": "WrongPass123!"})
        self.assertEqual(wrong.status_code, 401)
        user.is_active = False
        user.save(update_fields=["is_active"])
        inactive = json_request(self.client, "post", "/api/v1/auth/login", {"email": user.email, "password": DEFAULT_PASSWORD})
        self.assertEqual(inactive.status_code, 403)

    def test_me_and_logout_require_session(self):
        anon_me = self.client.get("/api/v1/auth/me")
        self.assertIn(anon_me.status_code, (401, 403))
        user = make_user(email="me@example.com", phone="09120000023")
        self.client.force_login(user)
        me = self.client.get("/api/v1/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["email"], user.email)
        logout = json_request(self.client, "post", "/api/v1/auth/logout")
        self.assertEqual(logout.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)


class CsrfProtectionTests(TestCase):
    def test_public_registration_rejects_missing_csrf_and_accepts_valid_token(self):
        client = Client(enforce_csrf_checks=True)
        payload = AuthenticationApiTests.register_payload
        rejected = json_request(client, "post", "/api/v1/auth/register", payload)
        self.assertEqual(rejected.status_code, 403)
        token = csrf_token(client, reverse("auth_page"))
        accepted = json_request(client, "post", "/api/v1/auth/register", payload, csrf_token=token)
        self.assertEqual(accepted.status_code, 201)

    def test_authenticated_mutation_enforces_csrf(self):
        from tests_support import make_course

        client = Client(enforce_csrf_checks=True)
        user = make_user(email="csrf@example.com", phone="09120000024")
        course = make_course(code="CSRF-101", slug="csrf-course")
        client.force_login(user)
        rejected = json_request(client, "post", "/api/v1/store/cart/items", {"course_id": course.id})
        self.assertEqual(rejected.status_code, 403)
        token = csrf_token(client)
        accepted = json_request(
            client,
            "post",
            "/api/v1/store/cart/items",
            {"course_id": course.id},
            csrf_token=token,
        )
        self.assertEqual(accepted.status_code, 201)


class RolePageMatrixTests(TestCase):
    def setUp(self):
        self.student = make_user(email="role-student@example.com", phone="09120000031")
        self.instructor = make_user(
            email="role-instructor@example.com",
            phone="09120000032",
            role=User.Role.INSTRUCTOR,
        )
        self.admin = make_user(
            email="role-admin@example.com",
            phone="09120000033",
            role=User.Role.ADMIN,
        )

    def test_anonymous_protected_pages_redirect_to_login(self):
        for name in ("account_overview", "my_orders", "my_courses", "my_favorites", "cart", "checkout", "dashboard_home", "instructor_dashboard"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("auth_page"), response.url)

    def test_student_instructor_admin_page_access_matrix(self):
        cases = [
            (self.student, "dashboard_home", 403),
            (self.student, "instructor_dashboard", 403),
            (self.instructor, "instructor_dashboard", 200),
            (self.instructor, "dashboard_home", 403),
            (self.admin, "dashboard_home", 200),
            (self.admin, "instructor_dashboard", 200),
        ]
        for user, route, expected in cases:
            with self.subTest(user=user.role, route=route):
                self.client.force_login(user)
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, expected)
                self.client.logout()


class UserManagerTests(TestCase):
    def test_normal_user_cannot_be_created_as_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="bad@example.com",
                password=DEFAULT_PASSWORD,
                first_name="Bad",
                last_name="User",
                is_superuser=True,
            )

    def test_superuser_must_have_admin_role(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="root@example.com",
                password=DEFAULT_PASSWORD,
                first_name="Root",
                last_name="User",
                role=User.Role.STUDENT,
            )
