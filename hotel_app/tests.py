from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class HotelAPITests(APITestCase):
    """
    Full CRUD tests for all endpoints defined in hotel_app/urls_api.py
    """

    def setUp(self):
        # Create a test user & authenticate
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # ===========================
    # 1. Authentication
    # ===========================
    def test_login(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": "testuser", "password": "password123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    # ===========================
    # 2. Users
    # ===========================
    def test_user_crud(self):
        # Create
        response = self.client.post(
            "/api/users/", {"username": "newuser", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_id = response.data["id"]

        # Read
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/users/{user_id}/", {"username": "updateduser"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/users/{user_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 3. Departments
    # ===========================
    def test_department_crud(self):
        # Create
        response = self.client.post("/api/departments/", {"name": "Housekeeping"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dept_id = response.data["id"]

        # Read
        response = self.client.get("/api/departments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/departments/{dept_id}/", {"name": "Reception"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/departments/{dept_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 4. User Groups
    # ===========================
    def test_user_group_crud(self):
        # Create
        response = self.client.post("/api/user-groups/", {"name": "Admins"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group_id = response.data["id"]

        # Read
        response = self.client.get("/api/user-groups/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/user-groups/{group_id}/", {"name": "Employees"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/user-groups/{group_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 5. Locations
    # ===========================
    def test_location_crud(self):
        # Create
        response = self.client.post("/api/locations/", {"name": "Lobby"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loc_id = response.data["id"]

        # Read
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/locations/{loc_id}/", {"name": "Main Lobby"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/locations/{loc_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 6. Complaints
    # ===========================
    def test_complaint_crud(self):
        # Create
        response = self.client.post("/api/complaints/", {"title": "AC not working"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint_id = response.data["id"]

        # Read
        response = self.client.get("/api/complaints/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/complaints/{complaint_id}/", {"status": "Resolved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/complaints/{complaint_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 7. Vouchers
    # ===========================
    def test_voucher_crud(self):
        # Create
        response = self.client.post("/api/vouchers/", {"guest": self.user.id,"valid_until": "2025-12-31"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        voucher_id = response.data["id"]

        # Read
        response = self.client.get("/api/vouchers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/vouchers/{voucher_id}/", {"redeemed": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/vouchers/{voucher_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 8. Reviews
    # ===========================
    def test_review_crud(self):
        # Create
        response = self.client.post("/api/reviews/", {"comment": "Great stay!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review_id = response.data["id"]

        # Read
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/reviews/{review_id}/", {"rating": 4}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/reviews/{review_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 9. Dashboards (GET only)
    # ===========================
    def test_dashboard_overview(self):
        response = self.client.get(reverse("dashboard-overview"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_complaints(self):
        response = self.client.get(reverse("dashboard-complaints"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_reviews(self):
        response = self.client.get(reverse("dashboard-reviews"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
