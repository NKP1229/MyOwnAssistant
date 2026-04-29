import streamlit as st
import assistant_core as core
import re
st.title("🧠 Purchase Assistant")
# -------------------------
# SESSION STATE
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_recommendation" not in st.session_state:
    st.session_state.last_recommendation = None
# -------------------------
# DISPLAY CHAT HISTORY
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
# -------------------------
# USER INPUT
# -------------------------
user_input = st.chat_input("What do you want to do?")
if user_input:
    user_input = user_input.strip()
    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    with st.chat_message("user"):
        st.markdown(user_input)
    # -------------------------
    # PROCESS INPUT
    # -------------------------
    intent = core.classify_intent(user_input)
    response = ""
    # -------------------------
    # RECOMMEND
    # -------------------------
    if intent == "recommend":
        best = core.recommend()
        if best:
            st.session_state.last_recommendation = best
            savings = best["market_price"] - best["my_price"]
            response = f"💡 **You should buy:** {best['name']}\n\n"
            response += f"- Priority: {best['priority']}\n"
            response += f"- Score: {round(core.score(best), 2)}\n"
            if savings >= 0:
                response += f"- Savings: ${round(savings, 2)}"
            else:
                response += f"- Overpay: ${round(abs(savings), 2)}"
        else:
            response = "No good deals right now."
    # -------------------------
    # BUY
    # -------------------------
    elif intent == "buy":
        items = core.load_items()
        # ✅ STEP 1: pronoun handling
        if re.search(r"\b(it|that|this|the one)\b", user_input.lower()):
            last = st.session_state.last_recommendation
            if last:
                result = core.mark_item_purchased(last["name"])
                if result["success"]:
                    response = f"🛒 Marked **{last['name']}** as purchased."
                else:
                    response = result["error"]
            else:
                response = "I'm not sure what you're referring to."
        else:
            # ✅ STEP 2: find matches
            matches = []
            for item in items:
                if core.is_match(user_input, item["name"]):
                    matches.append(item)
            # fallback keyword match
            if not matches:
                for item in items:
                    words = item["name"].lower().split()
                    if any(word in user_input.lower() for word in words):
                        matches.append(item)
            # ✅ STEP 3: resolve matches
            if len(matches) == 1:
                result = core.mark_item_purchased(matches[0]["name"])
                if result["success"]:
                    response = f"🛒 Marked **{matches[0]['name']}** as purchased."
                else:
                    response = result["error"]
            elif len(matches) > 1:
                response = "I found multiple matches:\n"
                for i, item in enumerate(matches):
                    response += f"{i}. {item['name']}\n"
                response += "\nBe more specific."
            else:
                response = "Couldn't find that item."
    # -------------------------
    # LIST
    # -------------------------
    elif intent == "list":
        items = core.load_items()
        if not items:
            response = "No items yet."
        else:
            response = "🧾 **Your items:**\n\n"
            for item in items:
                status = "✅" if item["purchased"] else "❌"
                response += f"- {status} {item['name']}\n"
    # -------------------------
    # UNKNOWN → try add
    # -------------------------
    else:
        parsed = core.parse_natural_add(user_input)
        if parsed["my_price"] is not None and parsed["market_price"] is not None:
            item = core.add_item(
                parsed["name"],
                parsed["my_price"],
                parsed["market_price"],
                parsed["priority"]
            )
            response = f"✅ Added **{item['name']}**"
        else:
            response = "I didn’t understand that."
    # -------------------------
    # SHOW RESPONSE
    # -------------------------
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })
    with st.chat_message("assistant"):
        st.markdown(response)