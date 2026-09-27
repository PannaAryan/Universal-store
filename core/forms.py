from django import forms

from . import content
from .models import Lead, NewsletterSubscriber


class LeadForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[("", "Choose a category")] + [(c, c) for c in content.SELLER_CATEGORIES],
        required=False,
    )

    class Meta:
        model = Lead
        fields = ["kind", "name", "phone", "email", "business_name", "facebook_page", "category", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your full name", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "01XXXXXXXXX", "autocomplete": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "business_name": forms.TextInput(attrs={"placeholder": "e.g. Nakshi Threads"}),
            "facebook_page": forms.URLInput(attrs={"placeholder": "https://facebook.com/yourpage"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us what you sell and how you take orders today"}),
        }
        labels = {"kind": "I'd like to", "business_name": "Business name", "facebook_page": "Facebook page (optional)"}

    def clean_phone(self):
        phone = "".join(ch for ch in self.cleaned_data["phone"] if ch.isdigit() or ch == "+")
        if len(phone.lstrip("+")) < 10:
            raise forms.ValidationError("Enter a valid mobile number.")
        return phone


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ["email"]
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "Your email", "aria-label": "Email address"})}

    def validate_unique(self):
        # Re-subscribing is fine; the view uses get_or_create.
        pass


class SnapDemoForm(forms.Form):
    title = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"placeholder": "e.g. Handloom cotton saree"}))
    price = forms.DecimalField(min_value=0, max_digits=10, decimal_places=0, widget=forms.NumberInput(attrs={"placeholder": "1450"}))
    category = forms.ChoiceField(choices=[(c, c) for c in content.SELLER_CATEGORIES], required=False)
    image = forms.ImageField(required=False)
