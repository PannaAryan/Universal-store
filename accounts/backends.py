from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Let sellers sign in with their email address instead of a username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or "@" not in username:
            return None
        User = get_user_model()
        user = User.objects.filter(email__iexact=username).order_by("id").first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
