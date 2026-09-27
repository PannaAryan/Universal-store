from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from stores.services.ai import generate_listing

from . import content
from .forms import LeadForm, NewsletterForm, SnapDemoForm
from .models import FAQ, NewsletterSubscriber, Plan

SNAP_DEMO_LIMIT = 5


def _pricing_context():
    return {"plans": Plan.objects.all(), "addons": content.PLAN_ADDONS}


def home(request):
    ctx = {
        "c": content,
        "faqs": FAQ.objects.filter(is_published=True)[:6],
        **_pricing_context(),
    }
    return render(request, "core/home.html", ctx)


def features(request):
    return render(request, "core/features.html", {"c": content})


def snap_and_sell(request):
    return render(request, "core/snap.html", {"c": content, "form": SnapDemoForm()})


@require_POST
def snap_demo(request):
    """Public "try it" endpoint for AI Snap & Sell, limited per session."""
    used = request.session.get("snap_demo_used", 0)
    if used >= SNAP_DEMO_LIMIT:
        return JsonResponse(
            {"ok": False, "error": "You've used all free tries. Create a free store to keep going."},
            status=429,
        )
    form = SnapDemoForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    data = form.cleaned_data
    listing = generate_listing(
        title=data["title"], price=data["price"], category=data.get("category") or "", image=data.get("image")
    )
    request.session["snap_demo_used"] = used + 1
    return JsonResponse({"ok": True, "listing": listing, "remaining": SNAP_DEMO_LIMIT - used - 1})


def pricing(request):
    ctx = {"c": content, "faqs": FAQ.objects.filter(is_published=True), **_pricing_context()}
    return render(request, "core/pricing.html", ctx)


def compare(request):
    return render(request, "core/compare.html", {"c": content})


def about(request):
    return render(request, "core/about.html", {"c": content})


def investors(request):
    max_arr = max(p["arr"] for p in content.PROJECTIONS)
    projections = [{**p, "pct": round(p["arr"] / max_arr * 100, 1)} for p in content.PROJECTIONS]
    return render(request, "core/investors.html", {"c": content, "projections": projections})


def contact(request):
    initial_kind = request.GET.get("type", "demo")
    form = LeadForm(request.POST or None, initial={"kind": initial_kind})
    if request.method == "POST" and form.is_valid():
        lead = form.save()
        messages.success(
            request,
            f"Thanks {lead.name.split()[0]}! Our team will call you within one business day.",
        )
        return redirect(reverse("core:contact") + "?sent=1")
    return render(request, "core/contact.html", {"form": form, "sent": request.GET.get("sent")})


def help_center(request):
    faqs = FAQ.objects.filter(is_published=True)
    return render(request, "core/help.html", {"faqs": faqs, "c": content})


def status(request):
    return render(request, "core/status.html", {"components": content.STATUS_COMPONENTS})


def legal(request, page):
    titles = {"terms": "Terms of service", "privacy": "Privacy policy", "refund": "Refund & SLA policy"}
    if page not in titles:
        raise Http404
    return render(request, f"core/legal_{page}.html", {"title": titles[page]})


@require_POST
def newsletter(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        NewsletterSubscriber.objects.get_or_create(email=form.cleaned_data["email"].lower())
        messages.success(request, "You're subscribed. Seller tips are on their way.")
    else:
        messages.error(request, "Please enter a valid email address.")
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("core:home")
    return redirect(next_url)


def not_found(request, exception=None):
    return render(request, "404.html", status=404)
