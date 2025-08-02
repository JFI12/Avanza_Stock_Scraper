# scraper-python.py
# To run this script: `python scraper-python.py`

import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# === Configuration ===
GENAI_API_KEY = "asdasdasdasd"
TARGET_KEYWORD = "ökning"
BASE_URL = "https://www.di.se"

# === Gemini Setup ===
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# === Gemini Call ===
def call_gemini(content):
    print("🤖 Calling Gemini with data...")
    try:
        prompt = (
            "You are a financial analyst assistant. Read the following news telegrams and extract company recommendation data. "
            "Return ONLY a valid JSON structure like this:\n\n"
            "{[company, url, motivation, brokername, fame-level (high, medium, low), determine based on the text if I should (buy, hold or sell)]}\n\n"
            "- Estimate the fame-level of the broker (based on its popularity in Sweden).\n"
            "- Extract the company name from the text if possible.\n"
            "- Extract the broker name if available.\n"
            "- Generate a short motivation based on the content.\n"
            "- Only return VALID JSON. No explanations or extra text.\n\n"
            + content
        )
        response = model.generate_content(prompt)
        print("📬 Gemini response:")
        print(response.text)
    except Exception as e:
        print(f"❌ Gemini API error: {e}")


# === Scrape all telegram links ===
def scrape_all_telegram_urls():
    list_url = f"{BASE_URL}/bors/aktier/aza-1294/nyheter/"
    try:
        response = requests.get(list_url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch telegram list page: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    telegram_links = {
        BASE_URL + a['href']
        for a in soup.find_all("a", href=True)
        if "/bors/telegram/" in a["href"]
    }

    print(f"🔗 Found {len(telegram_links)} unique telegram links.")
    return list(telegram_links)


# === Extract headline + content if it contains "ökning" ===
def extract_telegram_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    text_div = soup.find("div", class_="telegram-page__text")
    headline_div = soup.find("div", class_="telegram-page__headline")

    if not text_div or not headline_div:
        return None

    content = headline_div.get_text(strip=True) + "\n" + text_div.get_text(strip=True)
    if TARGET_KEYWORD in content.lower():
        return content
    return None


# === Main Script ===
def main():
    telegram_urls = scrape_all_telegram_urls()
    compiled_data = []

    for url in telegram_urls:
        print(f"📄 Processing: {url}")
        text = extract_telegram_data(url)
        if text:
            compiled_data.append(f"[Unknown Company, {url}]: {text}\n")

    print(f"✅ Extracted 'ökning' text from {len(compiled_data)} telegrams.")

    if compiled_data:
        content_for_gemini = "\n".join(compiled_data)
        call_gemini(content_for_gemini)
    else:
        print("⚠️ No matching telegrams found with the keyword.")


if __name__ == "__main__":
    main()
