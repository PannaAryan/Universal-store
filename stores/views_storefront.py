from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, OTPForm, TrackForm
from .models import Coupon, Order, Product, Store
from .services import orders as order_service
from .services import otp
from .services.cart import Cart
from .services.risk import normalize_phone


def _store(slug):
    store = get_object_or_404(Store.objects.select_related("plan"), slug=slug)
    if not store.is_live:
        raise Http404("This store is not live yet.")
    return store


def _ctx(request, store, **extra):
    return {"store": store, "cart_count": Cart(request, store).count(), **extra}


def home(request, slug):
    store = _store(slug)
    qs = store.products.filter(is_active=True).select_related("category")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("c", "")
    sort = request.GET.get("sort", "new")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(title_bn__icontains=q) | Q(tags__icontains=q))
    if cat:
        qs = qs.filter(category__slug=cat)
    qs = {"low": qs.order_by("price"), "high": qs.order_by("-price")}.get(sort, qs)
    page = Paginator(qs, 12).get_page(request.GET.get("page"))
    categories = store.categories.filter(products__is_active=True).distinct()
    return render(request, "storefront/home.html", _ctx(
        request, store, page=page, q=q, cat=cat, sort=sort, categories=categories,
    ))


def product(request, slug, product_slug):
    store = _store(slug)
    item = get_object_or_404(Product, store=store, slug=product_slug, is_active=True)
    related = store.products.filter(is_active=True, category=item.category).exclude(pk=item.pk)[:4]
    return render(request, "storefront/product.html", _ctx(request, store, product=item, related=related))


@require_POST
def cart_add(request, slug):
    store = _store(slug)
    item = get_object_or_404(Product, store=store, pk=request.POST.get("product"), is_active=True)
    try:
        qty = max(1, int(request.POST.get("quantity", 1)))
    except ValueError:
        qty = 1
    variant = request.POST.get("variant", "")
    if variant and variant not in item.variant_list:
        variant = ""
    if item.stock <= 0:
        messages.error(request, "Sorry, this item is out of stock.")
        return redirect(item.get_absolute_url())
    Cart(request, store).add(item, qty, variant)
    messages.success(request, f"Added “{item.title}” to your bag.")
    if request.POST.get("buy_now"):
        return redirect("storefront:checkout", slug=store.slug)
    return redirect("storefront:cart", slug=store.slug)


def cart(request, slug):
    store = _store(slug)
    c = Cart(request, store)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update":
            for key in list(c.data):
                val = request.POST.get(f"qty_{key}")
                if val is not None:
                    try:
                        c.update(key, int(val))
                    except ValueError:
                        pass
        elif action == "remove":
            c.update(request.POST.get("key", ""), 0)
        elif action == "coupon":
            code = request.POST.get("code", "").upper().strip()
            coupon = Coupon.objects.filter(store=store, code=code).first()
            ok, err = coupon.is_valid_for(c.subtotal()) if coupon else (False, "That code isn't valid.")
            if ok:
                request.session[f"coupon_{store.pk}"] = coupon.pk
                messages.success(request, f"Coupon {coupon.code} applied — {coupon.label}.")
            else:
                request.session.pop(f"coupon_{store.pk}", None)
                messages.error(request, err)
        return redirect("storefront:cart", slug=store.slug)
    lines = c.lines()
    subtotal = c.subtotal()
    coupon = _coupon(request, store, subtotal)
    discount = coupon.discount_for(subtotal) if coupon else 0
    return render(request, "storefront/cart.html", _ctx(
        request, store, lines=lines, subtotal=subtotal, coupon=coupon, discount=discount,
        total_before_delivery=subtotal - discount,
    ))


def _coupon(request, store, subtotal):
    pk = request.session.get(f"coupon_{store.pk}")
    coupon = Coupon.objects.filter(pk=pk, store=store).first() if pk else None
    if coupon and coupon.is_valid_for(subtotal)[0]:
        return coupon
    return None


def checkout(request, slug):
    store = _store(slug)
    c = Cart(request, store)
    lines = c.lines()
    if not lines:
        messages.info(request, "Your bag is empty.")
        return redirect("storefront:home", slug=store.slug)
    subtotal = c.subtotal()
    coupon = _coupon(request, store, subtotal)
    items = [(line["product"], line["quantity"], line["variant"]) for line in lines]
    form = CheckoutForm(request.POST or None, store=store, initial=request.session.get("checkout_details"))
    if request.method == "POST" and form.is_valid():
        details = form.cleaned_data
        request.session["checkout_details"] = {**details, "inside_dhaka": "1" if details["inside_dhaka"] else "0"}
        if store.otp_checkout:
            code = otp.issue(request.session, details["phone"], store.name)
            if settings.OTP_SHOW_ON_SCREEN:
                request.session["otp_hint"] = code
            return redirect("storefront:verify", slug=store.slug)
        return _finalize(request, store, c, items, coupon, otp_verified=False)
    quote = order_service.quote(store, items, True, "cod", "", coupon)
    quote["base"] = quote["total"] - quote["delivery_fee"]
    return render(request, "storefront/checkout.html", _ctx(
        request, store, form=form, lines=lines, quote=quote, coupon=coupon,
    ))


def verify(request, slug):
    store = _store(slug)
    details = request.session.get("checkout_details")
    c = Cart(request, store)
    lines = c.lines()
    if not details or not lines:
        return redirect("storefront:checkout", slug=store.slug)
    subtotal = c.subtotal()
    coupon = _coupon(request, store, subtotal)
    items = [(line["product"], line["quantity"], line["variant"]) for line in lines]
    inside = details["inside_dhaka"] == "1"
    quote = order_service.quote(store, items, inside, details["payment_method"], details["phone"], coupon)
    prepaid = details["payment_method"] in {"bkash", "nagad"}
    needs_txn = bool(quote["advance_required"]) or prepaid
    form = OTPForm(request.POST or None, advance_required=needs_txn)
    if request.method == "POST":
        if request.POST.get("action") == "resend":
            code = otp.issue(request.session, details["phone"], store.name)
            if settings.OTP_SHOW_ON_SCREEN:
                request.session["otp_hint"] = code
            messages.info(request, "We've sent a new code.")
            return redirect("storefront:verify", slug=store.slug)
        if form.is_valid():
            ok, err = otp.verify(request.session, details["phone"], form.cleaned_data["code"])
            if ok:
                return _finalize(request, store, c, items, coupon, otp_verified=True,
                                 transaction_id=form.cleaned_data.get("transaction_id", ""))
            form.add_error("code", err)
    return render(request, "storefront/verify.html", _ctx(
        request, store, form=form, details=details, quote=quote, needs_txn=needs_txn, prepaid=prepaid,
        otp_hint=request.session.get("otp_hint"),
    ))


def _finalize(request, store, cart, items, coupon, otp_verified, transaction_id=""):
    d = request.session["checkout_details"]
    try:
        order = order_service.place_order(
            store, name=d["name"], phone=d["phone"], email=d.get("email", ""), address=d["address"],
            city=d["city"], inside_dhaka=d["inside_dhaka"] == "1", payment_method=d["payment_method"],
            note=d.get("note", ""), items=items, coupon=coupon, otp_verified=otp_verified,
            transaction_id=transaction_id,
        )
    except order_service.OutOfStock as exc:
        messages.error(request, str(exc))
        return redirect("storefront:cart", slug=store.slug)
    cart.clear()
    for key in ("checkout_details", "otp_hint", f"coupon_{store.pk}"):
        request.session.pop(key, None)
    request.session.setdefault("my_orders", [])
    request.session["my_orders"] = request.session["my_orders"][-9:] + [order.number]
    return redirect("storefront:order", slug=store.slug, number=order.number)


def order(request, slug, number):
    store = _store(slug)
    if number not in request.session.get("my_orders", []):
        return redirect("storefront:track", slug=store.slug)
    placed = get_object_or_404(Order, store=store, number=number)
    return render(request, "storefront/order.html", _ctx(request, store, order=placed))


def track(request, slug):
    store = _store(slug)
    form = TrackForm(request.GET or None)
    found = None
    if request.GET and form.is_valid():
        found = Order.objects.filter(
            store=store, number=form.cleaned_data["number"].strip().lstrip("#"),
            shipping_phone=normalize_phone(form.cleaned_data["phone"]),
        ).first()
        if not found:
            form.add_error(None, "We couldn't find an order with that number and phone.")
    return render(request, "storefront/track.html", _ctx(request, store, form=form, order=found))
