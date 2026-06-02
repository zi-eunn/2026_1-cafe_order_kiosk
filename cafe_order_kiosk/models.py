from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from cafe_order_kiosk.utils import utc_now


class OrderStatus(str, Enum):
    OPEN = "open"
    PAID = "paid"
    CANCELED = "canceled"


@dataclass(frozen=True)
class MenuItem:
    id: int
    name: str
    price: int
    category: str | None = None
    description: str | None = None
    is_available: bool = True
    
# MenuOption 클래스
@dataclass(frozen=True)
class MenuOption:
    name: str
    extra_price: int


@dataclass
class OrderItem:
    menu_item_id: int
    name: str
    unit_price: int
    quantity: int
    # 기존 문자열 리스트에서 객체 리스트로 변경
    options: list[MenuOption] = field(default_factory=list)

    @property
    def line_total(self) -> int:
        # 금액 계산
        options_total = sum(opt.extra_price for opt in self.options)
        return (self.unit_price + options_total) * self.quantity


@dataclass(frozen=True)
class Payment:
    method: str
    amount: int
    paid_at: datetime


@dataclass
class Order:
    id: int
    items: list[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.OPEN
    created_at: datetime = field(default_factory=utc_now)
    paid_at: datetime | None = None
    canceled_at: datetime | None = None
    note: str | None = None
    payment: Payment | None = None

    @property
    def total(self) -> int:
        return sum(item.line_total for item in self.items)
