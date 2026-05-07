import sqlite3
import os
from .config import Config


def get_db():
    """Create and return database connection"""
    db_path = Config.DATABASE

    # Ensure instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()

    # Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            barcode TEXT UNIQUE NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            image_emoji TEXT DEFAULT '📦',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            receipt_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            subtotal REAL NOT NULL DEFAULT 0,
            discount_amount REAL NOT NULL DEFAULT 0,
            tax_amount REAL NOT NULL DEFAULT 0,
            grand_total REAL NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL DEFAULT 'cash',
            amount_tendered REAL NOT NULL DEFAULT 0,
            change_returned REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'PAID',
            cashier TEXT DEFAULT 'Cashier #1',
            total_items INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bill items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bill_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount_percent REAL DEFAULT 0,
            line_total REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(receipt_id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    # Seed products if empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        seed_products(cursor)

    conn.commit()
    conn.close()


def seed_products(cursor):
    """Insert default products into database"""
    products = [
        # Electronics
        ("E001", "Wireless Earbuds", "Electronics", 1299.00,
         "8901234560001", 50, "🎧"),
        ("E002", "USB-C Hub 7-in-1", "Electronics", 899.00,
         "8901234560002", 30, "🔌"),
        ("E003", "Phone Stand", "Electronics", 249.00,
         "8901234560003", 80, "📱"),
        ("E004", "Bluetooth Speaker", "Electronics", 1599.00,
         "8901234560004", 25, "🔊"),
        # Grocery
        ("G001", "Whole Wheat Bread", "Grocery", 45.00,
         "8901234561001", 100, "🍞"),
        ("G002", "Farm Fresh Milk 1L", "Grocery", 68.00,
         "8901234561002", 200, "🥛"),
        ("G003", "Basmati Rice 5kg", "Grocery", 320.00,
         "8901234561003", 60, "🌾"),
        ("G004", "Olive Oil 500ml", "Grocery", 475.00,
         "8901234561004", 40, "🫒"),
        ("G005", "Organic Honey 250g", "Grocery", 299.00,
         "8901234561005", 55, "🍯"),
        # Clothing
        ("C001", "Cotton T-Shirt", "Clothing", 399.00,
         "8901234562001", 75, "👕"),
        ("C002", "Denim Jeans", "Clothing", 1199.00,
         "8901234562002", 45, "👖"),
        ("C003", "Sports Sneakers", "Clothing", 2499.00,
         "8901234562003", 30, "👟"),
        ("C004", "Winter Jacket", "Clothing", 1999.00,
         "8901234562004", 20, "🧥"),
        # Beverages
        ("B001", "Cold Coffee 250ml", "Beverages", 60.00,
         "8901234563001", 120, "☕"),
        ("B002", "Orange Juice 1L", "Beverages", 110.00,
         "8901234563002", 90, "🍊"),
        ("B003", "Sparkling Water", "Beverages", 40.00,
         "8901234563003", 150, "💧"),
        ("B004", "Green Tea Pack", "Beverages", 180.00,
         "8901234563004", 70, "🍵"),
        # Stationery
        ("S001", "Ballpoint Pen Set", "Stationery", 85.00,
         "8901234564001", 200, "✒️"),
        ("S002", "A4 Notebook 200pg", "Stationery", 120.00,
         "8901234564002", 130, "📒"),
        ("S003", "Sticky Notes Pack", "Stationery", 65.00,
         "8901234564003", 180, "📝"),
    ]

    insert_sql = '''INSERT INTO products
        (id, name, category, price, barcode, stock, image_emoji)
        VALUES (?, ?, ?, ?, ?, ?, ?)'''
    cursor.executemany(insert_sql, products)


def get_all_products_db():
    """Get all products from database"""
    conn = get_db()
    products = conn.execute(
        "SELECT * FROM products ORDER BY category, name").fetchall()
    conn.close()
    return [dict(p) for p in products]


def get_product_by_id_db(pid):
    """Get product by ID"""
    conn = get_db()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    conn.close()
    return dict(product) if product else None


def get_product_by_barcode_db(barcode):
    """Get product by barcode"""
    conn = get_db()
    product = conn.execute(
        "SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    conn.close()
    return dict(product) if product else None


def search_products_db(query):
    """Search products"""
    conn = get_db()
    q = f"%{query}%"
    products = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? OR category LIKE ?"
        " OR barcode LIKE ?",
        (q, q, q)
    ).fetchall()
    conn.close()
    return [dict(p) for p in products]


def create_product_db(product):
    """Create a new product."""
    conn = get_db()
    try:
        conn.execute(
            '''INSERT INTO products
            (id, name, category, price, barcode, stock, image_emoji)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                product["id"],
                product["name"],
                product["category"],
                product["price"],
                product["barcode"],
                product["stock"],
                product.get("image_emoji", "📦")
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_product_db(product_id):
    """Delete a product if it has never been billed."""
    conn = get_db()
    try:
        used = conn.execute(
            "SELECT 1 FROM bill_items WHERE product_id = ? LIMIT 1",
            (product_id,)
        ).fetchone()
        if used:
            return False, "Cannot delete product with billing history"

        result = conn.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )
        conn.commit()
        if result.rowcount == 0:
            return False, "Product not found"
        return True, ""
    finally:
        conn.close()


def update_stock_db(product_id, quantity_change):
    """Update product stock"""
    conn = get_db()
    conn.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (quantity_change, product_id)
    )
    conn.commit()
    conn.close()


def save_bill_db(receipt):
    """Save bill to database"""
    conn = get_db()
    try:
        # Insert bill
        conn.execute('''
            INSERT INTO bills (receipt_id, timestamp, session_id,
                             subtotal, discount_amount, tax_amount,
                             grand_total, payment_method,
                             amount_tendered, change_returned,
                             status, total_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            receipt['receipt_id'],
            receipt['timestamp'],
            receipt['session_id'],
            receipt['subtotal'],
            receipt['discount_amount'],
            receipt['tax_amount'],
            receipt['grand_total'],
            receipt['payment_method'],
            receipt['amount_tendered'],
            receipt['change_returned'],
            receipt['status'],
            receipt['item_count']
        ))

        # Insert bill items
        for item in receipt['items']:
            conn.execute('''
                INSERT INTO bill_items (bill_id, product_id,
                                      product_name, quantity,
                                      unit_price, discount_percent,
                                      line_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt['receipt_id'],
                item['product_id'],
                item['product_name'],
                item['quantity'],
                item['unit_price'],
                item['discount_percent'],
                item['line_total']
            ))

            # Update stock
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item['quantity'], item['product_id'])
            )

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving bill: {e}")
        return False
    finally:
        conn.close()


def get_all_bills_db(limit=None):
    """Get all bills"""
    conn = get_db()
    if limit:
        bills = conn.execute(
            "SELECT * FROM bills ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    else:
        bills = conn.execute(
            "SELECT * FROM bills ORDER BY created_at DESC"
        ).fetchall()
    conn.close()
    return [dict(b) for b in bills]


def get_bill_by_id_db(receipt_id):
    """Get bill with items"""
    conn = get_db()
    bill = conn.execute(
        "SELECT * FROM bills WHERE receipt_id = ?", (receipt_id,)
    ).fetchone()

    if not bill:
        conn.close()
        return None

    items = conn.execute(
        "SELECT * FROM bill_items WHERE bill_id = ?", (receipt_id,)
    ).fetchall()

    conn.close()

    bill_dict = dict(bill)
    bill_dict['items'] = [dict(i) for i in items]
    return bill_dict


def get_bills_by_date_db(date_str):
    """Get bills for specific date (YYYY-MM-DD)"""
    conn = get_db()
    bills = conn.execute(
        "SELECT * FROM bills WHERE date(timestamp) = ?"
        " ORDER BY created_at DESC",
        (date_str,)
    ).fetchall()
    conn.close()
    return [dict(b) for b in bills]


def get_daily_stats_db(date_str=None):
    """Get daily statistics"""
    conn = get_db()

    if date_str:
        where_clause = "WHERE date(timestamp) = ?"
        params = (date_str,)
    else:
        where_clause = "WHERE date(timestamp) = date('now')"
        params = ()

    stats = conn.execute(f'''
        SELECT
            COUNT(*) as total_transactions,
            COALESCE(SUM(grand_total), 0) as total_revenue,
            COALESCE(SUM(tax_amount), 0) as total_tax,
            COALESCE(SUM(discount_amount), 0) as total_discount,
            COALESCE(AVG(grand_total), 0) as average_bill,
            COALESCE(SUM(total_items), 0) as total_items
        FROM bills {where_clause}
    ''', params).fetchone()

    conn.close()
    return dict(stats) if stats else None


def get_category_sales_db(date_str=None):
    """Get sales by category"""
    conn = get_db()

    if date_str:
        where_clause = "WHERE date(b.timestamp) = ?"
        params = (date_str,)
    else:
        where_clause = ""
        params = ()

    category_sales = conn.execute(f'''
        SELECT
            p.category,
            COUNT(DISTINCT b.receipt_id) as bill_count,
            COALESCE(SUM(bi.quantity), 0) as units_sold,
            COALESCE(SUM(bi.line_total), 0) as revenue
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.receipt_id
        JOIN products p ON bi.product_id = p.id
        {where_clause}
        GROUP BY p.category
        ORDER BY revenue DESC
    ''', params).fetchall()

    conn.close()
    return [dict(c) for c in category_sales]


def get_top_products_db(limit=10, date_str=None):
    """Get top selling products"""
    conn = get_db()

    if date_str:
        where_clause = "WHERE date(b.timestamp) = ?"
        params = (date_str, limit)
    else:
        where_clause = ""
        params = (limit,)

    top_products = conn.execute(f'''
        SELECT
            bi.product_id,
            bi.product_name,
            COALESCE(SUM(bi.quantity), 0) as units_sold,
            COALESCE(SUM(bi.line_total), 0) as revenue
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.receipt_id
        {where_clause}
        GROUP BY bi.product_id, bi.product_name
        ORDER BY revenue DESC
        LIMIT ?
    ''', params).fetchall()

    conn.close()
    return [dict(p) for p in top_products]


def get_hourly_sales_db(date_str=None):
    """Get hourly sales breakdown"""
    conn = get_db()

    if date_str:
        where_clause = "WHERE date(timestamp) = ?"
        params = (date_str,)
    else:
        where_clause = "WHERE date(timestamp) = date('now')"
        params = ()

    hourly = conn.execute(f'''
        SELECT
            CAST(strftime('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as transaction_count,
            COALESCE(SUM(grand_total), 0) as revenue
        FROM bills
        {where_clause}
        GROUP BY hour
        ORDER BY hour
    ''', params).fetchall()

    conn.close()

    # Fill in all 24 hours
    hourly_dict = {
        h: {'hour': h, 'label': f"{h:02d}:00", 'count': 0, 'revenue': 0}
        for h in range(24)
    }
    for h in hourly:
        hour_data = dict(h)
        hourly_dict[hour_data['hour']] = {
            'hour': hour_data['hour'],
            'label': f"{hour_data['hour']:02d}:00",
            'count': hour_data['transaction_count'],
            'revenue': hour_data['revenue']
        }

    return list(hourly_dict.values())
