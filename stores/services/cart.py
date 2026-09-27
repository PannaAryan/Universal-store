"""Session cart, one per store."""

from decimal import Decimal

from ..models import Product


class Cart:
    def __init__(self, request, store):
        self.session = request.session
        self.store = store
        self.key = f"cart_{store.pk}"
        self.data = self.session.get(self.key, {})

    def _save(self):
        self.session[self.key] = self.data
        self.session.modified = True

    @staticmethod
    def _line_key(product_id, variant):
        return f"{product_id}:{variant}"

    def add(self, product, quantity=1, variant=""):
        key = self._line_key(product.pk, variant)
        current = self.data.get(key, {"q": 0})["q"]
        self.data[key] = {"q": min(current + quantity, max(product.stock, 0))}
        if self.data[key]["q"] <= 0:
            self.data.pop(key)
        self._save()

    def update(self, key, quantity):
        if key in self.data:
            if quantity <= 0:
                self.data.pop(key)
            else:
                self.data[key]["q"] = quantity
            self._save()

    def clear(self):
        self.session.pop(self.key, None)
        self.session.modified = True

    def lines(self):
        ids = {int(k.split(":")[0]) for k in self.data}
        products = {p.pk: p for p in Product.objects.filter(pk__in=ids, store=self.store, is_active=True)}
        result = []
        for key, item in self.data.items():
            pid, _, variant = key.partition(":")
            product = products.get(int(pid))
            if not product:
                continue
            qty = min(item["q"], product.stock)
            if qty <= 0:
                continue
            result.append({
                "key": key, "product": product, "variant": variant,
                "quantity": qty, "line_total": product.price * qty,
            })
        return result

    def count(self):
        return sum(item["q"] for item in self.data.values())

    def subtotal(self):
        return sum((line["line_total"] for line in self.lines()), Decimal(0))
