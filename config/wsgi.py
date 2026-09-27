"""WSGI entry point. Vercel's Python runtime looks for a module-level ``app``."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()


def _prepare_vercel_database():
    """Apply migrations on cold start and seed the demo store if the database is empty."""
    from django.conf import settings
    from django.core.management import call_command

    if not settings.ON_VERCEL or os.environ.get("AUTO_MIGRATE", "1") != "1":
        return
    call_command("migrate", interactive=False, verbosity=0)
    from stores.models import Store

    if not Store.objects.exists():
        call_command("seed_demo", verbosity=0)


_prepare_vercel_database()

app = application
