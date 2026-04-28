import json
import re
pending_item = None
pending_action = None
last_recommendation = None
FILE = "data.json"

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

def add_item():
    name = input("Item name: ")
    my_price = float(input("Your price: "))
    market_price = float(input("Market price: "))
    priority = input("Priority (low/medium/high): ")
    items = load_items()
    items.append({
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority,
        "purchased": False
    })
    save_items(items)

def score(item):
    try:
        priority_map = {"low": 1, "medium": 2, "high": 3}
        my_price = item.get("my_price")
        market_price = item.get("market_price")
        priority = item.get("priority", "low")
        if my_price is None or market_price is None:
            return -1
        savings = market_price - my_price
        # 🚨 Penalize bad or zero savings
        if savings <= 0:
            savings_score = -50
        else:
            savings_ratio = savings / market_price
            savings_score = savings_ratio * 100
        return (
            savings_score * 0.6 +
            priority_map.get(priority, 1) * 40
        )
    except:
        return -1
    
def recommend():
    global last_recommendation
    items = load_items()
    valid_items = [
        i for i in items
        if not i.get("purchased") and
        "my_price" in i and
        "market_price" in i
    ]
    if not valid_items:
        print("No valid items to recommend.")
        return
    best = max(valid_items, key=score)
    last_recommendation = best
    savings = best["market_price"] - best["my_price"]
    print("\n💡 Based on your items, here's what I recommend:")
    print(f"You should buy: {best['name']}")
    print("\nReasoning:")
    print(f"- Priority: {best['priority']}")
    print(f"- Savings: ${round(savings, 2)}")
    print(f"- Score: {round(score(best), 2)}")

def list_items():
    items = load_items()
    for i, item in enumerate(items):
        status = "✓" if item["purchased"] else " "
        print(f"{i}. [{status}] {item['name']}")

def mark_purchased():
    list_items()
    index = int(input("Which item did you buy? "))
    items = load_items()
    items[index]["purchased"] = True
    save_items(items)

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

def handle_add_command(text):
    try:
        parts = text.split()
        # format: add name my_price market_price priority
        name = " ".join(parts[1:-3])
        my_price = float(parts[-3])
        market_price = float(parts[-2])
        priority = parts[-1]
        items = load_items()
        items.append({
            "name": name,
            "my_price": my_price,
            "market_price": market_price,
            "priority": priority,
            "purchased": False
        })
        save_items(items)
        print(f"Added: {name}")
    except:
        print("Format: add <name> <your_price> <market_price> <priority>")

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

def handle_buy_command(text):
    global last_recommendation
    items = load_items()
    # Try index-based match
    # 👇 NEW: handle "that" / "it"
    if any(phrase in text for phrase in [
        "that", "it", "the one", "the item", "that one"
    ]):
        if last_recommendation:
            mark_item_purchased(last_recommendation["name"])
            return
        else:
            print("I'm not sure what you're referring to.")
            return
    numbers = re.findall(r"\d+", text)
    if numbers:
        idx = int(numbers[0])
        if 0 <= idx < len(items):
            mark_item_purchased(items[idx]["name"])
            return
    # Try name match (with multi-match support)
    matches = []
    for item in items:
        if is_match(text, item["name"]):
            matches.append(item)
    # 👇 Handle results
    if len(matches) == 1:
        mark_item_purchased(matches[0]["name"])
        return
    elif len(matches) > 1:
        print("I found multiple matching items:")
        for i, item in enumerate(matches):
            print(f"{i}. {item['name']}")
        choice = input("Which one did you buy? (number): ")
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(matches):
                mark_item_purchased(matches[idx]["name"])
                return
        print("Invalid selection.")
        return
    # Fallback
    print("What did you buy? You can say:")
    list_items()

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

def confirm_and_add(parsed):
    print("\nI understood:")
    print(f"- Item: {parsed['name']}")
    print(f"- Your price: {parsed['my_price']}")
    print(f"- Market price: {parsed['market_price']}")
    print(f"- Priority: {parsed['priority']}")
    confirm = input("Add this item? (y/n): ").lower()
    if confirm == "y":
        items = load_items()
        items.append({
            "name": parsed["name"],
            "my_price": parsed["my_price"],
            "market_price": parsed["market_price"],
            "priority": parsed["priority"],
            "purchased": False
        })
        save_items(items)
        print(f"Added '{parsed['name']}'.")
    else:
        print("Cancelled.")

def handle_followup(text):
    global pending_item
    numbers = [float(n) for n in re.findall(r"\d+\.?\d*", text)]
    if pending_item["my_price"] is None and numbers:
        pending_item["my_price"] = numbers[0]
        print(f"Got it. Your price: {numbers[0]}")
        return
    if pending_item["market_price"] is None and numbers:
        pending_item["market_price"] = numbers[0]
        print(f"Got it. Market price: {numbers[0]}")
        confirm_and_add(pending_item)
        pending_item = None
        return
    print("I still need a number (price).")

def handle_input(text):
    global pending_action
    global pending_item
    text = text.strip().lower()
    # 👇 HANDLE FOLLOW-UP RESPONSES FIRST
    if pending_action == "recommend_followup":
        if text in ["yes", "y", "sure", "ok", "yeah", "yep", "yup", "yea", "yessir", "duh", "obviously"]:
            pending_action = None
            recommend()
            return
        elif text in ["no", "n", "nah", "nope", "not"]:
            pending_action = None
            print("Is there anything else I can help with?")
            return
        else:
            print("Please answer yes or no.")
            return
    intent = classify_intent(text)
    print(f"[DEBUG] text='{text}' | intent='{intent}'")
    if intent == "recommend":
        recommend()
    elif intent == "add":
        handle_add_command(text)
    # 👇 NEW: try natural add if unknown
    elif intent == "unknown":
        # Step 1: follow-up
        if pending_item:
            handle_followup(text)
            return
        # Step 2: try parsing as NEW item FIRST
        parsed = parse_natural_add(text)
        if parsed:
            missing_fields = []
            if parsed["my_price"] is None:
                missing_fields.append("your price")
            if parsed["market_price"] is None:
                missing_fields.append("market price")
            if missing_fields:
                pending_item = parsed
                print(f"I need more info: {', '.join(missing_fields)}")
                return
            confirm_and_add(parsed)
            return
        # Step 3: ONLY IF parsing fails → try matching existing items
        items = load_items()
        matches = []
        for item in items:
            if is_match(text, item["name"]):
                matches.append(item)
        if len(matches) == 1:
            mark_item_purchased(matches[0]["name"])
            return
        elif len(matches) > 1:
            print("I found multiple matching items:")
            for i, item in enumerate(matches):
                print(f"{i}. {item['name']}")
            choice = input("Which one did you buy? (number): ")
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(matches):
                    mark_item_purchased(matches[idx]["name"])
                    return
            print("Invalid selection.")
            return
        print("I didn’t understand that. Try:")
        # 👇 Step 1: If we're in follow-up mode
        if pending_item:
            handle_followup(text)
            return
        items = load_items()
        # 👇 Step 2: Try matching existing item by name
        for item in items:
            if text.strip() in item["name"].lower():
                mark_item_purchased(item["name"])
                return
        # 👇 Step 3: Try fuzzy match (partial match)
        for item in items:
            if any(word in item["name"].lower() for word in text.split()):
                mark_item_purchased(item["name"])
                return
        # 👇 Step 4: Only now try parsing as new item
        parsed = parse_natural_add(text)
        if parsed:
            missing_fields = []
            if parsed["my_price"] is None:
                missing_fields.append("your price")
            if parsed["market_price"] is None:
                missing_fields.append("market price")
            # 👇 If missing info → ask instead of confirming
            if missing_fields:
                pending_item = parsed
                print(f"I need more info: {', '.join(missing_fields)}")
                return
            # 👇 Only confirm if complete
            confirm_and_add(parsed)
            return
        print("I didn’t understand that. Try:")
        print("- add laptop 900 1200 high")
        print("- what should i buy")
        print("- bought corsair psu")
    elif intent == "list":
        list_items()
    elif intent == "buy":
        handle_buy_command(text)

def main():
    while True:
        text = input("\nYou: ").lower()
        if text == "exit":
            break
        handle_input(text)

if __name__ == "__main__":
    main()