import json
import time
from bs4 import BeautifulSoup
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import threading

# === Gemini Setup ===
genai.configure(api_key="asdasdasdsad")
model = genai.GenerativeModel("gemini-1.5-flash")

INPUT_FILE = "Base_scripts/avanza_stock_data1.json"
OUTPUT_FILE = "ai_companies.json"

# === Thread-local WebDriver (so each thread gets its own browser) ===
thread_local = threading.local()

def get_driver():
    if not hasattr(thread_local, "driver"):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        thread_local.driver = webdriver.Chrome(options=options)
    return thread_local.driver

# === Scrape function using Selenium ===
def scrape_company_description(order_book_id):
    url = f"https://www.avanza.se/aktier/om-aktien.html/{order_book_id}"
    driver = get_driver()

    try:
        print(f"🔍 Navigating to: {url}")
        driver.get(url)

        # ✅ Wait up to 10 seconds for <p class="separation"> to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "separation"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        paragraphs = soup.find_all("p", class_="separation")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text

        # Optional fallback: any long <p>
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text

    except TimeoutException:
        print(f"❌ Timeout waiting for description at: {url}")
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")

    return ""

# === Multithreaded scraper ===
def parallel_scrape_companies(data, max_workers=10):
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

# === Batch classifier ===
def batch_dict(data, batch_size=100):
    items = list(data.items())
    print(f"📦 Batching {len(items)} items into size {batch_size}...")
    for i in range(0, len(items), batch_size):
        yield dict(items[i:i + batch_size])

def get_ai_flags_batched(descriptions):
    ai_flags = {}
    print("🤖 Classifying companies as AI-related...")
    for batch in batch_dict(descriptions, batch_size=100):
        prompt = (
            "Based on the following company descriptions, respond ONLY in JSON format "
            "with structure {company name: true/false} for whether the company develops or builds AI solutions.\n\n"
        )
        for company, desc in batch.items():
            prompt += f"{company}: {desc}\n"

        try:
            response = model.generate_content(prompt)
            cleaned = response.text.strip().strip("```json").strip("```")
            parsed = json.loads(cleaned)
            ai_flags.update(parsed)
        except Exception as e:
            print(f"⚠️ Gemini classification failed: {e}")
            continue

        time.sleep(1)

    return ai_flags

# === Main pipeline ===
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Loaded {len(data)} companies from input file")

    # Scrape in parallel
    descriptions, company_info = parallel_scrape_companies(data, max_workers=10)

    print(f"✅ Scraped {len(descriptions)} descriptions")

    # Gemini classification
    ai_flags = get_ai_flags_batched(descriptions)

    # Combine data
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
