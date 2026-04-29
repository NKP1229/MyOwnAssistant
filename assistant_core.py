import json
import re
FILE = "data.json"
VALUE_WEIGHT = 100
PRIORITY_WEIGHT = 40
OVERPAY_WEIGHT = 150

def add_item(name, my_price, market_price, priority):
    if not name.strip():
        return None
    items = load_items()
    item = {
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority,
        "purchased": False
    }
    items.append(item)
    save_items(items)
    return item

def load_items():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except:
        return []

def list_items():
    items = load_items()
    for i, item in enumerate(items):
        status = "✓" if item["purchased"] else " "
        print(f"{i}. [{status}] {item['name']}")

def save_items(items):
    with open(FILE, "w") as f:
        json.dump(items, f, indent=2)

def score(item):
    try:
        priority_map = {"low": 1, "medium": 2, "high": 3}
        my_price = item.get("my_price")
        market_price = item.get("market_price")
        priority = item.get("priority", "low")
        if my_price is None or market_price is None:
            return -999
        # 🧠 VALUE (discount %)
        discount = market_price - my_price
        discount_ratio = discount / market_price if market_price else 0
        # 🧠 PRIORITY
        priority_score = priority_map.get(priority, 1)
        # ✅ ADD IT RIGHT HERE
        priority_multiplier = {
            "low": 1.0,
            "medium": 1.0,
            "high": 1.2
        }
        priority_score *= priority_multiplier.get(priority, 1.0)
        # 🧠 OVERPAY PENALTY
        if discount < 0:
            overpay_penalty = abs(discount_ratio) * OVERPAY_WEIGHT
        else:
            overpay_penalty = 0
        # ⚖️ WEIGHTS
        final_score = (
            discount_ratio * VALUE_WEIGHT +
            priority_score * PRIORITY_WEIGHT -
            overpay_penalty
        )
        return final_score
    except:
        return -999

def recommend():
    items = load_items()
    valid_items = [
        i for i in items
        if not i.get("purchased")
        and i.get("my_price") is not None
        and i.get("market_price") is not None
    ]
    if not valid_items:
        return None
    # Optional: filter out bad deals
    if all(score(i) < 0 for i in valid_items):
        return None
    best = max(valid_items, key=score)
    return best

def parse_natural_add(text):
    text = text.lower()
    # Extract numbers (prices)
    numbers = re.findall(r"\d+\.?\d*", text)
    numbers = [float(n) for n in numbers] if numbers else []
    my_price = numbers[0] if len(numbers) > 0 else None
    market_price = numbers[1] if len(numbers) > 1 else None
    # Extract priority
    if "high" in text:
        priority = "high"
    elif "medium" in text:
        priority = "medium"
    elif "low" in text:
        priority = "low"
    else:
        priority = "medium"
    # take first few words as name
    name = extract_name(text)
    return {
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority
    }

def extract_name(text):
    text = text.lower()
    # Cut off everything after price indicators
    text = re.split(r"\bfor\b|\bis\b|\bthat\b|\bbut\b", text)[0]
    words = text.split()
    # Remove common filler words
    stopwords = {
        "i", "found", "a", "an", "the", "another", "new",
        "this", "it", "its"
    }
    filtered = [w for w in words if w not in stopwords]
    # Keep only meaningful words (limit to 2–3 words)
    name = " ".join(filtered[:2])
    return name if name else "unknown item"

def is_match(text, item_name):
    text_words = set(text.lower().split())
    item_words = set(item_name.lower().split())
    stopwords = {
        "i", "a", "the", "it", "is", "for", "and", "to",
        "found", "new", "that", "this", "usually", "bought"
    }
    text_words -= stopwords
    item_words -= stopwords
    overlap = text_words & item_words
    # Require at least 1 shared meaningful word
    return len(overlap) >= max(1, len(item_words) // 2)

def classify_intent(text):
    text = text.lower().strip()
    text = " ".join(text.split())
    # RECOMMEND (split into 2 clear paths)
    # Case 1: explicit recommendation words
    if any(word in text for word in ["recommend", "suggest"]):
        return "recommend"
    # Case 2: implicit "what should I buy"
    if "buy" in text and any(word in text for word in ["what", "should", "next", "do"]):
        return "recommend"
    # ADD
    if text.startswith("add"):
        return "add"
    # LIST
    if any(word in text for word in ["list", "show", "items"]):
        return "list"
    # BUY / MARK PURCHASED
    if any(word in text for word in ["bought", "purchase", "purchased"]) or text.startswith("buy "):
        return "buy"
    return "unknown"

def mark_item_purchased(text):
    items = load_items()
    for item in items:
        # ✅ exact match first (very important)
        if item["name"].lower() == text.lower():
            item["purchased"] = True
            save_items(items)
            return {"success": True, "item": item}
    for item in items:
        # ✅ fuzzy match fallback
        if is_match(text, item["name"]):
            item["purchased"] = True
            save_items(items)
            return {"success": True, "item": item}
    return {"success": False, "error": "Item not found"}
