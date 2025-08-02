from avanza import Avanza
from datetime import datetime
import json
import time

# Your credentials
USERNAME = 'asd'
PASSWORD = 'asd'
TOTP_SECRET = 'asd'

INPUT_JSON = "avanza_all_companies.json"
#INPUT_JSON = "avanza_orderbookids_extended.json"
OUTPUT_JSON = "avanza_stock_data.json"

def fetch_data():
    # Load list of companies from file
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        companies = json.load(f)

    print(f"📥 Loaded {len(companies)} companies.")

    # Initialize Avanza client
    avanza = Avanza({
        'username': USERNAME,
        'password': PASSWORD,
        'totpSecret': TOTP_SECRET
    })

    stock_data = []
    failed = []

    for idx, company in enumerate(companies):
        name = company.get("name")
        orderBookId = company.get("orderBookId")

        try:
            info = avanza.get_stock_info(orderBookId)

            owners = info['keyIndicators'].get('numberOfOwners', None)
            market_cap_data = info['keyIndicators'].get('marketCapital', {})
            market_cap = market_cap_data.get('value', None)
            market_cap_currency = market_cap_data.get('currency', "N/A")

            quote = info.get('quote', {})
            percent_change = quote.get('changePercent', None)
            volume = quote.get('totalVolumeTraded', None)
            value = quote.get('totalValueTraded', None)
            updated_ts = quote.get('updated', 0)

            historical_data = info.get("historicalClosingPrices", {})
            first_trading_date = historical_data.get("startDate", None)

            last_updated = datetime.utcfromtimestamp(updated_ts / 1000).replace(microsecond=0).isoformat()

            market_cap_div_owners = (market_cap / owners) if owners and market_cap else None
            hype_potential = (market_cap_div_owners * value) if market_cap_div_owners and value else None

            stock_data.append({
                "name": name,
                "orderBookId": orderBookId,
                "owners": owners,
                "marketCap": market_cap,
                "marketCapCurrency": market_cap_currency,
                "changePercentToday": percent_change,
                "volumeTradedToday": volume,
                "valueTradedToday": value,
                "firstTradingDate": first_trading_date,
                "lastUpdated": last_updated,
                "hypePotential": hype_potential
            })

            print(f"✅ {idx+1}/{len(companies)} {name} – Done")

            # Optional: Sleep briefly to avoid rate-limiting
           # time.sleep(0.2)

        except Exception as e:
            print(f"❌ Failed to fetch for {name} ({orderBookId}): {e}")
            failed.append({
                "name": name,
                "orderBookId": orderBookId,
                "error": str(e)
            })
            time.sleep(1)  # Delay on failure to avoid lockout

    # Save results
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(stock_data, f, indent=2, ensure_ascii=False)

    print(f"\n🎉 Finished! Fetched data for {len(stock_data)} stocks.")
    if failed:
        print(f"⚠ {len(failed)} stocks failed to fetch. Saving to failed_log.json.")
        with open("failed_log.json", "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    fetch_data()
