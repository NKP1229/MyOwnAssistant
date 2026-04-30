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
            if not isinstance(data, list):
                return []
            # 🔧 FIX: ensure all fields exist
            for item in data:
                if "category" not in item:
                    item["category"] = "general"
                if "priority" not in item:
                    item["priority"] = "medium"
                if "purchased" not in item:
                    item["purchased"] = False
            return data
    except:
        return []

def save_items(items):
    with open(FILE, "w") as f:
        json.dump(items, f, indent=2)

def add_item(name, my_price, market_price, priority, category="general"):
    items = load_items()
    item = {
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority,
        "category": category,
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

def compare_items(query):
    items = load_items()
    # 1. Try category match first
    category = detect_category(query)
    matched = [
        i for i in items
        if i.get("category") == category and not i.get("purchased")
    ]
    # 2. If no category match → fallback to name match
    if len(matched) < 2:
        matched = [
            i for i in items
            if is_match(query, i["name"]) and not i.get("purchased")
        ]
    if len(matched) < 2:
        return None
    # Score and sort
    scored = [(i, score(i)) for i in matched]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

def compare_reasoning(a, b):
    reasons = []
    score_a = score(a)
    score_b = score(b)
    # 🧠 TIE DETECTION
    if abs(score_a - score_b) < 1e-6:
        return None, ["These items are equally good based on your criteria."]
    if score_a > score_b:
        winner, loser = a, b
    else:
        winner, loser = b, a
    # VALUE
    discount_a = a["market_price"] - a["my_price"]
    discount_b = b["market_price"] - b["my_price"]
    if discount_a > discount_b:
        reasons.append(f"{a['name']} has better savings")
    # PRIORITY
    priority_map = {"low": 1, "medium": 2, "high": 3}
    if priority_map[a["priority"]] > priority_map[b["priority"]]:
        reasons.append(f"{a['name']} is higher priority")
    # OVERPAY
    if a["my_price"] > a["market_price"]:
        reasons.append(f"{a['name']} is overpriced")
    if b["my_price"] > b["market_price"]:
        reasons.append(f"{b['name']} is overpriced")
    # FALLBACK (if no clear reason)
    if not reasons:
        reasons.append("Scores are very close, decision is marginal.")
    return winner, reasons

def compare_category(category):
    items = load_items()
    filtered = [
        i for i in items
        if i.get("category") == category
        and not i.get("purchased")
    ]
    if len(filtered) < 2:
        return []
    scored = [(item, score(item)) for item in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

# -------------------------
# NATURAL PARSE
# -------------------------
def detect_category(text):
    text = text.lower()
    if any(w in text for w in ["gpu", "rtx", "graphics"]):
        return "gpu"
    if any(w in text for w in ["ssd", "nvme", "storage"]):
        return "storage"
    if any(w in text for w in ["psu", "power"]):
        return "psu"
    if any(w in text for w in ["desk", "table"]):
        return "desk"
    return "general"

def parse_natural_add(text):
    text = text.lower()
    category = detect_category(text)
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
        "priority": priority,
        "category": category
    }

def extract_name(text):
    text = re.split(r"\bfor\b|\bis\b|\bthat\b|\bbut\b", text)[0]
    words = text.split()
    stopwords = {"i", "found", "a", "an", "the", "this", "it", "its"}
    filtered = [w for w in words if w not in stopwords]
    return " ".join(filtered[:2]) or "unknown item"

def extract_category(text):
    mapping = {
        "gpu": ["gpu", "graphics"],
        "psu": ["psu", "power"],
        "storage": ["ssd", "storage", "drive"],
        "desk": ["desk"],
        "chair": ["chair"],
        "keyboard": ["keyboard"]
    }
    for key, words in mapping.items():
        for w in words:
            if w in text:
                return key
    return None

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
    # COMPARE
    if "compare" in text or "vs" in text:
        return "compare"
    return "unknown"