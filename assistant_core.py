import json
import re

FILE = "data.json"

VALUE_WEIGHT = 100
PRIORITY_WEIGHT = 40
OVERPAY_WEIGHT = 150


# -------------------------
# DATA
# -------------------------
def load_items():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []


def save_items(items):
    with open(FILE, "w") as f:
        json.dump(items, f, indent=2)


def add_item(name, my_price, market_price, priority):
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


# -------------------------
# MATCHING
# -------------------------
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
    return len(overlap) >= 1


# -------------------------
# SCORE
# -------------------------
def score(item):
    try:
        priority_map = {"low": 1, "medium": 2, "high": 3}

        my_price = item.get("my_price")
        market_price = item.get("market_price")
        priority = item.get("priority", "low")

        if my_price is None or market_price is None:
            return -999

        discount = market_price - my_price
        discount_ratio = discount / market_price if market_price else 0

        priority_score = priority_map.get(priority, 1)

        priority_multiplier = {"low": 1.0, "medium": 1.0, "high": 1.2}
        priority_score *= priority_multiplier.get(priority, 1.0)

        overpay_penalty = abs(discount_ratio) * OVERPAY_WEIGHT if discount < 0 else 0

        return (
            discount_ratio * VALUE_WEIGHT +
            priority_score * PRIORITY_WEIGHT -
            overpay_penalty
        )

    except:
        return -999

def explain_score(item):
    reasons = []

    my = item.get("my_price")
    market = item.get("market_price")
    priority = item.get("priority", "low")

    if my is None or market is None:
        return ["Missing price data"]

    savings = market - my
    discount_pct = (savings / market) * 100 if market else 0

    # 💰 VALUE
    if savings > 0:
        reasons.append(f"💰 {round(discount_pct, 1)}% below market price")
    else:
        reasons.append(f"⚠️ Over market by ${round(abs(savings), 2)}")

    # 🎯 PRIORITY
    if priority == "high":
        reasons.append("🔥 High priority item")
    elif priority == "medium":
        reasons.append("⚖️ Medium priority balance")
    else:
        reasons.append("🟢 Low urgency item")

    # 🧠 LOGIC INSIGHT
    score_val = score(item)
    if score_val > 100:
        reasons.append("🚀 Extremely strong value score")
    elif score_val > 50:
        reasons.append("👍 Good value deal")

    return reasons

# -------------------------
# RECOMMEND (TOP 3)
# -------------------------
def recommend(top_n=3):
    items = load_items()

    valid = [
        i for i in items
        if not i.get("purchased")
        and i.get("my_price") is not None
        and i.get("market_price") is not None
    ]

    scored = [(i, score(i)) for i in valid]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:top_n]


# -------------------------
# NATURAL PARSE
# -------------------------
def parse_natural_add(text):
    text = text.lower()

    numbers = re.findall(r"\d+\.?\d*", text)
    numbers = [float(n) for n in numbers] if numbers else []

    my_price = numbers[0] if len(numbers) > 0 else None
    market_price = numbers[1] if len(numbers) > 1 else None

    if "high" in text:
        priority = "high"
    elif "medium" in text:
        priority = "medium"
    elif "low" in text:
        priority = "low"
    else:
        priority = "medium"

    name = extract_name(text)

    return {
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority
    }


def extract_name(text):
    text = re.split(r"\bfor\b|\bis\b|\bthat\b|\bbut\b", text)[0]
    words = text.split()

    stopwords = {"i", "found", "a", "an", "the", "this", "it", "its"}

    filtered = [w for w in words if w not in stopwords]
    return " ".join(filtered[:2]) or "unknown item"


# -------------------------
# MARK PURCHASED (FIXED)
# -------------------------
def mark_item_purchased(item_name):
    items = load_items()

    for item in items:
        if is_match(item_name, item["name"]):

            if item.get("purchased"):
                return {"success": False, "error": "Already marked as purchased"}

            item["purchased"] = True
            save_items(items)

            return {"success": True, "item": item}

    return {"success": False, "error": "Item not found"}

def classify_intent(text):
    text = text.lower().strip()

    # RECOMMEND
    if any(word in text for word in ["recommend", "suggest"]):
        return "recommend"

    if "buy" in text and any(w in text for w in ["what", "should", "next", "do"]):
        return "recommend"

    # ADD
    if text.startswith("add"):
        return "add"

    # LIST
    if any(word in text for word in ["list", "show", "items"]):
        return "list"

    # BUY
    if any(word in text for word in ["bought", "purchase", "purchased"]) or text.startswith("buy"):
        return "buy"

    return "unknown"