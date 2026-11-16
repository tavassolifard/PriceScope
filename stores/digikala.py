from playwright.sync_api import Error as PlaywrightError
from urllib.parse import urljoin, quote
from utils import normalize_price


class Digikala:

    def __init__(self, playwright):
        self.playwright = playwright
        self.browser = self.playwright.chromium.launch(
            headless=True
        )

    def search_product(self, query):
        page = None
        try:
            page = self.browser.new_page()

            url = "https://www.digikala.com/search/?q=" + quote(query)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            products = page.locator('a[href*="/product/dkp-"]')

            products.first.wait_for(
                state="visible",
                timeout=20000
            )
            results = []
            seen = set()

            for i in range(products.count()):
                item = products.nth(i)
                href = item.get_attribute("href")

                if item.locator("h3").count() > 0:
                    title = item.locator("h3").inner_text().strip()
                    if not href or not title or href in seen:
                        continue

                    seen.add(href)

                    href = urljoin("https://www.digikala.com", href)

                    results.append({
                        "title": title,
                        "url": href,
                    })

                    if len(results) == 5:
                        break

            return results

        except PlaywrightError as e:
            print(f"Search failed: {e}")
            return "Search error"

        finally:
            if page is not None:
                page.close()

    def get_price(self, product_url):
        page = None
        try:
            page = self.browser.new_page()
            page.goto(product_url, wait_until="domcontentloaded", timeout=30000)

            page.wait_for_timeout(3000)

            buy_box = page.get_by_test_id("buy-box")

            if "ناموجود" in buy_box.inner_text():
                return "Product is unavailable"

            price = buy_box.get_by_test_id("price-final").inner_text()
            return normalize_price(price)

        except PlaywrightError as e:
            print(f"Scraping failed: {e}")
            return "Extraction error"

        finally:
            if page is not None:
                page.close()

    def close(self):
        self.browser.close()
