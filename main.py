import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

from stores.digikala import Digikala
from stores.torob import Torob
from stores.techno_life import TechnoLife
from store_manager import StoreManager
from ai_matcher import Ai
from database import Database
from report_manager import ReportManager

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
CONFIG_FILE = BASE_DIR / "config.json"
NOT_FOUND = "NOT_FOUND"
STORE_NAMES = ("digikala", "torob", "technolife")


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON syntax: {error}"
        ) from error

    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object.")

    products = config.get("products")

    if not isinstance(products, list):
        raise ValueError("'products' must be a list.")

    config_ids = set()

    for index, product in enumerate(products, start=1):

        if not isinstance(product, dict):
            raise ValueError(
                f"Product #{index} must be an object."
            )

        config_id = product.get("config_id")
        name = product.get("name")

        if not isinstance(config_id, str) or not config_id.strip():
            raise ValueError(
                f"Product #{index} has an invalid config_id."
            )

        if config_id in config_ids:
            raise ValueError(
                f"Duplicate config_id found: {config_id}"
            )

        config_ids.add(config_id)

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Product #{index} has an invalid name."
            )

        if "active" in product and not isinstance(product["active"], bool):
            raise ValueError(
                f"Product '{name}' has an invalid active value."
            )

        for store_name in STORE_NAMES:
            url = product.get(f"{store_name}_url")

            if url is not None and not isinstance(url, str):
                raise ValueError(
                    f"Invalid {store_name}_url for product '{name}'."
                )

    return config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)


def main():
    config = load_config()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    stores = {}
    db = None

    try:
        db = Database()
        with sync_playwright() as playwright:

            stores["digikala"] = Digikala(playwright)
            stores["torob"] = Torob(playwright)
            stores["technolife"] = TechnoLife()

            needs_ai = any(
                product.get(f"{store_name}_url") is None
                for product in config["products"]
                if product.get("active", True)
                for store_name in STORE_NAMES
            )

            if not gemini_api_key:
                print(
                    "Warning: Gemini API key not found. "
                    "Skipping URL discovery."
                )

            elif needs_ai:
                store_manager = StoreManager(stores)
                ai = Ai()

                for product in config["products"]:
                    if not product.get("active", True):
                        continue

                    product_name = product["name"]
                    print(f"\nProcessing: {product_name}")

                    identified_results = {}

                    for store_name in STORE_NAMES:
                        url_key = f"{store_name}_url"
                        current_url = product.get(url_key)

                        if current_url is not None:
                            continue

                        print(f"Searching {store_name}...")

                        try:
                            found_urls = store_manager.find_product_url(
                                store_name,
                                product_name
                            )

                            identified_results[store_name] = found_urls

                        except Exception as error:
                            print(f"{store_name} failed: {error}")

                    if not any(identified_results.values()):
                        continue

                    try:
                        selected_ids = ai.matcher(
                            product_name,
                            identified_results
                        )
                    except Exception as error:
                        print(f"AI matching failed: {error}")
                        continue

                    for store_name, selected_id in selected_ids.items():
                        if store_name not in identified_results:
                            continue

                        url_key = f"{store_name}_url"

                        if selected_id is None:
                            continue

                        if selected_id == 0:
                            product[url_key] = NOT_FOUND
                            print(f"{store_name}: Product not found")
                            continue

                        candidates = identified_results[store_name]

                        matched_result = next(
                            (
                                result for result in candidates
                                if result["id"] == selected_id
                            ),
                            None
                        )

                        if matched_result is None:
                            print(
                                f"{store_name}: Invalid result ID "
                                f"{selected_id}"
                            )
                            continue

                        product[url_key] = matched_result["url"]
                        print(f"{store_name}: URL found")

                    save_config(config)

            else:
                print("All product URLs are already configured. "
                      "Skipping URL discovery.")

            # Phase 2: Price extraction.

            report_data = []
            for product in config["products"]:
                if not product.get("active", True):
                    continue

                product_name = product["name"]
                config_id = product["config_id"]

                prices = {}

                print(f"\nGetting prices: {product_name}")

                for store_name, store in stores.items():
                    url = product.get(f"{store_name}_url")

                    if not url or url == NOT_FOUND:
                        prices[f"{store_name}_price"] = None
                        continue

                    print(f"Getting {store_name} price...")

                    try:
                        result = store.get_price(url)

                    except Exception as error:
                        print(f"{store_name} failed: {error}")
                        prices[f"{store_name}_price"] = None
                        continue

                    if isinstance(result, int):
                        prices[f"{store_name}_price"] = result
                        print(f"{store_name}: {result:,}")

                    else:
                        prices[f"{store_name}_price"] = None
                        print(f"{store_name}: {result}")

                report_data.append({
                    "config_id": config_id,
                    "name": product_name,
                    "digikala_price": prices["digikala_price"],
                    "torob_price": prices["torob_price"],
                    "technolife_price": prices["technolife_price"],
                })

                if not any(
                        price is not None
                        for price in prices.values()
                ):
                    print(f"No prices extracted for {product_name}")
                    continue

                db.add_price_history(
                    config_id=config_id,
                    digikala_price=prices["digikala_price"],
                    torob_price=prices["torob_price"],
                    technolife_price=prices["technolife_price"],
                )

            report_manager = ReportManager(report_data)
            report_manager.generate_report()

    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
