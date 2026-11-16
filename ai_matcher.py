from google import genai
from pydantic import BaseModel
from typing import Optional


class AiResponse(BaseModel):
    digikala: Optional[int] = None
    torob: Optional[int] = None
    technolife: Optional[int] = None


class Ai:
    def __init__(self):
        self.client = genai.Client()

    def matcher(self, product_name, search_results):

        titles_only = {
            store_name: [
                {
                    "id": result["id"],
                    "title": result["title"]
                }
                for result in results
            ]
            for store_name, results in search_results.items() if results
        }

        prompt = f"""
        You are a product-matching assistant.

        Identify matching products independently for each store.

        Target product:
        {product_name}

        Search results grouped by store:
        {titles_only}

        Rules:
        1. Select a result only if its product identity matches the target.

        2. Compare the brand, model, generation, and all specifications
           explicitly stated in the target product name.

        3. Specifications not stated in the target product name do not
            need to match a particular value.

        4. Never ignore any specification explicitly stated in the target
           product name. For example, a product with a different capacity,
           size, or model variant is not a match when that difference is
           explicitly specified in the target.

        5. If multiple results match, select the first suitable result
           within that store's results.

        6. If results exist but none matches, return 0 for that store.
           If no results were provided, return null.

        7. Evaluate each store independently. Never transfer IDs
           between stores or invent or modify result IDs.

        Output:
        Return one ID, 0, or null for each store, following the
        provided response schema. Do not include explanations.
        """

        interaction = self.client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": AiResponse.model_json_schema(),
            },
            timeout=30
        )

        response = AiResponse.model_validate_json(
            interaction.output_text
        )

        selected_ids = response.model_dump()

        for store_name, selected_id in selected_ids.items():
            candidates = search_results.get(store_name)

            if not candidates:
                if selected_id is not None:
                    raise ValueError(
                        f"AI returned {selected_id} for "
                        f"{store_name}, but no candidates exist."
                    )
                continue

            if selected_id is None or selected_id == 0:
                continue

            valid_ids = {
                result["id"] for result in candidates
            }

            if selected_id not in valid_ids:
                raise ValueError(
                    f"Invalid AI result ID for {store_name}: "
                    f"{selected_id}"
                )

        return selected_ids
