from django.contrib import admin

from .models import FAQ, Lead, NewsletterSubscriber, Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_monthly", "is_featured", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "phone", "business_name", "handled", "created_at")
    list_filter = ("kind", "handled")
    search_fields = ("name", "phone", "email", "business_name")
    list_editable = ("handled",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")
