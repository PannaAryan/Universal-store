from django.conf import settings


def brand(request):
    return {"BRAND": settings.BRAND}
