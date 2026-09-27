"""COD fraud shield: score a buyer's phone number from their order history."""

from django.db.models import Count, Q

from ..models import Order


def normalize_phone(phone):
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if digits.startswith("880"):
        digits = digits[2:]
    return digits


def is_valid_bd_mobile(phone):
    p = normalize_phone(phone)
    return len(p) == 11 and p.startswith("01") and p[2] in "3456789"


def risk_score(phone, total=0, payment_method="cod"):
    """Return (score 0–100, reasons list).

    Uses shared history across all stores on the platform — the network effect that
    makes the fraud shield better as more sellers join.
    """
    phone = normalize_phone(phone)
    reasons = []
    score = 0
    if not is_valid_bd_mobile(phone):
        return 90, ["Phone number is not a valid Bangladeshi mobile number"]

    stats = Order.objects.filter(shipping_phone=phone).aggregate(
        total=Count("id"),
        delivered=Count("id", filter=Q(status=Order.Status.DELIVERED)),
        failed=Count("id", filter=Q(status__in=[Order.Status.RETURNED, Order.Status.CANCELLED])),
    )
    if stats["total"] == 0:
        score += 20
        reasons.append("First order on the network")
    else:
        fail_rate = stats["failed"] / stats["total"]
        score += round(fail_rate * 70)
        if stats["failed"]:
            reasons.append(f"{stats['failed']} of {stats['total']} past orders returned or cancelled")
        if stats["delivered"] >= 3:
            score -= 15
            reasons.append(f"{stats['delivered']} successful deliveries")
    if payment_method == "cod" and total >= 5000:
        score += 15
        reasons.append("High-value cash-on-delivery order")
    if payment_method != "cod":
        score -= 20
        reasons.append("Prepaid order")
    return max(0, min(100, score)), reasons
