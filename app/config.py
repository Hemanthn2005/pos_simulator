import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "pos-simulator-key-2024")
    DEBUG = True
    TAX_RATE = 0.18
    CURRENCY_SYMBOL = "₹"
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    DATABASE = os.environ.get(
        "DATABASE_PATH", "instance/pos_database.db")
