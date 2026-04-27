import json
import re

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
    if len(numbers) < 2:
        return None
    my_price = numbers[0]
    market_price = numbers[1]
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

def handle_buy_command(text):
    items = load_items()
    # Try to match item name
    for item in items:
        if item["name"].lower() in text:
            item["purchased"] = True
            save_items(items)
            print(f"Marked '{item['name']}' as purchased.")
            return
    # If user just says "bought"
    if text.strip() == "bought":
        print("Tell me what you bought, e.g.:")
        print("- bought corsair psu")
        return
    print("Couldn't find that item.")

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
    if text.startswith("buy ") or "bought" in text:
        return "buy"
    return "unknown"

def handle_input(text):
    intent = classify_intent(text)
    print(f"[DEBUG] text='{text}' | intent='{intent}'")
    if intent == "recommend":
        recommend()
    elif intent == "add":
        handle_add_command(text)
    # 👇 NEW: try natural add if unknown
    elif intent == "unknown":
        parsed = parse_natural_add(text)
        if parsed:
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
                print(f"Added '{parsed['name']}' to your list.")
            else:
                print("Cancelled.")
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