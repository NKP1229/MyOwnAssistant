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
            st.write("🧾 Edit your items below:")
            edited = st.data_editor(
                items,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn("Item"),
                    "my_price": st.column_config.NumberColumn("Your Price"),
                    "market_price": st.column_config.NumberColumn("Market Price"),
                    "priority": st.column_config.SelectboxColumn(
                        "Priority",
                        options=["low", "medium", "high"]
                    ),
                    "category": st.column_config.SelectboxColumn(
                        "Category",
                        options=["gpu", "storage", "psu", "desk", "general"]
                    ),
                    "purchased": st.column_config.CheckboxColumn("Bought")
                }
            )
            # Save changes automatically
            core.save_items(edited)
            response = "✏️ Changes saved automatically."

    # =========================
    # COMPARE
    # =========================
    elif intent == "compare":
        category = core.extract_category(user_input)
        # -------------------------
        # 🔥 CASE 1: compare ALL in category
        # -------------------------
        if category:
            results = core.compare_category(category)
            if not results:
                response = f"Not enough items in category '{category}' to compare."
            else:
                response = f"⚔️ **All {category.upper()} comparison**\n\n"
                for i, (item, sc) in enumerate(results):
                    savings = item["market_price"] - item["my_price"]
                    response += f"### {i+1}. {item['name']}\n"
                    response += f"- Score: {round(sc, 2)}\n"
                    response += f"- Price: ${item['my_price']} (market ${item['market_price']})\n"
                    if savings >= 0:
                        response += f"- Savings: ${round(savings, 2)}\n"
                    else:
                        response += f"- Overpay: ${round(abs(savings), 2)}\n"
                    reasons = core.explain_score(item)
                    for r in reasons:
                        response += f"- {r}\n"
                    response += "\n"
                best = results[0][0]
                response += f"🏆 **Best {category}: {best['name']}**"
        # -------------------------
        # ⚔️ CASE 2: compare specific items (existing logic)
        # -------------------------
        else:
            results = core.compare_items(user_input)
            if not results:
                response = "I couldn't find enough items to compare."
            else:
                response = "⚔️ **Comparison**\n\n"
                for i, (item, sc) in enumerate(results):
                    savings = item["market_price"] - item["my_price"]
                    response += f"### {i+1}. {item['name']}\n"
                    response += f"- Score: {round(sc, 2)}\n"
                    response += f"- Price: ${item['my_price']} (market ${item['market_price']})\n"
                    if savings >= 0:
                        response += f"- Savings: ${round(savings, 2)}\n"
                    else:
                        response += f"- Overpay: ${round(abs(savings), 2)}\n"
                    reasons = core.explain_score(item)
                    for r in reasons:
                        response += f"- {r}\n"
                    response += "\n"
                best = results[0][0]
                response += f"\n🏆 **Best choice: {best['name']}**"

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