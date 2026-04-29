import assistant_core as core
import re

last_recommendation = None


def handle_input(text):
    global last_recommendation
    text = text.strip().lower()
    intent = core.classify_intent(text)

    print(f"\n[DEBUG] {intent}")

    # -------------------------
    # RECOMMEND
    # -------------------------
    if intent == "recommend":
        recs = core.recommend()
        if not recs:
            print("No recommendations.")
            return
        last_recommendation = recs
        for i, (item, sc) in enumerate(recs):
            savings = item["market_price"] - item["my_price"]
            print(f"\n💡 {i+1}. {item['name']}")
            print(f"- Score: {round(sc, 2)}")
            print(f"- Savings: ${round(savings, 2)}")

    # -------------------------
    # BUY
    # -------------------------
    elif intent == "buy":
        items = core.load_items()
        # 👉 pronoun handling
        if re.search(r"\b(it|that|this|the one)\b", text):
            if last_recommendation:
                item = last_recommendation[0][0]
                result = core.mark_item_purchased(item["name"])
                print(result["success"] and f"🛒 Bought {item['name']}" or result["error"])
            else:
                print("No recent recommendation.")
            return
        # normal match
        for item in items:
            if core.is_match(text, item["name"]):
                result = core.mark_item_purchased(item["name"])
                print(result["success"] and f"🛒 Bought {item['name']}" or result["error"])
                return
        print("Couldn't find item.")

    # -------------------------
    # LIST
    # -------------------------
    elif intent == "list":
        items = core.load_items()
        print("\n🧾 ITEMS:")
        for i in items:
            status = "✅" if i["purchased"] else "❌"
            print(f"{status} {i['name']}")

    # -------------------------
    # ADD
    # -------------------------
    else:
        parsed = core.parse_natural_add(text)
        if parsed["my_price"] and parsed["market_price"]:
            core.add_item(**parsed)
            print(f"Added {parsed['name']}")
        else:
            print("Need more info.")

def main():
    while True:
        text = input("\nYou: ")
        if text == "exit":
            break
        handle_input(text)

if __name__ == "__main__":
    main()