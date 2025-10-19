# core/cart.py
from decimal import Decimal

SESSION_KEY = "cart"


class Cart:
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[SESSION_KEY] = cart
        self._cart = cart

    # Helpers
    def _save(self):
        self.session[SESSION_KEY] = self._cart
        self.session.modified = True

    def items(self):
        """Iterar items como (pid, data)."""
        return self._cart.items()

    # Operaciones 
    def add(self, product_id, price, qty=1):
        pid = str(product_id)
        if pid not in self._cart:
            self._cart[pid] = {"qty": 0, "precio": str(price)}
        self._cart[pid]["qty"] += int(qty)
        self._save()

    def dec(self, product_id, qty=1):
        pid = str(product_id)
        if pid in self._cart:
            self._cart[pid]["qty"] -= int(qty)
            if self._cart[pid]["qty"] <= 0:
                del self._cart[pid]
            self._save()

    def remove(self, product_id):
        pid = str(product_id)
        if pid in self._cart:
            del self._cart[pid]
            self._save()

    def empty(self):
        self._cart = {}
        self._save()

    def subtotal(self) -> Decimal:
        total = Decimal("0")
        for _, item in self._cart.items():
            total += Decimal(item["precio"]) * int(item["qty"])
        return total
