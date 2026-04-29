import streamlit as st
import assistant_core as core

st.title("🧠 Purchase Assistant")

# -------------------------
# SESSION STATE (chat memory)
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------
# DISPLAY CHAT HISTORY
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------------
# USER INPUT
# -------------------------
user_input = st.chat_input("What do you want to do?")

if user_input:
    # show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # -------------------------
    # PROCESS INPUT
    # -------------------------
    intent = core.classify_intent(user_input)

    response = ""

    # RECOMMEND
    if intent == "recommend":
        best = core.recommend()
        if best:
            savings = best["market_price"] - best["my_price"]
            response = f"💡 You should buy: **{best['name']}**\n\n"
            response += f"- Priority: {best['priority']}\n"
            response += f"- Score: {round(core.score(best), 2)}\n"

            if savings >= 0:
                response += f"- Savings: ${round(savings, 2)}"
            else:
                response += f"- Overpay: ${round(abs(savings), 2)}"
        else:
            response = "No good deals right now."

    # ADD (natural language)
    elif intent == "unknown":
        parsed = core.parse_natural_add(user_input)

        if parsed["my_price"] and parsed["market_price"]:
            item = core.add_item(
                parsed["name"],
                parsed["my_price"],
                parsed["market_price"],
                parsed["priority"]
            )
            response = f"✅ Added **{item['name']}**"
        else:
            response = "I need more info (price / market price)."

    # LIST
    elif intent == "list":
        items = core.load_items()
        if not items:
            response = "No items yet."
        else:
            response = "🧾 Your items:\n"
            for item in items:
                status = "✅" if item["purchased"] else "❌"
                response += f"- {status} {item['name']}\n"

    # BUY
    elif intent == "buy":
        items = core.load_items()
        matched = None
        # 1. Strong match
        for item in items:
            if core.is_match(user_input, item["name"]):
                matched = item
                break
        # 2. Fallback: partial keyword match
        if not matched:
            for item in items:
                words = item["name"].lower().split()
                if any(word in user_input for word in words):
                    matched = item
                    break

        if matched:
            result = core.mark_item_purchased(matched["name"])
            if result["success"]:
                response = f"🛒 Marked **{matched['name']}** as purchased."
            else:
                response = result["error"]
        else:
            response = "Couldn't find that item."

    else:
        response = "I didn’t understand that."

    # -------------------------
    # SHOW RESPONSE
    # -------------------------
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)