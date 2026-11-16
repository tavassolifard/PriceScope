class StoreManager:

    def __init__(self, stores):
        self.stores = stores

    def find_product_url(self, store_name, product_name, existing_url=None):

        # Reuse an existing URL instead of searching again.
        if existing_url:
            return existing_url

        store = self.stores.get(store_name)

        if store is None:
            raise ValueError(f"Unknown store: {store_name}")

        search_results = store.search_product(product_name)
        print("Search results:", search_results)

        # Keep search failures separate from products not found.
        if isinstance(search_results, str):
            if search_results == "Search error":
                raise RuntimeError(
                    f"Search failed for {store_name}: {product_name}"
                )

            raise RuntimeError(
                f"Unexpected search response from {store_name}: "
                f"{search_results}"
            )

        if not search_results:
            return None

        # Give each result an ID for the AI matcher.
        identified_results = []

        for result_id, result in enumerate(search_results, start=1):
            identified_results.append({
                "id": result_id,
                "title": result["title"],
                "url": result["url"],
            })

        return identified_results
