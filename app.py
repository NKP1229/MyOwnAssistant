import streamlit as st
import assistant_core as core

st.title("🧠 Purchase Assistant")

# -------------------------
# SIDEBAR FILTERS (optional user control)
# -------------------------
st.sidebar.header("🔍 Filters")
max_price = st.sidebar.slider("Max price", 0, 2000, 2000)
priority_filter = st.sidebar.selectbox(
    "Priority",
    ["all", "high", "medium", "low"]
)

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
            response = "🧾 **Your items by category:**\n\n"
            grouped = {}
            for item in items:
                cat = item.get("category", "uncategorized")
                grouped.setdefault(cat, []).append(item)
            for cat, group_items in grouped.items():
                response += f"## {cat.upper()}\n"
                for item in group_items:
                    status = "✅" if item["purchased"] else "❌"
                    savings = item["market_price"] - item["my_price"]
                    score_val = round(core.score(item), 2)
                    response += f"**{status} {item['name']}**\n"
                    response += f"- 💰 Price: ${item['my_price']} (market ${item['market_price']})\n"
                    response += f"- 📊 Score: {score_val}\n"
                    response += f"- 🎯 Priority: {item['priority']}\n"
                    if savings >= 0:
                        response += f"- 🟢 Savings: ${round(savings, 2)}\n"
                    else:
                        response += f"- 🔴 Overpay: ${round(abs(savings), 2)}\n"
                    response += "\n"
                response += "---\n"

    # =========================
    # COMPARE
    # =========================
    elif intent == "compare":
        category = core.extract_category(user_input)
        # -------------------------
        # LOAD + APPLY FILTERS
        # -------------------------
        items = core.load_items()
        items = core.apply_user_filters(items, max_price, priority_filter)
        results = None
        title = ""
        # -------------------------
        # CASE 1: CATEGORY
        # -------------------------
        if category:
            results = core.compare_category(category, items)
            title = f"⚔️ **All {category.upper()} comparison**\n\n"
        # -------------------------
        # CASE 2: DIRECT ITEM MATCH
        # -------------------------
        if not results:
            results = core.compare_items(user_input)
            if results:
                title = "⚔️ **Comparison**\n\n"
        # -------------------------
        # CASE 3: SMART FILTER
        # -------------------------
        if not results:
            results = core.filter_items(user_input)
            if results:
                title = "⚔️ **Smart comparison**\n\n"
        # -------------------------
        # FINAL CHECK
        # -------------------------
        if not results or len(results) < 2:
            response = "Not enough items to compare."
        else:
            response = title
            # ✅ SAVE for follow-ups
            st.session_state.last_compare = results
            # -------------------------
            # SHOW ITEMS
            # -------------------------
            for i, (item, sc) in enumerate(results[:5]):
                savings = item["market_price"] - item["my_price"]
                response += f"### {i+1}. {item['name']}\n"
                response += f"- Score: {round(sc, 2)}\n"
                response += f"- Price: ${item['my_price']} (market ${item['market_price']})\n"
                if savings >= 0:
                    response += f"- Savings: ${round(savings, 2)}\n"
                else:
                    response += f"- Overpay: ${round(abs(savings), 2)}\n"
                # -------------------------
                # 🔥 SMART TAGS (UX BOOST)
                # -------------------------
                if sc > 150:
                    response += "🚀 Elite deal\n"
                elif sc > 100:
                    response += "🔥 Strong buy\n"
                elif sc > 50:
                    response += "👍 Solid option\n"
                else:
                    response += "🤔 Consider waiting\n"
                # WHY
                for r in core.explain_score(item):
                    response += f"- {r}\n"
                response += "\n"
            # -------------------------
            # 🏆 BEST
            # -------------------------
            best = results[0][0]
            response += f"🏆 **Best choice: {best['name']}**\n"
            # -------------------------
            # 🧠 DECISION SUMMARY
            # -------------------------
            if len(results) >= 2:
                second = results[1][0]
                diff = core.score(best) - core.score(second)
                response += "\n🧠 **Decision Summary**\n"
                if diff > 40:
                    response += f"- {best['name']} is a clear winner\n"
                else:
                    response += "- These options are very close in value\n"
                # -------------------------
                # 🧠 WHY A > B
                # -------------------------
                winner, reasons = core.compare_reasoning(best, second)
                if winner is None:
                    response += "\n🧠 **Comparison insight**\n"
                    for r in reasons:
                        response += f"- {r}\n"
                else:
                    other = second if winner == best else best
                    response += f"\n🧠 **Why {winner['name']} beats {other['name']}**\n"
                    for r in reasons:
                        response += f"- {r}\n"
            # -------------------------
            # 💬 SUGGESTIONS
            # -------------------------
            response += "\n💬 **Try asking:**\n"
            response += "- compare under 200\n"
            response += "- compare gpu\n"
            response += "- why is #1 better than #2\n"

    # =========================
    # ITEM INSPECTION MODE
    # =========================
    elif intent == "unknown":
        items = core.load_items()
        # =========================
        # 1. CATEGORY MODE
        # =========================
        category = core.detect_category(user_input)
        if category:
            matched = [i for i in items if i.get("category") == category]
            if matched:
                response = f"📦 **All {category.upper()} items**\n\n"
                for item in matched:
                    savings = item["market_price"] - item["my_price"]
                    response += f"**{item['name']}**\n"
                    response += f"- 💰 {item['my_price']} → {item['market_price']}\n"
                    response += f"- 🎯 {item['priority']}\n"
                    response += f"- 📊 Score: {round(core.score(item), 2)}\n"
                    response += f"- {'🟢 Savings' if savings >= 0 else '🔴 Overpay'}: ${round(abs(savings), 2)}\n\n"
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").markdown(response)
                st.stop()   # ✅ IMPORTANT (NOT return)
        # =========================
        # 2. ITEM INSPECTION MODE
        # =========================
        matched = next(
            (item for item in items if core.is_match(user_input, item["name"])),
            None
        )
        if matched:
            reasons = core.explain_score(matched)
            response = f"📦 **{matched['name']}**\n\n"
            response += f"- 💰 Your price: ${matched['my_price']}\n"
            response += f"- 🏪 Market price: ${matched['market_price']}\n"
            response += f"- 🎯 Priority: {matched['priority']}\n\n"
            response += "**Why this matters**\n"
            for r in reasons:
                response += f"- {r}\n"
        # =========================
        # 3. SMART ADD MODE (FIXED)
        # =========================
        else:
            parsed = core.parse_natural_add(user_input)
            my_price = parsed.get("my_price")
            market_price = parsed.get("market_price")
            # -------------------------
            # SMART VALIDATION
            # -------------------------
            valid_prices = (
                isinstance(my_price, (int, float))
                and isinstance(market_price, (int, float))
                and my_price > 0
                and market_price > 0
                and abs(my_price - market_price) > 1  # prevents duplicates like 233/233
            )
            if valid_prices:
                result = core.add_item(**parsed)
                if isinstance(result, dict) and "error" in result:
                    response = f"⚠️ {result['error']}"
                else:
                    response = (
                        f"✅ Added **{result['name']}**\n\n"
                        f"- 💰 You: ${result['my_price']}\n"
                        f"- 🏪 Market: ${result['market_price']}\n"
                    )
            else:
                # 🔥 fallback (BUT now less aggressive)
                response = (
                    "I couldn't fully confirm both prices.\n\n"
                    "Try:\n"
                    "👉 ryzen 7 7700x cpu for 233 usually 399\n"
                    "👉 gpu 650 vs 799 high\n"
                )

    # =========================
    # OUTPUT (ONLY ONCE — FIXED)
    # =========================
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").markdown(response)
