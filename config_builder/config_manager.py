import json


def build_config(products, next_config_id):
    config = {
        "next_config_id": next_config_id,
        "products": []
    }

    seen_ids = set()

    for product in products:
        config_id = product["config_id"]

        if config_id in seen_ids:
            raise ValueError(
                f"Duplicate config_id: {config_id}"
            )

        seen_ids.add(config_id)

        item = {
            "config_id": config_id,
            "name": product["name"],
            "active": product["active_check"].isChecked()
        }

        for store_key, widgets in product["store_widgets"].items():
            ai_enabled = widgets["ai_check"].isChecked()
            url = widgets["url_input"].text().strip()

            if ai_enabled:
                item[f"{store_key}_url"] = None

            else:
                if not url:
                    raise ValueError(
                        f"Enter a URL or enable AI for "
                        f"{product['name']} - {store_key}."
                    )

                item[f"{store_key}_url"] = url

        config["products"].append(item)

    return config


def load_config(path):
    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Invalid configuration format.")

    products = config.get("products")

    if not isinstance(products, list):
        raise ValueError(
            "The configuration must contain a products list."
        )

    seen_ids = set()

    for index, product in enumerate(products, start=1):
        if not isinstance(product, dict):
            raise ValueError(
                f"Invalid product entry at position {index}."
            )

        config_id = product.get("config_id")
        name = product.get("name")

        if (
                not isinstance(config_id, str)
                or not config_id.isdigit()
                or int(config_id) < 1
        ):
            raise ValueError(
                f"Invalid config_id for product #{index}."
            )

        if config_id in seen_ids:
            raise ValueError(
                f"Duplicate config_id: {config_id}"
            )

        seen_ids.add(config_id)

        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Invalid product name for product #{index}."
            )

        if "active" in product and not isinstance(
                product["active"], bool
        ):
            raise ValueError(
                f"Invalid active value for product '{name}'."
            )

    max_id = max(
        (int(product["config_id"]) for product in products),
        default=0
    )

    next_id = config.get("next_config_id", max_id + 1)

    if (
            isinstance(next_id, bool)
            or not isinstance(next_id, int)
            or next_id < 1
    ):
        raise ValueError("Invalid next_config_id.")

    loaded_next_id = max(next_id, max_id + 1)

    return products, loaded_next_id


def save_config(path, config):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=4
        )
