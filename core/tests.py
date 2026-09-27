from django.test import TestCase, override_settings
from django.urls import reverse

from .models import FAQ, Lead, NewsletterSubscriber, Plan


class MarketingPagesTests(TestCase):
    def test_pages_render(self):
        for name in ["home", "features", "snap", "pricing", "compare", "about", "investors", "contact", "help", "status"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(f"core:{name}")).status_code, 200)

    def test_plans_and_faqs_are_seeded(self):
        self.assertEqual(list(Plan.objects.values_list("slug", flat=True)), ["shuru", "growth", "business", "scale"])
        self.assertTrue(FAQ.objects.exists())
        growth = Plan.objects.get(slug="growth")
        self.assertEqual(growth.price_annual, 7990)

    def test_unknown_legal_page_is_404(self):
        self.assertEqual(self.client.get("/legal/unknown/").status_code, 404)

    def test_contact_creates_lead(self):
        r = self.client.post(reverse("core:contact"), {"kind": "migration", "name": "Rina Das", "phone": "01711-000000"})
        self.assertRedirects(r, reverse("core:contact") + "?sent=1")
        lead = Lead.objects.get()
        self.assertEqual((lead.kind, lead.phone), ("migration", "01711000000"))

    def test_newsletter_rejects_offsite_redirect(self):
        r = self.client.post(reverse("core:newsletter"), {"email": "A@B.com", "next": "https://evil.example/"})
        self.assertRedirects(r, reverse("core:home"))
        self.assertTrue(NewsletterSubscriber.objects.filter(email="a@b.com").exists())

    @override_settings(AI_ENABLED=False)
    def test_snap_demo_is_rate_limited(self):
        url = reverse("core:snap_demo")
        for _ in range(5):
            r = self.client.post(url, {"title": "cotton saree", "price": "1450", "category": "Fashion"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json()["listing"]["source"], "template")
        self.assertEqual(self.client.post(url, {"title": "x", "price": "1"}).status_code, 429)
