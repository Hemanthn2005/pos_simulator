import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "pos-simulator-key-2024")
    DEBUG = True
    TAX_RATE = 0.18
    CURRENCY_SYMBOL = "₹"
