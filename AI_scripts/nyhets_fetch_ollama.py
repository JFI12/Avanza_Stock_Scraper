# scraper-python.py
# To run this script: `python scraper-python.py`

import os
import requests
from bs4 import BeautifulSoup
import json

# === Configuration ===
TARGET_KEYWORD = "ökning"
BASE_URL = "https://www.di.se"
OLLAMA_URL = "http://localhost:11500/api/generate"

OLLAMA_MODEL = "gemma3"  # or "phi3", "llama3" if installed

# === Ollama Call ===
def call_ollama(content):
    print("🤖 Calling local LLM (Ollama) with data...")
    prompt = (
        "You are a financial analyst assistant. Read the following news telegrams and extract company recommendation data. "
        "Return ONLY a valid JSON structure like this:\n\n"
        "[{\"company\": \"...\", \"url\": \"...\", \"motivation\": \"...\", \"brokername\": \"...\", \"fame-level\": \"high\", \"recommendation\": \"buy\"}]\n\n"
        "- Estimate the fame-level of the broker (based on its popularity in Sweden).\n"
        "- Extract the company name from the text if possible.\n"
        "- Extract the broker name if available.\n"
        "- Generate a short motivation based on the content.\n"
        "- Only return VALID JSON. No explanations or extra text.\n\n"
        + content
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        result = response.json()
        print("📬 Ollama response:")
        print(result["response"])
    except Exception as e:
        print(f"❌ Ollama error: {e}")


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
    call_ollama("hello world")  # Test call to Ollama
    telegram_urls = scrape_all_telegram_urls()
    compiled_data = []

    for url in telegram_urls:
        print(f"📄 Processing: {url}")
        text = extract_telegram_data(url)
        if text:
            compiled_data.append(f"[Unknown Company, {url}]: {text}\n")

    print(f"✅ Extracted 'ökning' text from {len(compiled_data)} telegrams.")

    if compiled_data:
        content_for_llm = "\n".join(compiled_data)
        call_ollama(content_for_llm)
    else:
        print("⚠️ No matching telegrams found with the keyword.")


if __name__ == "__main__":
    main()
