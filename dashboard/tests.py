from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import InstructorProfile, User
from catalog.models import Course
from core.models import ContactMessage
from tests_support import json_request, make_course, make_paid_enrollment, make_user


class AdminApiPermissionMatrixTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = make_user(email="dash-student@example.com", phone="09120000401")
        self.instructor = make_user(
            email="dash-instructor@example.com",
            phone="09120000402",
            role=User.Role.INSTRUCTOR,
        )
        self.admin = make_user(
            email="dash-admin@example.com",
            phone="09120000403",
            role=User.Role.ADMIN,
        )
        self.course = make_course(code="DASH-101", slug="dashboard-course", instructor=self.instructor)
        self.message = ContactMessage.objects.create(
            name="مهمان",
            email="guest@example.com",
            subject="موضوع تست",
            message="پیام تست معتبر برای داشبورد مدیریت.",
        )

    def test_anonymous_student_and_instructor_cannot_use_admin_api(self):
        endpoints = [
            ("get", "/api/v1/admin/stats", None),
            ("get", "/api/v1/admin/users", None),
            ("patch", f"/api/v1/admin/users/{self.student.id}", {"is_active": False}),
            ("patch", f"/api/v1/admin/courses/{self.course.id}/status", {"is_active": False}),
            ("patch", f"/api/v1/admin/messages/{self.message.id}", {"status": "READ"}),
        ]
        for user in (None, self.student, self.instructor):
            if user:
                self.client.force_login(user)
            for method, path, payload in endpoints:
                with self.subTest(role=getattr(user, "role", "anonymous"), method=method, path=path):
                    response = self.client.get(path) if method == "get" else json_request(self.client, method, path, payload)
                    self.assertIn(response.status_code, (401, 403))
            self.client.logout()

    def test_admin_can_open_all_dashboard_pages_and_stats(self):
        self.client.force_login(self.admin)
        for route in ("dashboard_home", "dashboard_users", "dashboard_courses", "dashboard_orders", "dashboard_messages"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        stats = self.client.get("/api/v1/admin/stats")
        self.assertEqual(stats.status_code, 200)
        self.assertIn("revenue", stats.json())


class AdminUserMutationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user(
            email="manager@example.com",
            phone="09120000411",
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)
        self.student = make_user(email="managed@example.com", phone="09120000412")

    def patch_user(self, user, payload):
        return json_request(self.client, "patch", f"/api/v1/admin/users/{user.id}", payload)

    def test_empty_or_invalid_user_update_is_rejected(self):
        self.assertEqual(self.patch_user(self.student, {}).status_code, 400)
        self.assertEqual(self.patch_user(self.student, {"role": "INVALID"}).status_code, 400)

    def test_admin_can_promote_student_to_instructor_and_profile_is_created(self):
        response = self.patch_user(self.student, {"role": User.Role.INSTRUCTOR})
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, User.Role.INSTRUCTOR)
        self.assertTrue(InstructorProfile.objects.filter(user=self.student).exists())

    def test_instructor_with_course_cannot_be_demoted_to_student(self):
        self.patch_user(self.student, {"role": User.Role.INSTRUCTOR})
        make_course(code="TEACH-101", slug="teach-course", instructor=self.student)
        response = self.patch_user(self.student, {"role": User.Role.STUDENT})
        self.assertEqual(response.status_code, 409)

    def test_instructor_with_active_course_cannot_be_deactivated(self):
        self.patch_user(self.student, {"role": User.Role.INSTRUCTOR})
        course = make_course(code="TEACH-202", slug="teach-active-course", instructor=self.student)
        response = self.patch_user(self.student, {"is_active": False})
        self.assertEqual(response.status_code, 409)
        course.is_active = False
        course.save(update_fields=["is_active"])
        response = self.patch_user(self.student, {"is_active": False})
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_deactivate_or_demote_self(self):
        self.assertEqual(self.patch_user(self.admin, {"is_active": False}).status_code, 400)
        self.assertEqual(self.patch_user(self.admin, {"role": User.Role.STUDENT}).status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertEqual(self.admin.role, User.Role.ADMIN)

    def test_superuser_cannot_be_changed_from_custom_dashboard(self):
        root = User.objects.create_superuser(
            email="root@example.com",
            password="StrongPass123!",
            first_name="مدیر",
            last_name="ارشد",
            phone="09120000413",
        )
        self.assertEqual(self.patch_user(root, {"is_active": False}).status_code, 400)
        self.assertEqual(self.patch_user(root, {"role": User.Role.STUDENT}).status_code, 400)
        root.refresh_from_db()
        self.assertTrue(root.is_active)
        self.assertEqual(root.role, User.Role.ADMIN)

    def test_role_change_updates_staff_flag(self):
        response = self.patch_user(self.student, {"role": User.Role.ADMIN})
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_staff)
        response = self.patch_user(self.student, {"role": User.Role.STUDENT})
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_staff)


class AdminCourseAndMessageMutationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user(
            email="admin-actions@example.com",
            phone="09120000421",
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)
        self.course = make_course(code="ACTION-101", slug="action-course")
        self.message = ContactMessage.objects.create(
            name="کاربر",
            email="user@example.com",
            subject="پیام مدیریتی",
            message="این پیام برای بررسی تغییر وضعیت ساخته شده است.",
        )

    def test_course_status_toggle(self):
        response = json_request(
            self.client,
            "patch",
            f"/api/v1/admin/courses/{self.course.id}/status",
            {"is_active": False},
        )
        self.assertEqual(response.status_code, 200)
        self.course.refresh_from_db()
        self.assertFalse(self.course.is_active)

    def test_message_status_validation_and_update(self):
        invalid = json_request(
            self.client,
            "patch",
            f"/api/v1/admin/messages/{self.message.id}",
            {"status": "INVALID"},
        )
        self.assertEqual(invalid.status_code, 400)
        valid = json_request(
            self.client,
            "patch",
            f"/api/v1/admin/messages/{self.message.id}",
            {"status": ContactMessage.Status.READ},
        )
        self.assertEqual(valid.status_code, 200)
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, ContactMessage.Status.READ)

    def test_missing_resources_return_404_not_500(self):
        self.assertEqual(
            json_request(self.client, "patch", "/api/v1/admin/users/999999", {"is_active": False}).status_code,
            404,
        )
        self.assertEqual(
            json_request(self.client, "patch", "/api/v1/admin/courses/999999/status", {"is_active": False}).status_code,
            404,
        )
        self.assertEqual(
            json_request(self.client, "patch", "/api/v1/admin/messages/999999", {"status": "READ"}).status_code,
            404,
        )


class InstructorDashboardAggregationTests(TestCase):
    def test_revenue_is_not_multiplied_by_enrollment_join(self):
        instructor = make_user(
            email="aggregation-instructor@example.com",
            phone="09120000431",
            role=User.Role.INSTRUCTOR,
        )
        course = make_course(
            code="AGG-101",
            slug="aggregation-course",
            price=1_000_000,
            instructor=instructor,
        )
        first = make_user(email="agg-one@example.com", phone="09120000432")
        second = make_user(email="agg-two@example.com", phone="09120000433")
        make_paid_enrollment(first, course)
        make_paid_enrollment(second, course)

        self.client.force_login(instructor)
        response = self.client.get(reverse("instructor_dashboard"))
        self.assertEqual(response.status_code, 200)
        annotated = list(response.context["courses"])
        self.assertEqual(len(annotated), 1)
        self.assertEqual(annotated[0].students_count, 2)
        self.assertEqual(annotated[0].revenue, 2_000_000)
        self.assertEqual(response.context["students_count"], 2)
        self.assertEqual(response.context["sales_count"], 2)
