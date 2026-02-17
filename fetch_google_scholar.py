import time
import csv
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("google_scholar_selenium.log"),
        logging.StreamHandler()
    ]
)

# ---------------- SCRAPER ----------------
def scrape_google_scholar_exact_phrase(phrase: str):
    phrase_underscored = phrase.replace(" ", "_")
    output_csv = f"google_scholar_{phrase_underscored}.csv"

    search_url = (
        "https://scholar.google.com/scholar"
        f'?hl=en&q="{phrase.replace(" ", "+")}"&as_sdt=0,5'
    )

    # ---- Chromium setup ----
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    logging.info(f"Opening Google Scholar for phrase: {phrase}")
    driver.get(search_url)

    # -------- ONE-TIME MANUAL WAIT --------
    logging.info(
        "⏸️ Waiting 60 seconds for manual CAPTCHA / robot validation"
    )
    print("\n⚠️ ACTION REQUIRED (ONE TIME):")
    print("• Check the browser window")
    print("• Solve CAPTCHA / 'I'm not a robot' if shown")
    print("• Ensure results are visible")
    print("• Scraping starts automatically after 60 seconds\n")

    time.sleep(60)

    logging.info("Starting automated scraping")

    # ---- Resume support ----
    seen_titles = set()
    total_results = 0

    if os.path.exists(output_csv):
        with open(output_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                seen_titles.add(row["Title"])
        total_results = len(seen_titles)
        logging.info(
            f"Resuming '{phrase_underscored}' "
            f"from {total_results} existing results"
        )

    page = 1

    try:
        while True:
            logging.info(
                f"Scraping page {page} "
                f"for phrase '{phrase_underscored}'"
            )

            results = driver.find_elements(By.CSS_SELECTOR, "div.gs_ri")

            if not results:
                logging.warning("No results found on page — stopping")
                break

            write_header = not os.path.exists(output_csv)

            with open(output_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(["Source", "Search term", "Title"])

                for r in results:
                    try:
                        title_el = r.find_element(By.TAG_NAME, "h3")
                        title = title_el.text.strip()

                        if not title or title in seen_titles:
                            continue

                        writer.writerow([
                            "Google Scholar",
                            phrase_underscored,
                            title
                        ])

                        seen_titles.add(title)
                        total_results += 1

                        logging.info(
                            f"Result #{total_results} "
                            f"(page {page}): {title[:80]}"
                        )

                    except NoSuchElementException:
                        continue

            # short polite delay (NOT a long wait)
            time.sleep(5)

            # ---- Next page ----
            try:
                next_button = driver.find_element(By.LINK_TEXT, "Next")
                next_button.click()
                page += 1
                time.sleep(6)
            except NoSuchElementException:
                logging.info("No Next button found — end of results")
                break

    except TimeoutException:
        logging.error("Timeout — likely blocked by Google Scholar")

    finally:
        driver.quit()
        logging.info(
            f"Finished phrase '{phrase_underscored}'. "
            f"Total results saved: {total_results}"
        )


# ---------------- MAIN ----------------
if __name__ == "__main__":
    phrase = input("Enter exact search phrase: ").strip()

    if not phrase:
        raise ValueError("Search phrase cannot be empty")

    scrape_google_scholar_exact_phrase(phrase)
