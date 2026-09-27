"""Order placement shared by the storefront checkout and manual (Messenger/WhatsApp) orders."""

from decimal import Decimal

from django.db import transaction
from django.db.models import F

from ..models import Coupon, Customer, Order, OrderItem, Product
from .risk import risk_score


class OutOfStock(Exception):
    pass


def delivery_fee(store, inside_dhaka):
    return Decimal(store.delivery_fee_dhaka if inside_dhaka else store.delivery_fee_outside)


def quote(store, items, inside_dhaka, payment_method, phone, coupon=None):
    """Price an order before it is placed. items: [(product, qty, variant)]."""
    subtotal = sum((p.price * q for p, q, _ in items), Decimal(0))
    fee = delivery_fee(store, inside_dhaka)
    discount = coupon.discount_for(subtotal) if coupon else Decimal(0)
    total = max(Decimal(0), subtotal + fee - discount)
    score, reasons = risk_score(phone, total, payment_method)
    advance = fee if payment_method == "cod" and score >= store.advance_threshold else Decimal(0)
    return {
        "subtotal": subtotal, "delivery_fee": fee, "discount": discount, "total": total,
        "risk_score": score, "risk_reasons": reasons, "advance_required": advance,
    }


@transaction.atomic
def place_order(store, *, name, phone, address, city, inside_dhaka, payment_method, items,
                email="", note="", coupon=None, source="store", otp_verified=False, transaction_id=""):
    products = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=[p.pk for p, _, _ in items], store=store)}
    locked = []
    for product, qty, variant in items:
        fresh = products.get(product.pk)
        if not fresh or not fresh.is_active or fresh.stock < qty:
            raise OutOfStock(f"Sorry, only {fresh.stock if fresh else 0} left of “{product.title}”.")
        locked.append((fresh, qty, variant))

    if coupon:
        coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)
        ok, _ = coupon.is_valid_for(sum((p.price * q for p, q, _ in locked), Decimal(0)))
        if not ok:
            coupon = None

    q = quote(store, locked, inside_dhaka, payment_method, phone, coupon)
    customer, created = Customer.objects.get_or_create(
        store=store, phone=phone, defaults={"name": name, "email": email, "address": address, "city": city},
    )
    if not created:
        customer.name, customer.address, customer.city = name, address, city
        if email:
            customer.email = email
    if otp_verified:
        customer.phone_verified = True
    customer.save()

    payment_status = Order.PaymentStatus.UNPAID
    if transaction_id:
        payment_status = Order.PaymentStatus.PARTIAL if payment_method == "cod" else Order.PaymentStatus.PAID

    order = Order.objects.create(
        store=store, customer=customer, payment_method=payment_method, payment_status=payment_status,
        transaction_id=transaction_id, shipping_name=name, shipping_phone=phone, shipping_address=address,
        shipping_city=city, inside_dhaka=inside_dhaka, subtotal=q["subtotal"], delivery_fee=q["delivery_fee"],
        discount=q["discount"], total=q["total"], advance_required=q["advance_required"], coupon=coupon,
        risk_score=q["risk_score"], otp_verified=otp_verified, source=source, note=note,
    )
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=p, title=p.title, variant=v, unit_price=p.price, quantity=qty)
        for p, qty, v in locked
    ])
    for p, qty, _ in locked:
        Product.objects.filter(pk=p.pk).update(stock=F("stock") - qty)
    if coupon:
        Coupon.objects.filter(pk=coupon.pk).update(times_used=F("times_used") + 1)
    Customer.objects.filter(pk=customer.pk).update(loyalty_points=F("loyalty_points") + int(q["total"] // 100))
    store.extend_trial_for_milestones()
    return order
