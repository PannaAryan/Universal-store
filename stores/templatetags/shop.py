from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

THUMBS = ["", "alt", "gold", "sky"]


@register.filter
def taka(value):
    """Format a number as Bangladeshi taka: ৳1,450."""
    try:
        return f"৳{intcomma(int(round(float(value))))}"
    except (TypeError, ValueError):
        return "৳0"


@register.filter
def thumb_class(obj):
    return THUMBS[(getattr(obj, "pk", 0) or 0) % len(THUMBS)]


@register.simple_tag(takes_context=True)
def query(context, **kwargs):
    """Rebuild the current querystring with some keys replaced (for pagination/filters)."""
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ""):
            params.pop(k, None)
        else:
            params[k] = v
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
