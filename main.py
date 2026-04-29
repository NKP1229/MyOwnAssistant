import assistant_core as core
import re

pending_item = None
last_recommendation = None

def handle_input(text):
    global pending_item, last_recommendation
    text = text.strip().lower()
    intent = core.classify_intent(text)
    print(f"[DEBUG] text='{text}' | intent='{intent}'")
    # -------------------
    # RECOMMEND
    # -------------------
    if intent == "recommend":
        global last_recommendation
        best = core.recommend()
        if best:
            savings = best["market_price"] - best["my_price"]
            last_recommendation = best
            print(f"\n💡 You should buy: {best['name']}")
            print(f"Priority: {best['priority']}")
            print(f"Score: {round(core.score(best), 2)}")
            print(f"Savings: ${round(savings, 2)}")
        else:
            print("No good items to recommend.")
    # -------------------
    # ADD
    # -------------------
    elif intent == "add":
        print("Use: add <name> <your_price> <market_price> <priority>")
    # -------------------
    # LIST
    # -------------------
    elif intent == "list":
        items = core.load_items()
        print("\n🧾 Your items:\n")
        for item in items:
            status = "✅" if item["purchased"] else "❌"
            print(f"{status} {item['name']}")
    # -------------------
    # BUY
    # -------------------
    elif intent == "buy":
        global last_recommendation
        print(f"[DEBUG BUY] text = {text}")
        # 👇 STEP 1: pronoun handling FIRST
        if re.search(r"\b(it|that|this|the one)\b", text):
            print("[DEBUG] pronoun detected")
            if last_recommendation:
                result = core.mark_item_purchased(last_recommendation["name"])
                if result["success"]:
                    print(f"🛒 Marked {last_recommendation['name']} as purchased.")
                else:
                    print(result["error"])
            else:
                print("I'm not sure what you're referring to.")
            return
        # 👇 STEP 2: normal matching
        items = core.load_items()
        matches = []
        for item in items:
            if core.is_match(text, item["name"]):
                matches.append(item)
        if len(matches) == 1:
            result = core.mark_item_purchased(matches[0]["name"])
            if result["success"]:
                print(f"🛒 Marked {matches[0]['name']} as purchased.")
            else:
                print(result["error"])
        elif len(matches) > 1:
            print("I found multiple matches:")
            for i, item in enumerate(matches):
                print(f"{i}. {item['name']}")
            choice = input("Which one? (number): ")
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(matches):
                    core.mark_item_purchased(matches[idx]["name"])
                    print(f"🛒 Marked {matches[idx]['name']} as purchased.")
        else:
            print("Couldn't find that item.")
    # -------------------
    # UNKNOWN → try add
    # -------------------
    else:
        parsed = core.parse_natural_add(text)
        if parsed["my_price"] and parsed["market_price"]:
            core.add_item(
                parsed["name"],
                parsed["my_price"],
                parsed["market_price"],
                parsed["priority"]
            )
            print(f"Added '{parsed['name']}'")
        else:
            print("I didn’t understand that.")
def main():
    while True:
        text = input("\nYou: ")
        if text == "exit":
            break
        handle_input(text)
if __name__ == "__main__":
    main()