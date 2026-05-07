from flask import (Blueprint, request, jsonify, session,
                   render_template, redirect, url_for)
import uuid
import datetime
from functools import wraps

from .models import (
    Cart, get_all_products, get_product_by_id,
    get_product_by_barcode, search_products
)
from .database import (
    save_bill_db, get_all_bills_db, get_bill_by_id_db,
    get_daily_stats_db, get_category_sales_db,
    get_top_products_db, get_hourly_sales_db,
    get_bills_by_date_db, create_product_db, delete_product_db
)

main = Blueprint("main", __name__)

# In-memory session carts
_carts: dict = {}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def _get_cart(session_id: str) -> Cart:
    if session_id not in _carts:
        _carts[session_id] = Cart(tax_rate=0.18)
    return _carts[session_id]

# ─────────────────────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────────────────────


@main.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        cashier=session.get("cashier_name", "Cashier #1"))


@main.route("/admin")
@login_required
def admin_dashboard():
    return render_template("admin.html")


@main.route("/bills")
@login_required
def bills_page():
    """View all bills history"""
    bills = get_all_bills_db()
    return render_template("bills.html", bills=bills)

# ─────────────────────────────────────────────────────────────
# PRODUCT API
# ─────────────────────────────────────────────────────────────


@main.route("/api/products", methods=["GET"])
def api_get_products():
    """Return full product catalog"""
    category = request.args.get("category", "").strip()
    products = get_all_products()
    if category:
        products = [
            p for p in products
            if p["category"].lower() == category.lower()
        ]
    return jsonify({"products": products}), 200


@main.route("/api/products", methods=["POST"])
def api_create_product():
    """Create a product (stored in database)."""
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    category = data.get("category", "General").strip() or "General"
    barcode = data.get("barcode", "").strip()
    image_emoji = data.get("image_emoji", "📦")
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))

    if not name:
        return jsonify({"error": "Product name is required"}), 400
    if price <= 0:
        return jsonify({"error": "Price must be greater than 0"}), 400
    if stock < 0:
        return jsonify({"error": "Stock cannot be negative"}), 400

    existing = get_all_products()
    next_num = len(existing) + 1
    product_id = f"N{next_num:03d}"
    while any(p["id"] == product_id for p in existing):
        next_num += 1
        product_id = f"N{next_num:03d}"

    if not barcode:
        barcode = f"999{uuid.uuid4().int % 10**10:010d}"

    payload = {
        "id": product_id,
        "name": name,
        "category": category,
        "price": round(price, 2),
        "barcode": barcode,
        "stock": stock,
        "image_emoji": image_emoji
    }

    success = create_product_db(payload)
    if not success:
        return jsonify({"error": "Failed to create product (duplicate ID/barcode)"}), 409
    return jsonify({"message": "Product created", "product": payload}), 201


@main.route("/api/products/<product_id>", methods=["DELETE"])
def api_delete_product(product_id: str):
    """Delete product from catalog if not used in any bill."""
    success, msg = delete_product_db(product_id)
    if not success:
        if msg == "Product not found":
            return jsonify({"error": msg}), 404
        return jsonify({"error": msg}), 409
    return jsonify({"message": "Product deleted"}), 200


@main.route("/api/products/search", methods=["GET"])
def api_search_products():
    """Search products by name, category, or barcode"""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(
            {"error": "Query parameter 'q' is required"}), 400
    results = search_products(query)
    return jsonify({"products": results, "count": len(results)}), 200


@main.route("/api/products/barcode/<barcode>", methods=["GET"])
def api_get_by_barcode(barcode: str):
    """Fetch product by barcode"""
    product = get_product_by_barcode(barcode)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product.to_dict()}), 200


# ─────────────────────────────────────────────────────────────
# CART API
# ─────────────────────────────────────────────────────────────

@main.route("/api/cart/<session_id>", methods=["GET"])
def api_get_cart(session_id: str):
    """Return current cart state"""
    cart = _get_cart(session_id)
    return jsonify(cart.to_dict()), 200


@main.route("/api/cart/<session_id>/add", methods=["POST"])
def api_add_to_cart(session_id: str):
    """Add product to cart"""
    data = request.get_json(force=True)
    pid = data.get("product_id", "").strip()
    qty = int(data.get("quantity", 1))
    discount = float(data.get("discount_percent", 0.0))

    product = get_product_by_id(pid)
    if not product:
        return jsonify(
            {"error": f"Product '{pid}' not found"}), 404
    if qty < 1:
        return jsonify(
            {"error": "Quantity must be at least 1"}), 400
    if qty > product.stock:
        return jsonify(
            {"error": f"Only {product.stock} units in stock"}), 409

    cart = _get_cart(session_id)
    cart.add_item(product, qty, discount)
    return jsonify(
        {"message": "Item added", "cart": cart.to_dict()}), 200


@main.route("/api/cart/<session_id>/update", methods=["PUT"])
def api_update_cart(session_id: str):
    """Update quantity for cart item"""
    data = request.get_json(force=True)
    pid = data.get("product_id", "").strip()
    qty = int(data.get("quantity", 1))

    cart = _get_cart(session_id)
    cart.update_quantity(pid, qty)
    return jsonify({"message": "Cart updated", "cart": cart.to_dict()}), 200


@main.route("/api/cart/<session_id>/remove/<product_id>",
            methods=["DELETE"])
def api_remove_from_cart(session_id: str, product_id: str):
    """Remove product from cart"""
    cart = _get_cart(session_id)
    cart.remove_item(product_id)
    return jsonify({"message": "Item removed", "cart": cart.to_dict()}), 200


@main.route("/api/cart/<session_id>/discount", methods=["POST"])
def api_apply_discount(session_id: str):
    """Apply global discount"""
    data = request.get_json(force=True)
    discount = float(data.get("discount_percent", 0.0))
    if not (0 <= discount <= 100):
        return jsonify(
            {"error": "Discount must be between 0 and 100"}), 400
    cart = _get_cart(session_id)
    cart.global_discount_percent = discount
    return jsonify({
        "message": f"Discount {discount}% applied",
        "cart": cart.to_dict()
    }), 200


@main.route("/api/cart/<session_id>/clear", methods=["DELETE"])
def api_clear_cart(session_id: str):
    """Clear cart"""
    cart = _get_cart(session_id)
    cart.clear()
    return jsonify({"message": "Cart cleared", "cart": cart.to_dict()}), 200

# ─────────────────────────────────────────────────────────────
# BILLING / CHECKOUT API
# ─────────────────────────────────────────────────────────────


@main.route("/api/checkout/<session_id>", methods=["POST"])
def api_checkout(session_id: str):
    """Process payment and generate receipt (SAVED TO DB)"""
    data = request.get_json(force=True)
    payment_method = data.get("payment_method", "cash").lower()
    amount_tendered = float(data.get("amount_tendered", 0.0))

    cart = _get_cart(session_id)
    if not cart.items:
        return jsonify({"error": "Cart is empty"}), 400

    grand_total = cart.grand_total

    if payment_method == "cash" and amount_tendered < grand_total:
        return jsonify({
            "error": (
                f"Insufficient cash. Required: ₹{grand_total}, "
                f"Tendered: ₹{amount_tendered}")
        }), 422

    change = round(
        amount_tendered - grand_total, 2
    ) if payment_method == "cash" else 0.0

    # Build receipt
    receipt_id = "RCPT-" + uuid.uuid4().hex[:8].upper()
    receipt = {
        "receipt_id": receipt_id,
        "timestamp": datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"),
        "session_id": session_id,
        "items": [i.to_dict() for i in cart.items],
        "subtotal": cart.subtotal,
        "discount_amount": cart.global_discount_amount,
        "tax_amount": cart.tax_amount,
        "grand_total": grand_total,
        "payment_method": payment_method,
        "amount_tendered": amount_tendered,
        "change_returned": change,
        "status": "PAID",
        "cashier": session.get("cashier_name", "Cashier #1"),
        "item_count": cart.item_count
    }

    # Save to database
    success = save_bill_db(receipt)

    if success:
        cart.clear()
        return jsonify({
            "message": "Payment successful",
            "receipt": receipt,
            "saved_to_db": True
        }), 200
    else:
        return jsonify(
            {"error": "Failed to save bill to database"}), 500

# ─────────────────────────────────────────────────────────────
# BILLS / HISTORY API
# ─────────────────────────────────────────────────────────────


@main.route("/api/bills", methods=["GET"])
def api_get_bills():
    """Get all bills"""
    limit = request.args.get("limit", type=int)
    date = request.args.get("date", "").strip()

    if date:
        bills = get_bills_by_date_db(date)
    else:
        bills = get_all_bills_db(limit)

    return jsonify({
        "bills": bills,
        "count": len(bills)
    }), 200


@main.route("/api/bills/<receipt_id>", methods=["GET"])
def api_get_bill(receipt_id: str):
    """Get specific bill with items"""
    bill = get_bill_by_id_db(receipt_id)
    if not bill:
        return jsonify({"error": "Bill not found"}), 404
    return jsonify({"bill": bill}), 200

# ─────────────────────────────────────────────────────────────
# REPORTS API
# ─────────────────────────────────────────────────────────────


@main.route("/api/reports/summary", methods=["GET"])
def api_report_summary():
    """Get complete sales report"""
    date = request.args.get("date", "").strip()

    daily_stats = get_daily_stats_db(date) or {
        "total_transactions": 0,
        "total_revenue": 0.0,
        "total_tax": 0.0,
        "total_discount": 0.0,
        "average_bill": 0.0,
        "total_items": 0
    }

    category_sales = get_category_sales_db(date)
    top_products = get_top_products_db(10, date)
    hourly_sales = get_hourly_sales_db(date)

    # Get payment method split
    bills = get_all_bills_db()
    payment_split = {}
    for bill in bills:
        method = bill['payment_method']
        if method not in payment_split:
            payment_split[method] = {"count": 0, "revenue": 0.0}
        payment_split[method]["count"] += 1
        payment_split[method]["revenue"] += bill['grand_total']

    return jsonify({
        "daily_summary": {
            "total_transactions": daily_stats["total_transactions"],
            "total_revenue": round(daily_stats["total_revenue"], 2),
            "total_tax_collected": round(daily_stats["total_tax"], 2),
            "total_discount_given": round(
                daily_stats["total_discount"], 2),
            "average_bill_value": round(daily_stats["average_bill"], 2),
            "total_items_sold": daily_stats["total_items"]
        },
        "payment_split": payment_split,
        "top_products": top_products,
        "category_breakdown": category_sales,
        "hourly_trends": hourly_sales,
    }), 200


@main.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "POS Simulator",
        "database": "connected"
    }), 200
