import streamlit as st
import assistant_core as core

st.title("🧠 Purchase Assistant")

# -------------------------
# STATE
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_recs" not in st.session_state:
    st.session_state.last_recs = []

# -------------------------
# CHAT HISTORY
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------
# INPUT
# -------------------------
user_input = st.chat_input("Ask me anything...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})
    intent = core.classify_intent(user_input)

    response = ""

    # =========================
    # RECOMMEND (TOP 3)
    # =========================
    if intent == "recommend":

        recs = core.recommend(top_n=3)

        if not recs:
            response = "No good recommendations right now."

        else:
            st.session_state.last_recs = recs

            response = "💡 **Top recommendations**\n\n"

            for i, (item, sc) in enumerate(recs, start=1):

                savings = item["market_price"] - item["my_price"]
                reasons = core.explain_score(item)

                response += f"### {i}. {item['name']}\n"
                response += f"- Score: {round(sc, 2)}\n"
                response += f"- Savings: ${round(savings, 2)}\n\n"

                response += "**Why this?**\n"
                for r in reasons:
                    response += f"- {r}\n"

                response += "\n---\n"

    # =========================
    # BUY ITEM (SMART MATCH)
    # =========================
    elif intent == "buy":

        items = core.load_items()

        # pronoun handling ("it", "that", etc.)
        if any(w in user_input.lower() for w in ["it", "that", "this", "the one"]):

            if st.session_state.last_recs:
                item = st.session_state.last_recs[0][0]

                result = core.mark_item_purchased(item["name"])

                if result["success"]:
                    response = f"🛒 Marked **{item['name']}** as purchased."
                else:
                    response = result["error"]

            else:
                response = "I'm not sure what you're referring to."

        else:
            matched = None

            for item in items:
                if core.is_match(user_input, item["name"]):
                    matched = item
                    break

            if matched:
                result = core.mark_item_purchased(matched["name"])
                response = (
                    f"🛒 Marked **{matched['name']}** as purchased."
                    if result["success"] else result["error"]
                )
            else:
                response = "Couldn't find that item."

    # =========================
    # LIST
    # =========================
    elif intent == "list":

        items = core.load_items()

        if not items:
            response = "No items yet."
        else:
            response = "🧾 **Your items**\n\n"
            for i in items:
                status = "✅" if i["purchased"] else "❌"
                response += f"- {status} {i['name']}\n"

    # =========================
    # ITEM INSPECTION MODE
    # =========================
    elif intent == "unknown":

        items = core.load_items()

        matched = None
        for item in items:
            if core.is_match(user_input, item["name"]):
                matched = item
                break

        if matched:

            reasons = core.explain_score(matched)

            response = f"📦 **{matched['name']}**\n\n"
            response += f"- Your price: ${matched['my_price']}\n"
            response += f"- Market price: ${matched['market_price']}\n"
            response += f"- Priority: {matched['priority']}\n\n"

            response += "**Analysis**\n"
            for r in reasons:
                response += f"- {r}\n"

        else:
            parsed = core.parse_natural_add(user_input)

            if parsed["my_price"] and parsed["market_price"]:
                item = core.add_item(**parsed)
                response = f"✅ Added **{item['name']}**"
            else:
                response = "I didn’t understand that. Try 'what should I buy?' or 'tell me about GPU'."

    # =========================
    # OUTPUT
    # =========================
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)