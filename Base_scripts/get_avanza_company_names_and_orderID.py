from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
import time
import json

options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Uncomment to run headless (faster, no UI)

driver = webdriver.Chrome(options=options)
driver.get("https://www.avanza.se/aktier/lista.html")
time.sleep(3)  # Just enough for initial load

# Step 1: Click "Visa fler" until all companies are loaded
max_scrolls = 700
previous_count = 0
wait_time = 1.2

for scroll in range(max_scrolls):
    current_count = len(driver.find_elements(By.CSS_SELECTOR, "a[title][href*='/aktier/om-aktien.html']"))


    # Stop if no new entries loaded
    if current_count == previous_count:
        print(f"⚠️ No new companies after {scroll} scrolls. Stopping.")
        break

    previous_count = current_count

    # Try to click "Visa fler" button
    try:
        show_more_button = driver.find_element(By.CSS_SELECTOR, "button[data-e2e='tbs-stocks-show-more']")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", show_more_button)
        time.sleep(0.3)
        show_more_button.click()
        time.sleep(wait_time)  # Reduce wait but still allow DOM update
    except (NoSuchElementException, ElementClickInterceptedException):
        print(f"🚫 No more 'Visa fler' button found at scroll {scroll}.")
        break

    print(f"🔄 Scroll {scroll+1}, Companies loaded: {current_count}")

# Step 2: Extract data from all loaded entries
print("📦 Extracting company names and orderBookIds...")
companies = []

for el in driver.find_elements(By.CSS_SELECTOR, "a[title][href*='/aktier/om-aktien.html']"):
    try:
        name = el.get_attribute("title").strip()
        relative_url = el.get_attribute("href").strip()
        if "aktien.html/" in relative_url:
            orderbook_id = relative_url.split("aktien.html/")[1].split("/")[0]
            companies.append({
                "name": name,
                "orderBookId": orderbook_id
            })
    except Exception:
        continue

driver.quit()

# Step 3: Save results
with open("avanza_all_companies.json", "w", encoding="utf-8") as f:
    json.dump(companies, f, indent=2, ensure_ascii=False)

print(f"✅ Done! Extracted {len(companies)} companies.")
