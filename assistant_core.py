import json
FILE = "data.json"

def load_items():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except:
        return []

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
            overpay_penalty = abs(discount_ratio) * 150
        else:
            overpay_penalty = 0
        # ⚖️ WEIGHTS
        VALUE_WEIGHT = 100
        PRIORITY_WEIGHT = 40
        final_score = (
            discount_ratio * VALUE_WEIGHT +
            priority_score * PRIORITY_WEIGHT -
            overpay_penalty
        )
        return final_score
    except:
        return -999

def recommend():
    global last_recommendation
    items = load_items()
    valid_items = [
        i for i in items
        if not i.get("purchased")
        and i.get("my_price") is not None
        and i.get("market_price") is not None
        and i["my_price"] <= i["market_price"]  # 🚨 key line
    ]
    bad_items = [
        i for i in items
        if not i.get("purchased")
        and i.get("my_price") is not None
        and i.get("market_price") is not None
        and i["my_price"] > i["market_price"]
    ]
    if bad_items and not valid_items:
        print("All remaining items are above market price.")
        print("You may want to wait for better deals.")
        return
    best = max(valid_items, key=score)
    last_recommendation = best
    savings = best["market_price"] - best["my_price"]
    discount_pct = (savings / best["market_price"]) * 100 if best["market_price"] else 0
    print("\n💡 Based on your items, here's what I recommend:")
    print(f"You should buy: {best['name']}")
    print("\nReasoning:")
    print(f"- Priority: {best['priority']}")
    if savings >= 0:
        print(f"- Discount: {round(discount_pct, 1)}% (${round(savings, 2)} off)")
    else:
        print(f"- Over market by: ${round(abs(savings), 2)}")
    print(f"- Score: {round(score(best), 2)}")

def parse_natural_add(text):
    text = text.lower()
    # Extract numbers (prices)
    numbers = re.findall(r"\d+\.?\d*", text)
    numbers = [float(n) for n in numbers]
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
    # Try to extract item name (very rough)
    words = text.split("for")[0].split()
    # remove filler words
    stopwords = ["i", "found", "a", "for", "but", "its", "it's", "usually"]
    filtered = [w for w in words if w not in stopwords]
    # remove numbers and priority words
    filtered = [
        w for w in filtered
        if not re.match(r"\d+\.?\d*", w) and w not in ["low", "medium", "high"]
    ]
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
    text_words = set(text.split())
    item_words = set(item_name.lower().split())
    # Remove useless words
    stopwords = {
        "i", "a", "the", "it", "is", "for", "and", "to",
        "found", "new", "that", "this", "usually"
    }
    text_words = text_words - stopwords
    # Count meaningful overlap
    overlap = text_words & item_words
    return len(overlap) >= 1  # require at least 1 meaningful word

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

def mark_item_purchased(item_name):
    global pending_action
    items = load_items()
    for item in items:
        if item["name"].lower() == item_name.lower():
            item["purchased"] = True
            save_items(items)
            print(f"Marked '{item['name']}' as purchased.")
            pending_action = "recommend_followup"
            print("Nice—want a new recommendation? (yes/no)")
            return
    print("Couldn't find that item.")
