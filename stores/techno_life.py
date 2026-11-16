import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from utils import normalize_price


class TechnoLife:
    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def get_price(self, url):
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            if "ناموجود" in soup.get_text(" ", strip=True):
                return "Product is unavailable"

            price_section = soup.select_one(
                "div.flex.w-full.justify-end.px-4.pb-4.pt-5"
            )

            if price_section:
                price = price_section.select_one(
                    "div.flex.items-center p.font-semiBold.text-primary-shade-1"
                )

                if price:
                    return normalize_price(price.get_text(strip=True))
                else:
                    return "Price not found"
            else:
                return "Price section not found"

        except requests.RequestException as e:
            print(f"Scraping failed: {e}")
            return "Extraction error"

    def search_product(self, query):
        try:
            url = (
                "https://www.technolife.com/product/list/search"
                f"?keywords={quote(query)}"
            )

            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            seen = set()
            if "کالایی یافت نشد." in soup.get_text(" ", strip=True):
                return []
            for a in soup.select("a[href*='/product-']"):
                href = a.get("href")
                title = a.get_text(" ", strip=True)
                if not href or not title or href in seen:
                    continue

                seen.add(href)

                results.append({
                    "title": title,
                    "url": urljoin("https://www.technolife.com", href)
                })

                if len(results) == 5:
                    break

            return results

        except requests.RequestException as e:
            print(f"Search failed: {e}")
            return "Search error"
