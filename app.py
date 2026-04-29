import streamlit as st
import assistant_core as core

st.title("🧠 Purchase Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_recommendation" not in st.session_state:
    st.session_state.last_recommendation = None


# -------------------------
# CHAT HISTORY
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -------------------------
# INPUT
# -------------------------
user_input = st.chat_input("What do you want to do?")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    intent = core.classify_intent(user_input)
    response = ""

    # -------------------------
    # RECOMMEND
    # -------------------------
    if intent == "recommend":
        recs = core.recommend()

        if not recs:
            response = "No recommendations."

        else:
            st.session_state.last_recommendation = recs

            response = "💡 **Top picks:**\n\n"

            for i, (item, sc) in enumerate(recs):
                savings = item["market_price"] - item["my_price"]

                response += f"**{i+1}. {item['name']}**\n"
                response += f"- Score: {round(sc, 2)}\n"
                response += f"- Savings: ${round(savings, 2)}\n\n"

    # -------------------------
    # BUY
    # -------------------------
    elif intent == "buy":

        items = core.load_items()

        # pronoun handling
        if any(w in user_input.lower() for w in ["it", "that", "this", "the one"]):

            recs = st.session_state.last_recommendation

            if recs:
                item = recs[0][0]
                result = core.mark_item_purchased(item["name"])
                response = result["success"] and f"🛒 Bought {item['name']}" or result["error"]
            else:
                response = "I don't know what you're referring to."

        else:
            for item in items:
                if core.is_match(user_input, item["name"]):
                    result = core.mark_item_purchased(item["name"])
                    response = result["success"] and f"🛒 Bought {item['name']}" or result["error"]
                    break
            else:
                response = "Couldn't find item."

    # -------------------------
    # LIST
    # -------------------------
    elif intent == "list":
        items = core.load_items()

        response = "🧾 Your items:\n\n"
        for i in items:
            status = "✅" if i["purchased"] else "❌"
            response += f"- {status} {i['name']}\n"

    # -------------------------
    # ADD
    # -------------------------
    else:
        parsed = core.parse_natural_add(user_input)

        if parsed["my_price"] and parsed["market_price"]:
            core.add_item(**parsed)
            response = f"✅ Added {parsed['name']}"
        else:
            response = "Need price + market price."

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)