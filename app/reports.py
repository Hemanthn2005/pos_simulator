from typing import List, Dict
from collections import defaultdict


class SalesReporter:
    def __init__(self, receipts: Dict[str, dict] = None):
        self.receipts = receipts or {}

    def _all_receipts(self) -> List[dict]:
        return list(self.receipts.values())

    def daily_summary(self) -> dict:
        receipts = self._all_receipts()
        if not receipts:
            return {
                "total_transactions": 0,
                "total_revenue": 0.0,
                "total_tax_collected": 0.0,
                "total_discount_given": 0.0,
                "average_bill_value": 0.0,
                "total_items_sold": 0
            }
        total_revenue = sum(r.get("grand_total", 0) for r in receipts)
        total_tax = sum(r.get("tax_amount", 0) for r in receipts)
        total_discount = sum(r.get("discount_amount", 0) for r in receipts)
        total_items = sum(r.get("item_count", 0) for r in receipts)
        return {
            "total_transactions": len(receipts),
            "total_revenue": round(total_revenue, 2),
            "total_tax_collected": round(total_tax, 2),
            "total_discount_given": round(total_discount, 2),
            "average_bill_value": round(
                total_revenue / len(receipts), 2) if receipts else 0,
            "total_items_sold": total_items,
        }

    def payment_method_split(self) -> Dict[str, dict]:
        split = defaultdict(lambda: {"count": 0, "revenue": 0.0})
        for r in self._all_receipts():
            m = r.get("payment_method", "unknown")
            split[m]["count"] += 1
            split[m]["revenue"] += r.get("grand_total", 0)
        return {
            k: {"count": v["count"], "revenue": round(v["revenue"], 2)}
            for k, v in split.items()
        }

    def category_breakdown(self) -> List[dict]:
        cats = defaultdict(
            lambda: {"revenue": 0.0, "units": 0, "transactions": 0})
        for r in self._all_receipts():
            for item in r.get("items", []):
                category = item.get("category", "Other")
                cats[category]["revenue"] += item.get("line_total", 0)
                cats[category]["units"] += item.get("quantity", 0)
                cats[category]["transactions"] += 1
        return [
            {"category": cat,
             "revenue": round(data["revenue"], 2),
             "units_sold": data["units"],
             "transactions": data["transactions"]}
            for cat, data in sorted(
                cats.items(), key=lambda x: -x[1]["revenue"])
        ]

    def top_products(self, limit: int = 5) -> List[dict]:
        products = defaultdict(
            lambda: {"name": "", "revenue": 0.0, "units": 0})
        for r in self._all_receipts():
            for item in r.get("items", []):
                pid = item.get("product_id", "")
                products[pid]["name"] = item.get("product_name", "")
                products[pid]["revenue"] += item.get("line_total", 0)
                products[pid]["units"] += item.get("quantity", 0)
        ranked = sorted(products.items(),
                        key=lambda x: -x[1]["revenue"])
        return [
            {"product_id": pid, "product_name": data["name"],
             "revenue": round(data["revenue"], 2),
             "units_sold": data["units"]}
            for pid, data in ranked[:limit]
        ]

    def hourly_trends(self) -> List[dict]:
        hours = defaultdict(lambda: {"count": 0, "revenue": 0.0})
        for r in self._all_receipts():
            try:
                timestamp = r.get("timestamp", "")
                hour = int(timestamp.split(" ")[1].split(":")[0])
            except Exception:
                hour = 0
            hours[hour]["count"] += 1
            hours[hour]["revenue"] += r.get("grand_total", 0)
        return [
            {"hour": h, "label": f"{h:02d}:00",
             "count": hours[h]["count"],
             "revenue": round(hours[h]["revenue"], 2)}
            for h in sorted(hours.keys())
        ]
