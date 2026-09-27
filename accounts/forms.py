from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm

User = get_user_model()


class SignupForm(forms.Form):
    full_name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder": "Your full name", "autocomplete": "name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"placeholder": "01XXXXXXXXX", "autocomplete": "tel", "inputmode": "tel"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "At least 8 characters", "autocomplete": "new-password"}),
        help_text="Use 8+ characters with a mix of letters and numbers.",
    )
    agree = forms.BooleanField(label="I agree to the Terms of service and Privacy policy")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Try signing in.")
        return email

    def clean_phone(self):
        phone = "".join(ch for ch in self.cleaned_data["phone"] if ch.isdigit())
        if len(phone) < 10:
            raise forms.ValidationError("Enter a valid mobile number.")
        return phone

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        if password:
            temp = User(username=cleaned.get("email", ""), email=cleaned.get("email", ""))
            try:
                password_validation.validate_password(password, temp)
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return cleaned

    def save(self):
        data = self.cleaned_data
        first, _, last = data["full_name"].strip().partition(" ")
        user = User.objects.create_user(
            username=data["email"], email=data["email"], password=data["password"],
            first_name=first, last_name=last,
        )
        user.profile.phone = data["phone"]
        user.profile.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password", strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Your password", "autocomplete": "current-password"}),
    )
