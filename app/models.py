# ============================================================
# JIRA TASK 2 — MEMBER 2
# Title: Product Catalog & Cart Engine (Business Logic)
# File: app/models.py
# ============================================================

from dataclasses import dataclass
from typing import List, Optional
from .database import (
    get_all_products_db, get_product_by_id_db,
    get_product_by_barcode_db, search_products_db
)


@dataclass
class Product:
    """Represents a single product in the store catalog."""
    id: str
    name: str
    category: str
    price: float
    barcode: str
    stock: int
    image_emoji: str = "📦"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "barcode": self.barcode,
            "stock": self.stock,
            "image_emoji": self.image_emoji,
        }

    @classmethod
    def from_db(cls, data: dict):
        """Create Product from database row"""
        return cls(
            id=data['id'],
            name=data['name'],
            category=data['category'],
            price=data['price'],
            barcode=data['barcode'],
            stock=data['stock'],
            image_emoji=data.get('image_emoji', '📦')
        )


@dataclass
class CartItem:
    """One line item in the shopping cart."""
    product: Product
    quantity: int
    discount_percent: float = 0.0

    @property
    def unit_price(self) -> float:
        return round(self.product.price * (1 - self.discount_percent / 100), 2)

    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)

    def to_dict(self):
        return {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_percent": self.discount_percent,
            "line_total": self.line_total,
        }


# ─────────────────────────────────────────────────────────────
# PRODUCT CATALOG FUNCTIONS (Now from Database)
# ─────────────────────────────────────────────────────────────


def get_all_products() -> List[dict]:
    """Get all products from database"""
    products_data = get_all_products_db()
    return [Product.from_db(p).to_dict() for p in products_data]


def get_product_by_id(pid: str) -> Optional[Product]:
    """Get product by ID"""
    data = get_product_by_id_db(pid)
    return Product.from_db(data) if data else None


def get_product_by_barcode(barcode: str) -> Optional[Product]:
    """Get product by barcode"""
    data = get_product_by_barcode_db(barcode)
    return Product.from_db(data) if data else None


def search_products(query: str) -> List[dict]:
    """Search products"""
    results = search_products_db(query)
    return [Product.from_db(p).to_dict() for p in results]


# ─────────────────────────────────────────────────────────────
# CART ENGINE
# ─────────────────────────────────────────────────────────────

class Cart:
    """Shopping cart — holds items and computes totals."""

    def __init__(self, tax_rate: float = 0.18):
        self.items: List[CartItem] = []
        self.tax_rate = tax_rate
        self.global_discount_percent: float = 0.0

    def add_item(self, product: Product, quantity: int = 1,
                 discount: float = 0.0):
        """Add or update item in cart."""
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self.items.append(
            CartItem(product=product, quantity=quantity,
                     discount_percent=discount))

    def remove_item(self, product_id: str):
        self.items = [i for i in self.items if i.product.id != product_id]

    def update_quantity(self, product_id: str, quantity: int):
        for item in self.items:
            if item.product.id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                return

    def clear(self):
        self.items = []
        self.global_discount_percent = 0.0

    @property
    def subtotal(self) -> float:
        return round(sum(i.line_total for i in self.items), 2)

    @property
    def global_discount_amount(self) -> float:
        return round(
            self.subtotal * self.global_discount_percent / 100, 2)

    @property
    def taxable_amount(self) -> float:
        return round(
            self.subtotal - self.global_discount_amount, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.taxable_amount * self.tax_rate, 2)

    @property
    def grand_total(self) -> float:
        return round(self.taxable_amount + self.tax_amount, 2)

    @property
    def item_count(self) -> int:
        return sum(i.quantity for i in self.items)

    def to_dict(self) -> dict:
        return {
            "items": [i.to_dict() for i in self.items],
            "subtotal": self.subtotal,
            "global_discount_percent": self.global_discount_percent,
            "global_discount_amount": self.global_discount_amount,
            "taxable_amount": self.taxable_amount,
            "tax_rate_percent": round(self.tax_rate * 100, 1),
            "tax_amount": self.tax_amount,
            "grand_total": self.grand_total,
            "item_count": self.item_count,
        }
