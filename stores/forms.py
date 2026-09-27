from django import forms

from core.content import SELLER_CATEGORIES

from .models import COURIERS, PAYMENT_METHODS, Category, Coupon, Order, Product, Store
from .services.risk import is_valid_bd_mobile, normalize_phone

MAX_IMAGE_MB = 4  # Vercel rejects request bodies over 4.5 MB


def validate_image_size(image):
    if image and hasattr(image, "size") and image.size > MAX_IMAGE_MB * 1024 * 1024:
        raise forms.ValidationError(f"Please upload an image under {MAX_IMAGE_MB} MB.")
    return image


class OnboardingForm(forms.ModelForm):
    category = forms.ChoiceField(choices=[(c, c) for c in SELLER_CATEGORIES])

    class Meta:
        model = Store
        fields = ["name", "slug", "category", "tagline", "phone", "brand_color", "theme"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Nakshi Threads", "data-slug-source": ""}),
            "slug": forms.TextInput(attrs={"placeholder": "nakshi-threads", "data-slug-target": ""}),
            "tagline": forms.TextInput(attrs={"placeholder": "Handwoven sarees from Tangail"}),
            "phone": forms.TextInput(attrs={"placeholder": "01XXXXXXXXX", "inputmode": "tel"}),
            "brand_color": forms.TextInput(attrs={"type": "color"}),
            "theme": forms.RadioSelect,
        }
        labels = {"slug": "Store address", "name": "Store name"}

    def clean_slug(self):
        from django.utils.text import slugify

        slug = slugify(self.cleaned_data["slug"])
        if not slug:
            raise forms.ValidationError("Choose a store address.")
        if slug in {"admin", "www", "app", "api", "dashboard", "help", "status"}:
            raise forms.ValidationError("That address is reserved. Try another.")
        qs = Store.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("That address is taken. Try another.")
        return slug


class StoreSettingsForm(OnboardingForm):
    payments = forms.MultipleChoiceField(choices=PAYMENT_METHODS, widget=forms.CheckboxSelectMultiple, required=True)
    couriers = forms.MultipleChoiceField(choices=COURIERS, widget=forms.CheckboxSelectMultiple, required=True)

    class Meta(OnboardingForm.Meta):
        fields = OnboardingForm.Meta.fields + [
            "logo", "email", "address", "facebook_url", "custom_domain",
            "delivery_fee_dhaka", "delivery_fee_outside", "otp_checkout", "advance_threshold", "is_live",
        ]
        labels = {
            **OnboardingForm.Meta.labels,
            "otp_checkout": "Require OTP verification at checkout",
            "advance_threshold": "Ask for delivery-fee advance at risk score",
            "is_live": "Store is live and accepting orders",
            "custom_domain": "Custom domain",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payments"].initial = self.instance.payment_list
        self.fields["couriers"].initial = self.instance.courier_list
        plan = self.instance.plan
        if not (plan and plan.custom_domain):
            self.fields["custom_domain"].disabled = True
            self.fields["custom_domain"].help_text = "Available on Growth and above."

    def clean_logo(self):
        return validate_image_size(self.cleaned_data.get("logo"))

    def save(self, commit=True):
        store = super().save(commit=False)
        store.enabled_payments = ",".join(self.cleaned_data["payments"])
        store.enabled_couriers = ",".join(self.cleaned_data["couriers"])
        if commit:
            store.save()
        return store


class ProductForm(forms.ModelForm):
    new_category = forms.CharField(max_length=60, required=False, widget=forms.TextInput(attrs={"placeholder": "Or create a new category"}))

    class Meta:
        model = Product
        fields = [
            "image", "title", "title_bn", "category", "price", "compare_at_price", "cost_price", "sku",
            "stock", "low_stock_threshold", "variants", "description_en", "description_bn",
            "highlights", "tags", "seo_title", "seo_description", "is_active", "ai_generated",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Handloom cotton saree"}),
            "description_en": forms.Textarea(attrs={"rows": 5}),
            "description_bn": forms.Textarea(attrs={"rows": 5, "lang": "bn"}),
            "highlights": forms.Textarea(attrs={"rows": 3}),
            "ai_generated": forms.HiddenInput,
            "image": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
            "title_bn": forms.TextInput(attrs={"lang": "bn"}),
        }
        labels = {"compare_at_price": "Compare-at price", "is_active": "Visible in store"}

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.fields["category"].queryset = Category.objects.filter(store=store)
        self.fields["category"].required = False
        self.fields["category"].empty_label = "No category"

    def clean_image(self):
        return validate_image_size(self.cleaned_data.get("image"))

    def clean(self):
        cleaned = super().clean()
        price, compare = cleaned.get("price"), cleaned.get("compare_at_price")
        if price is not None and compare is not None and compare and compare <= price:
            self.add_error("compare_at_price", "Compare-at price should be higher than the price.")
        return cleaned

    def save(self, commit=True):
        product = super().save(commit=False)
        product.store = self.store
        name = self.cleaned_data.get("new_category", "").strip()
        if name:
            product.category, _ = Category.objects.get_or_create(store=self.store, name=name)
        if commit:
            product.save()
        return product


class AIGenerateForm(forms.Form):
    title = forms.CharField(max_length=140, required=False)
    price = forms.DecimalField(min_value=0, max_digits=10, decimal_places=0)
    image = forms.ImageField(required=False)

    def clean_image(self):
        return validate_image_size(self.cleaned_data.get("image"))


class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["status", "payment_status", "courier", "tracking_code", "transaction_id", "note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 3, "placeholder": "Internal note"})}


class ManualOrderForm(forms.Form):
    source = forms.ChoiceField(choices=[("messenger", "Messenger"), ("whatsapp", "WhatsApp"), ("manual", "Phone / in person")])
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"inputmode": "tel", "placeholder": "01XXXXXXXXX"}))
    address = forms.CharField(max_length=240)
    city = forms.CharField(max_length=60, initial="Dhaka")
    inside_dhaka = forms.BooleanField(required=False, initial=True, label="Inside Dhaka")
    payment_method = forms.ChoiceField(choices=PAYMENT_METHODS)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        products = Product.objects.filter(store=store, is_active=True, stock__gt=0)
        for i in range(1, 4):
            self.fields[f"product_{i}"] = forms.ModelChoiceField(
                queryset=products, required=(i == 1), label=f"Item {i}",
                empty_label="Choose a product" if i == 1 else "— none —",
            )
            self.fields[f"qty_{i}"] = forms.IntegerField(min_value=1, initial=1, required=False, label="Qty")

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not is_valid_bd_mobile(phone):
            raise forms.ValidationError("Enter a valid Bangladeshi mobile number (01XXXXXXXXX).")
        return phone

    def items(self):
        for i in range(1, 4):
            product = self.cleaned_data.get(f"product_{i}")
            if product:
                yield product, self.cleaned_data.get(f"qty_{i}") or 1


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ["code", "percent_off", "amount_off", "min_order", "usage_limit", "expires_at", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "EID20", "style": "text-transform:uppercase"}),
            "expires_at": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store

    def clean_code(self):
        code = self.cleaned_data["code"].upper().strip()
        qs = Coupon.objects.filter(store=self.store, code=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("You already have a coupon with this code.")
        return code

    def clean(self):
        cleaned = super().clean()
        pct, amt = cleaned.get("percent_off"), cleaned.get("amount_off")
        if bool(pct) == bool(amt):
            raise forms.ValidationError("Set either a percentage or a fixed amount off, not both.")
        if pct and pct > 90:
            self.add_error("percent_off", "Keep percentage discounts at 90% or less.")
        return cleaned


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Full name"}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "01XXXXXXXXX"}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"placeholder": "Optional, for receipts"}))
    address = forms.CharField(max_length=240, widget=forms.TextInput(attrs={"autocomplete": "street-address", "placeholder": "House, road, area"}))
    city = forms.CharField(max_length=60, widget=forms.TextInput(attrs={"placeholder": "City / district"}))
    inside_dhaka = forms.TypedChoiceField(
        choices=[("1", "Inside Dhaka"), ("0", "Outside Dhaka")], coerce=lambda v: v == "1",
        widget=forms.RadioSelect, initial="1", label="Delivery area",
    )
    payment_method = forms.ChoiceField(widget=forms.RadioSelect, label="Payment")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Delivery instructions (optional)"}))

    def __init__(self, *args, store=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].choices = store.payment_choices
        if store.payment_list:
            self.fields["payment_method"].initial = store.payment_list[0]

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data["phone"])
        if not is_valid_bd_mobile(phone):
            raise forms.ValidationError("Enter a valid Bangladeshi mobile number (01XXXXXXXXX).")
        return phone


class OTPForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={
        "inputmode": "numeric", "autocomplete": "one-time-code", "placeholder": "••••••", "class": "otp-input",
    }))
    transaction_id = forms.CharField(max_length=60, required=False, widget=forms.TextInput(attrs={"placeholder": "e.g. 9HX7K2LM"}))

    def __init__(self, *args, advance_required=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transaction_id"].required = advance_required


class TrackForm(forms.Form):
    number = forms.CharField(max_length=20, label="Order number", widget=forms.TextInput(attrs={"placeholder": "e.g. 2609482913"}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"inputmode": "tel", "placeholder": "01XXXXXXXXX"}))
