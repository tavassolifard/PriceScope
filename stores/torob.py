from playwright.sync_api import Error as PlaywrightError
import json
from urllib.parse import urljoin
from urllib.parse import quote

class Torob:

    def __init__(self,playwright):
        self.playwright = playwright
        self.browser = self.playwright.chromium.launch(
            headless=True
        )

    def get_price(self,url):
        page = None

        try:
            page = self.browser.new_page()
            response = page.goto(url,wait_until="domcontentloaded",timeout=30000,)
            if response is None or response.status != 200:
                return f"HTTP error: {response.status if response else 'No response'}"
            page.wait_for_timeout(2000)
            scripts = page.locator('script[type="application/ld+json"]').all()

            for script in scripts:
                content = script.text_content()

                if not content:
                    continue

                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    continue

                if data.get("@type") == "Product":
                    offers = data.get("offers", {})
                    price = offers.get("lowPrice")

                    if price is not None:
                        if int(price) == 0:
                            return "Product is unavailable"
                        return int(price) // 10

            return "Price not found"

        except PlaywrightError as e:
            print(f"Scraping failed: {e}")
            return "Extraction error"
        finally:
            if page is not None:
                page.close()


    def search_product(self, query):
        page = None
        try:
            page = self.browser.new_page()

            url = (
                    "https://torob.com/search/?query="
                    + quote(query)
                    + "&_search_landing=header"
            )

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)

            products = page.locator('[data-testid="product-card"]')
            products.first.wait_for(
                state="visible",
                timeout=20000
            )
            results = []
            seen = set()

            for i in range(products.count()):
                item = products.nth(i)

                title = item.locator("h2").inner_text().strip()
                href = item.locator("xpath=ancestor::a").get_attribute("href")

                if not href or not title or href in seen:
                    continue

                seen.add(href)

                href = urljoin("https://torob.com", href)

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

    def close(self):
        self.browser.close()