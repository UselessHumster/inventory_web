
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from inventory_web.companies.models import Company


class CompanyApiKeyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="pass12345")
        self.company = Company.objects.create(name="Test Company")
        self.client.force_login(self.user)
        self.url = reverse("companies:company_update", args=[self.company.pk])

    def test_api_key_is_generated_and_can_be_regenerated(self):
        response = self.client.post(self.url, {"regenerate_api_key": "1"})

        self.assertRedirects(response, self.url)
        self.company.refresh_from_db()
        first_key = self.company.api_key
        self.assertTrue(first_key)

        response = self.client.get(self.url)
        self.assertContains(response, first_key)

        self.client.post(self.url, {"regenerate_api_key": "1"})
        self.company.refresh_from_db()
        self.assertNotEqual(first_key, self.company.api_key)
