# ai_company_scraper.py
# To run: `python ai_company_scraper.py`

import json
import time
import threading
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# === Configuration ===
INPUT_FILE = "avanza_stock_data1.json"
OUTPUT_FILE = "ai_companies.json"

OLLAMA_URL = "http://localhost:11500/api/generate"
OLLAMA_MODEL = "gemma3"  # or llama3, phi3, etc.

# === Thread-local WebDriver for parallel scraping ===
thread_local = threading.local()

def get_driver():
    if not hasattr(thread_local, "driver"):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        thread_local.driver = webdriver.Chrome(options=options)
    return thread_local.driver

# === Scrape company description ===
def scrape_company_description(order_book_id):
    url = f"https://www.avanza.se/aktier/om-aktien.html/{order_book_id}"
    driver = get_driver()

    try:
        print(f"🔍 Scraping: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "separation"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        paragraphs = soup.find_all("p", class_="separation")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text

        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text

    except TimeoutException:
        print(f"❌ Timeout: {url}")
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
    return ""

# === Parallel scraping ===
def parallel_scrape(data, max_workers=10):
    descriptions = {}
    company_info = {}

    def worker(item):
        name = item["name"]
        order_book_id = item["orderBookId"]
        desc = scrape_company_description(order_book_id)
        return name, desc, item

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, item) for item in data]
        for future in as_completed(futures):
            try:
                name, desc, item = future.result()
                if desc:
                    descriptions[name] = desc
                    company_info[name] = item
            except Exception as e:
                print(f"❌ Worker error: {e}")

    return descriptions, company_info

# === Batch descriptions for Ollama ===
def batch_dict(data, batch_size=100):
    items = list(data.items())
    for i in range(0, len(items), batch_size):
        yield dict(items[i:i + batch_size])

# === Call Ollama to classify ===
def classify_with_ollama(descriptions):
    ai_flags = {}

    for batch in batch_dict(descriptions, batch_size=100):
        prompt = (
            "You are an AI industry analyst. For each company below, respond with a JSON dictionary of the form "
            "{company name: true/false} to indicate if the company actively builds or develops AI technologies.\n\n"
        )

        for company, desc in batch.items():
            prompt += f"{company}: {desc}\n"

        try:
            print("🤖 Calling Ollama...")
            response = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "")
            print("📬 LLM Response received.")
            cleaned = raw_text.strip().strip("```json").strip("```")
            parsed = json.loads(cleaned)
            ai_flags.update(parsed)
        except Exception as e:
            print(f"⚠️ Ollama classification failed: {e}")
            continue

        time.sleep(1)

    return ai_flags

# === Main execution ===
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Loaded {len(data)} companies")

    # Scrape descriptions
    descriptions, company_info = parallel_scrape(data, max_workers=10)
    print(f"✅ Scraped {len(descriptions)} company descriptions")

    # Classify with Ollama
    ai_flags = classify_with_ollama(descriptions)

    # Merge results
    final_output = []
    for company_name, is_ai in ai_flags.items():
        obj = company_info.get(company_name, {})
        obj["ai_company"] = is_ai
        obj["description"] = descriptions.get(company_name, "")
        final_output.append(obj)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(final_output)} AI-labeled companies to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
