from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import Plan

from .models import Coupon, Customer, Order, Product, Store
from .services.ai import generate_listing
from .services import otp
from .services.risk import risk_score

User = get_user_model()


def make_store(**kw):
    user = User.objects.create_user("s@x.com", "s@x.com", "pass12345!")
    store = Store.objects.create(owner=user, name="Test Shop", plan=Plan.objects.get(slug="growth"), **kw)
    return user, store


class SignupOnboardingTests(TestCase):
    def test_signup_then_onboarding_creates_store(self):
        r = self.client.post(reverse("accounts:signup"), {
            "full_name": "Ayesha Khan", "email": "ayesha@example.com", "phone": "01711223344",
            "password": "Str0ng-pass!", "agree": "on",
        })
        self.assertRedirects(r, reverse("dashboard:onboarding"))
        self.assertRedirects(self.client.get(reverse("dashboard:home")), reverse("dashboard:onboarding"))
        r = self.client.post(reverse("dashboard:onboarding"), {
            "name": "Ayesha Crafts", "slug": "ayesha-crafts", "category": "Handicrafts", "tagline": "",
            "phone": "01711223344", "brand_color": "#1E7F5C", "theme": "bazaar", "plan": "business",
        })
        self.assertRedirects(r, reverse("dashboard:product_add"))
        store = Store.objects.get(slug="ayesha-crafts")
        self.assertEqual(store.plan.slug, "business")
        self.assertEqual(store.trial_days_left, 29)

    def test_email_login(self):
        User.objects.create_user("u1", "login@example.com", "Str0ng-pass!")
        r = self.client.post(reverse("accounts:login"), {"username": "LOGIN@example.com", "password": "Str0ng-pass!"})
        self.assertEqual(r.status_code, 302)


class AIListingTests(TestCase):
    @override_settings(AI_ENABLED=False)
    def test_template_listing_has_all_fields(self):
        listing = generate_listing("handloom cotton saree", 1450, "Fashion")
        self.assertEqual(listing["source"], "template")
        self.assertEqual(listing["title"], "Handloom Cotton Saree")
        self.assertIn("৳1,450", listing["description_en"])
        self.assertLessEqual(len(listing["seo_title"]), 70)
        self.assertIn("saree", listing["tags"])

    @override_settings(AI_ENABLED=False)
    def test_ai_generate_endpoint_respects_quota(self):
        user, store = make_store()
        store.plan = Plan.objects.get(slug="shuru")
        store.save()
        self.client.force_login(user)
        for i in range(20):
            Product.objects.create(store=store, title=f"P{i}", price=10, ai_generated=True)
        r = self.client.post(reverse("dashboard:ai_generate"), {"title": "x", "price": "10"})
        self.assertEqual(r.status_code, 402)


class RiskTests(TestCase):
    def test_invalid_phone_is_high_risk(self):
        self.assertEqual(risk_score("12345")[0], 90)

    def test_history_drives_score(self):
        _, store = make_store()
        cust = Customer.objects.create(store=store, name="A", phone="01711111111")
        for status in ["returned", "cancelled", "returned"]:
            Order.objects.create(store=store, customer=cust, status=status, shipping_name="A",
                                 shipping_phone="01711111111", shipping_address="x", shipping_city="Dhaka")
        self.assertGreaterEqual(risk_score("01711111111")[0], 60)
        self.assertEqual(risk_score("01811111111")[0], 20)


class CheckoutFlowTests(TestCase):
    def _post_checkout(self, data):
        codes = []
        real = otp.issue

        def spy(*a, **kw):
            codes.append(real(*a, **kw))
            return codes[-1]

        otp.issue = spy
        try:
            r = self.client.post(reverse("storefront:checkout", args=[self.store.slug]), data)
        finally:
            otp.issue = real
        return r, (codes[-1] if codes else None)

    def setUp(self):
        _, self.store = make_store(delivery_fee_dhaka=60, delivery_fee_outside=120)
        self.product = Product.objects.create(store=self.store, title="Kurti", price=1000, stock=5, variants="S, M")
        self.coupon = Coupon.objects.create(store=self.store, code="save10", percent_off=10)

    def _fill_cart(self):
        url = reverse("storefront:cart_add", args=[self.store.slug])
        self.client.post(url, {"product": self.product.pk, "quantity": 2, "variant": "M"})
        self.client.post(reverse("storefront:cart", args=[self.store.slug]), {"action": "coupon", "code": "SAVE10"})

    def _details(self, **kw):
        data = {"name": "Nusrat", "phone": "01912345678", "address": "Mirpur 10", "city": "Dhaka",
                "inside_dhaka": "1", "payment_method": "cod"}
        data.update(kw)
        return data

    def test_full_checkout_with_otp(self):
        self._fill_cart()
        r, code = self._post_checkout(self._details())
        self.assertRedirects(r, reverse("storefront:verify", args=[self.store.slug]))
        self.assertNotIn(code, str(self.client.session["checkout_otp"]))
        verify = reverse("storefront:verify", args=[self.store.slug])
        r = self.client.post(verify, {"code": "000000" if code != "000000" else "111111"})
        self.assertContains(r, "doesn")
        r = self.client.post(verify, {"code": code})
        order = Order.objects.get()
        self.assertRedirects(r, reverse("storefront:order", args=[self.store.slug, order.number]))
        self.assertEqual(order.subtotal, Decimal(2000))
        self.assertEqual(order.discount, Decimal(200))
        self.assertEqual(order.total, Decimal(1860))
        self.assertTrue(order.otp_verified)
        self.assertEqual(order.items.get().variant, "M")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.times_used, 1)
        self.assertEqual(self.client.get(reverse("storefront:cart", args=[self.store.slug])).context["lines"], [])

    def test_high_risk_cod_requires_advance(self):
        self.store.advance_threshold = 10
        self.store.save()
        self._fill_cart()
        _, code = self._post_checkout(self._details())
        verify = reverse("storefront:verify", args=[self.store.slug])
        r = self.client.post(verify, {"code": code})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.client.post(verify, {"code": code, "transaction_id": "9HX7K2LM"})
        order = Order.objects.get()
        self.assertEqual(order.advance_required, Decimal(60))
        self.assertEqual(order.payment_status, "partial")
        self.assertEqual(order.due_on_delivery, Decimal(1800))

    def test_order_page_needs_session_and_track_needs_phone(self):
        self.store.otp_checkout = False
        self.store.save()
        self._fill_cart()
        self.client.post(reverse("storefront:checkout", args=[self.store.slug]), self._details())
        order = Order.objects.get()
        other = self.client_class()
        r = other.get(reverse("storefront:order", args=[self.store.slug, order.number]))
        self.assertRedirects(r, reverse("storefront:track", args=[self.store.slug]))
        track = reverse("storefront:track", args=[self.store.slug])
        self.assertIsNone(other.get(track, {"number": order.number, "phone": "01700000000"}).context["order"])
        self.assertEqual(other.get(track, {"number": order.number, "phone": "01912345678"}).context["order"], order)

    def test_cannot_oversell(self):
        url = reverse("storefront:cart_add", args=[self.store.slug])
        self.client.post(url, {"product": self.product.pk, "quantity": 50})
        self.assertEqual(self.client.get(reverse("storefront:cart", args=[self.store.slug])).context["lines"][0]["quantity"], 5)


class DashboardTests(TestCase):
    def setUp(self):
        self.user, self.store = make_store()
        self.client.force_login(self.user)
        self.product = Product.objects.create(store=self.store, title="Tote", price=450, stock=10)

    def test_other_sellers_cannot_see_orders(self):
        other = User.objects.create_user("o@x.com", "o@x.com", "pass12345!")
        other_store = Store.objects.create(owner=other, name="Other")
        cust = Customer.objects.create(store=other_store, name="B", phone="01711111112")
        order = Order.objects.create(store=other_store, customer=cust, shipping_name="B", shipping_phone="01711111112",
                                     shipping_address="x", shipping_city="Dhaka")
        self.assertEqual(self.client.get(reverse("dashboard:order_detail", args=[order.number])).status_code, 404)

    def test_manual_order_and_cancel_restocks(self):
        r = self.client.post(reverse("dashboard:order_add"), {
            "source": "messenger", "name": "Rafiq", "phone": "01678901234", "address": "Zindabazar",
            "city": "Sylhet", "payment_method": "cod", "product_1": self.product.pk, "qty_1": 3,
        })
        order = Order.objects.get()
        self.assertRedirects(r, reverse("dashboard:order_detail", args=[order.number]))
        self.assertEqual(order.total, Decimal(450 * 3 + 120))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.client.post(reverse("dashboard:order_detail", args=[order.number]), {
            "status": "cancelled", "payment_status": "unpaid", "courier": "", "tracking_code": "", "transaction_id": "", "note": "",
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10)

    def test_product_with_orders_is_hidden_not_deleted(self):
        self.client.post(reverse("dashboard:order_add"), {
            "source": "manual", "name": "R", "phone": "01678901234", "address": "a", "city": "Dhaka",
            "inside_dhaka": "on", "payment_method": "cod", "product_1": self.product.pk, "qty_1": 1,
        })
        self.client.post(reverse("dashboard:product_delete", args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_coupon_requires_one_discount_type(self):
        r = self.client.post(reverse("dashboard:coupons"), {"code": "x", "percent_off": 10, "amount_off": 50, "min_order": 0, "is_active": "on"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Coupon.objects.exists())

    def test_billing_plan_change(self):
        self.client.post(reverse("dashboard:billing"), {"plan": "scale", "cycle": "annual"})
        self.store.refresh_from_db()
        self.assertEqual((self.store.plan.slug, self.store.billing_cycle), ("scale", "annual"))
