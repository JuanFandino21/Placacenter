from decimal import Decimal

SESSION_KEY = "cart"

class Cart:
    """
    Carrito simple en sesión:
    {
      "producto_id_str": {"qty": int, "precio": "12.34"}
    }
    """
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(SESSION_KEY)
        if cart is None:
            cart = {}
            self.session[SESSION_KEY] = cart
        self.cart = cart

    def save(self):
        self.session[SESSION_KEY] = self.cart
        self.session.modified = True

    def add(self, product_id: int, precio, qty: int = 1):
        pid = str(int(product_id))
        item = self.cart.get(pid, {"qty": 0, "precio": str(precio)})
        # si cambia el precio, actualizamos
        item["precio"] = str(precio)
        item["qty"] = int(item["qty"]) + int(qty)
        if item["qty"] <= 0:
            self.cart.pop(pid, None)
        else:
            self.cart[pid] = item
        self.save()

    def dec(self, product_id: int, qty: int = 1):
        pid = str(int(product_id))
        if pid in self.cart:
            self.cart[pid]["qty"] = int(self.cart[pid]["qty"]) - int(qty)
            if self.cart[pid]["qty"] <= 0:
                self.cart.pop(pid, None)
            self.save()

    def remove(self, product_id: int):
        pid = str(int(product_id))
        self.cart.pop(pid, None)
        self.save()

    def empty(self):
        self.cart = {}
        self.save()

    def items(self):
        # devuelve (pid, item_dict)
        return list(self.cart.items())

    def subtotal(self):
        total = Decimal("0")
        for _, it in self.cart.items():
            total += Decimal(it["precio"]) * Decimal(int(it["qty"]))
        return float(total)
