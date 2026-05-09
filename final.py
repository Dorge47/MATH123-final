import json
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
file_in = "filtered_items_narrow.jsonl"
required_nutrients = [
  "energy-kcal_serving",
  "fiber_serving",
  "sugars_serving",
  "fat_serving",
  "calcium_serving",
  "carbohydrates_serving",
  "cholesterol_serving",
  "proteins_serving"
]
exchange_rates = { # To-USD exchange rates for every currency in our input data
  "USD": 1.0,
  "EUR": 1.18,
  "TWD": 0.032,
  "NOK": 0.11,
  "DOP": 0.017,
  "COP": 0.00027,
  "CAD": 0.73,
  "DKK": 0.16,
  "CZK": 0.048,
  "INR": 0.011,
  "ZAR": 0.061,
  "JPY": 0.0064,
  "SGD": 0.79,
  "RUB": 0.013,
  "KZT": 0.0022
}
names = []
prices = []
currencies = []

nutrient_lists = {
  nutrient: []
  for nutrient in required_nutrients
}

with open(file_in, "r", encoding="utf-8") as f:
  for line in f:
    try:
      item = json.loads(line)
    except json.JSONDecodeError:
      continue
    nutriments = item["nutriments"]
    names.append(item.get("product_name"))
    currencies.append(item["currency"])
    for nutrient in required_nutrients:
      nutrient_lists[nutrient].append(
        float(nutriments[nutrient])
      )
    # Money
    raw_price = float(item["price"])
    currency = item["currency"]
    if currency not in exchange_rates:
      raise ValueError(f"No exchange rate defined for currency {currency}")
    prices.append(raw_price * exchange_rates[currency])

# SciPy likes NumPy arrays instead of lists
prices = np.array(prices)
for nutrient in nutrient_lists:
  nutrient_lists[nutrient] = np.array(nutrient_lists[nutrient])

print(f"Loaded {len(prices):,} items")

constraint_list = [ # Pretty loose constraints for proof of concept
  LinearConstraint(nutrient_lists["energy-kcal_serving"], lb=1500, ub=2500),
  LinearConstraint(nutrient_lists["fiber_serving"], lb=25, ub=70),
  LinearConstraint(nutrient_lists["sugars_serving"], lb=0, ub=90),
  LinearConstraint(nutrient_lists["fat_serving"], lb=40, ub=80),
  LinearConstraint(nutrient_lists["calcium_serving"], lb=1, ub=2.5),
  LinearConstraint(nutrient_lists["carbohydrates_serving"], lb=130, ub=325),
  LinearConstraint(nutrient_lists["carbohydrates_serving"], lb=0, ub=300),
  LinearConstraint(nutrient_lists["proteins_serving"], lb=50, ub=125)
]

final_result = milp(
  c = prices,
  constraints = constraint_list,
  bounds = Bounds(0,30),
  integrality=np.ones(len(prices))
)

total_cost = 0
total_calories = 0
total_fiber = 0
total_sugars = 0
total_fat = 0
total_calcium = 0
total_carbohydrates = 0
total_cholesterol = 0
total_protein = 0

for i, qty in enumerate(final_result.x):
  qty = round(qty) # Getting decimal answers despite specifying integrality. Floating point rounding error??
  if qty <= 0:
    continue
  total_cost += prices[i] * qty
  total_calories += nutrient_lists["energy-kcal_serving"][i] * qty
  total_fiber += nutrient_lists["fiber_serving"][i] * qty
  total_sugars += nutrient_lists["sugars_serving"][i] * qty
  total_fat += nutrient_lists["fat_serving"][i] * qty
  total_calcium += nutrient_lists["calcium_serving"][i] * qty
  total_carbohydrates += nutrient_lists["carbohydrates_serving"][i] * qty
  total_cholesterol += nutrient_lists["cholesterol_serving"][i] * qty
  total_protein += nutrient_lists["proteins_serving"][i] * qty
  print(f"{qty:2d}x {names[i]}")

print()
print(f"Total cost: ${total_cost:.2f}")
print(f"Calories: {total_calories:.1f}")
print(f"Fiber: {total_fiber:.1f} g")
print(f"Sugar (total): {total_sugars:.1f} g")
print(f"Fat: {total_fat:.1f} g")
print(f"Calcium: {total_calcium:.1f} g")
print(f"Carbs: {total_carbohydrates:.1f} g")
print(f"Cholesterol: {total_cholesterol:.1f} g")
print(f"Protein: {total_protein:.1f}")
