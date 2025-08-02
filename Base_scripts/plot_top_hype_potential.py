import json
import matplotlib.pyplot as plt

INPUT_FILE = "healthcare_companies.json"

def main():
    # Load the stock data
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter entries with required fields and AI tag
    filtered = [
        d for d in data
        if (
            d.get("valueTradedToday") is not None and
            d.get("changePercentToday") is not None and
            d.get("marketCapCurrency") == ("USD" or "SEK") and
            d.get("healthcare_company") is True
        )
    ]

    # Compute a composite score
    for d in filtered:
        d["score"] = d["valueTradedToday"] * abs(d["changePercentToday"])

    # Get top 20 by composite score
    top_20 = sorted(filtered, key=lambda x: x["score"], reverse=True)[:20]

    # Extract data
    names = [item["name"] for item in top_20]
    values = [item["score"] for item in top_20]
    change_directions = [item["changePercentToday"] for item in top_20]

    # Determine colors based on positive/negative change
    colors = ['green' if cp >= 0 else 'red' for cp in change_directions]

    # Plotting
    plt.figure(figsize=(14, 7))
    bars = plt.bar(names, values, color=colors)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.ylabel("ValueTraded × |ChangePercent|")
    plt.title("Top 20 AI Companies by Trading Activity and Volatility\n(Green = Positive Change, Red = Negative)")
    plt.tight_layout()

    # Add value labels
    for bar, change in zip(bars, change_directions):
        height = bar.get_height()
        label = f"{change:+.2f}%"
        plt.text(bar.get_x() + bar.get_width()/2, height, label,
                 ha='center', va='bottom', fontsize=8, rotation=90)

    plt.show()

if __name__ == "__main__":
    main()
