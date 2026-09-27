from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.shortcuts import redirect, render

from .forms import EmailAuthenticationForm, SignupForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="accounts.backends.EmailBackend")
        plan = request.GET.get("plan")
        if plan:
            request.session["chosen_plan"] = plan
        messages.success(request, "Welcome aboard! Let's set up your store — it takes about 10 minutes.")
        return redirect("dashboard:onboarding")
    return render(request, "accounts/signup.html", {"form": form})


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True
