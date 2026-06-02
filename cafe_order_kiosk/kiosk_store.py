from __future__ import annotations

from collections.abc import Iterable

from cafe_order_kiosk.models import MenuItem, MenuOption, Order, OrderItem, OrderStatus, Payment
from cafe_order_kiosk.utils import utc_now

DEFAULT_MENU: tuple[MenuItem, ...] = (
    MenuItem(id=1, name="Americano", price=3500, category="coffee"),
    MenuItem(id=2, name="Latte", price=4000, category="coffee"),
    MenuItem(id=3, name="Cappuccino", price=4200, category="coffee"),
    MenuItem(id=4, name="Cold Brew", price=4500, category="coffee"),
    MenuItem(id=5, name="Matcha Latte", price=4800, category="tea"),
    MenuItem(id=6, name="Chamomile Tea", price=3800, category="tea"),
    MenuItem(id=7, name="Lemonade", price=4200, category="juice"),
    MenuItem(id=8, name="Butter Croissant", price=3500, category="bakery"),
    MenuItem(id=9, name="Blueberry Muffin", price=3200, category="bakery"),
    MenuItem(id=10, name="Cheesecake", price=5200, category="dessert"),
)

# 기본 옵션 데이터
DEFAULT_OPTIONS: tuple[MenuOption, ...] = (
    MenuOption(name="샷추가", extra_price=500),
    MenuOption(name="사이즈업", extra_price=1000),
    MenuOption(name="디카페인", extra_price=300),
    MenuOption(name="얼음많이", extra_price=0),
    MenuOption(name="얼음적게", extra_price=0),
)

class KioskStore:
    # menu_options 인자
    def __init__(self, menu_items: Iterable[MenuItem] | None = None, menu_options: Iterable[MenuOption] | None = None) -> None:
        self._menu: dict[int, MenuItem] = {item.id: item for item in (menu_items or [])}
        self._options: dict[str, MenuOption] = {opt.name: opt for opt in (menu_options or [])}
        self._orders: dict[int, Order] = {}
        self._next_order_id = 1

    @classmethod
    def with_default_menu(cls) -> KioskStore:
        # 옵션 초기화
        return cls(menu_items=DEFAULT_MENU, menu_options=DEFAULT_OPTIONS)

    def list_options(self) -> list[MenuOption]:
        return list(self._options.values())
    
    def list_menu(self, only_available: bool = True) -> list[MenuItem]:
        items: Iterable[MenuItem] = self._menu.values()
        if only_available:
            items = [item for item in items if item.is_available]
        return sorted(items, key=lambda item: item.id)

    def get_menu_item(self, menu_item_id: int) -> MenuItem | None:
        return self._menu.get(menu_item_id)

    def create_order(self, note: str | None = None) -> Order:
        order_id = self._next_order_id
        self._next_order_id += 1

        order = Order(id=order_id, note=note)
        self._orders[order_id] = order
        return order

    def list_orders(self, status: OrderStatus | None = None) -> list[Order]:
        orders: Iterable[Order] = self._orders.values()
        if status is not None:
            orders = [order for order in orders if order.status == status]
        return sorted(orders, key=lambda order: order.id)

    def get_order(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def add_item(
        self,
        order_id: int,
        menu_item_id: int,
        quantity: int,
        options: list[str] | None = None,
    ) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        menu_item = self._menu.get(menu_item_id)
        if menu_item is None:
            raise ValueError("Menu item not found")
        if not menu_item.is_available:
            raise ValueError("Menu item is not available")

        valid_options = []
        if options:
            for opt_name in options:
                opt = self._options.get(opt_name)
                if opt is None:
                    raise ValueError(f"알 수 없는 옵션입니다: {opt_name}")
                valid_options.append(opt)

        order_item = OrderItem(
            menu_item_id=menu_item.id,
            name=menu_item.name,
            unit_price=menu_item.price,
            quantity=quantity,
            options=valid_options,
        )
        order.items.append(order_item)
        return order

    def remove_item(self, order_id: int, line_index: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if line_index < 1 or line_index > len(order.items):
            raise ValueError("Line item not found")

        order.items.pop(line_index - 1)
        return order

    def cancel_order(self, order_id: int) -> Order:
        order = self._require_order(order_id)
        if order.status is OrderStatus.CANCELED:
            return order
        if order.status is OrderStatus.PAID:
            raise ValueError("Paid order cannot be canceled")

        order.status = OrderStatus.CANCELED
        order.canceled_at = utc_now()
        return order

    def pay_order(self, order_id: int, method: str, amount: int) -> Order:
        order = self._require_order(order_id)
        if order.status is not OrderStatus.OPEN:
            raise ValueError("Order is not open")
        if not order.items:
            raise ValueError("Order has no items")
        if amount != order.total:
            raise ValueError("Payment amount does not match total")

        order.status = OrderStatus.PAID
        order.paid_at = utc_now()
        order.payment = Payment(method=method, amount=amount, paid_at=order.paid_at)
        return order

    def _require_order(self, order_id: int) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise ValueError("Order not found")
        return order
