from datetime import datetime, timedelta
import json

with open("avanza_stock_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

recent_threshold = datetime.now() - timedelta(days=90)

recent_companies = []
for company in data:
    first_date = company.get("firstTradingDate")
    if first_date:
        try:
            first_date_dt = datetime.strptime(first_date, "%Y-%m-%d")
            if first_date_dt >= recent_threshold:
                recent_companies.append(company)
        except Exception:
            continue

print(f"🆕 Found {len(recent_companies)} newly listed companies (last 90 days).")
