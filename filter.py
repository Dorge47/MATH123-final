import json
file_in = "openfoodfacts-products.jsonl" # https://world.openfoodfacts.org/data#:~:text=JSONL%20data%20export
file_out = "filtered_items_narrow.jsonl" # https://raw.githubusercontent.com/Dorge47/MATH123-final/refs/heads/main/filtered_items_narrow.jsonl
file_prices = "prices.jsonl" # https://prices.openfoodfacts.org/data/prices.jsonl.gz
count_in = 0
count_out = 0
count_prices = 0
keep_properties = [ # These are the only properties we care about
    "_id",
    "product_name",
    "serving_size",
    "nutriscore_grade",
    "nutriments"
]
required_nutrients = [ # Every item must have these per-serving nutrient values defined
    "energy-kcal_serving",
    "fiber_serving",
    "sugars_serving",
    "fat_serving",
    "calcium_serving",
    "carbohydrates_serving",
    "cholesterol_serving",
    "proteins_serving"
]

price_by_code = {} # Define a dict with price data for quick lookup

with open(file_prices, "r", encoding="utf-8") as fprice:
    for line in fprice: # Stream one line at a time
        try:
            price_item = json.loads(line)
        except json.JSONDecodeError: # Skip invalid JSON
            continue
        raw_code = price_item.get("product_code")
        if raw_code is None: # Skip items with null product codes
            continue
        try:
            code = int(raw_code)
        except (ValueError, TypeError):
            continue
        price_by_code[code] = {
            "currency": price_item.get("currency"),
            "price": price_item.get("price"),
        }
        count_prices += 1
        if count_prices % 10_000 == 0:
            print(f"Loaded {count_prices:,} prices")
print(f"Finished loading {len(price_by_code):,} price records")

with open(file_in, "r", encoding="utf-8") as fin, \
     open(file_out, "w", encoding="utf-8") as fout:
    for line in fin:
        count_in += 1
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if count_in % 10_000 == 0:
            print(f"Processed {count_in:,} lines, kept {count_out:,}") # Keep track of how many items have been filtered
        try:
            code = int(item.get("_id"))
        except (ValueError, TypeError):
            continue
        price_info = price_by_code.get(code)
        if price_info is None:
            continue
        states_tags = item.get("states_tags", [])
        if "en:nutrition-facts-completed" not in states_tags: # Skip if insufficient data
            continue
        if "en:product-name-completed" not in states_tags:
            continue
        if "serving_size" not in item:
            continue
        nutriments = item.get("nutriments")
        if not nutriments:
            continue
        if not all(nutrient in nutriments for nutrient in required_nutrients):
            continue
        filtered_item = { # Ditch any properties not in keep_properties list
            key: item[key]
            for key in keep_properties
            if key in item
        }
        filtered_item["product_code"] = code # Append price data
        filtered_item["currency"] = price_info["currency"]
        filtered_item["price"] = price_info["price"]

        fout.write(json.dumps(filtered_item) + "\n") # Output to file line-by-line
        count_out += 1

print(f"Done. Kept {count_out:,} out of {count_in:,}")
