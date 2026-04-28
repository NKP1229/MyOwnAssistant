import streamlit as st
import assistant_core as core

st.title("🧠 Purchase Assistant")

# -------------------------
# ADD ITEM
# -------------------------
st.header("Add Item")
name = st.text_input("Item name")
my_price = st.number_input("Your price", min_value=0.0)
market_price = st.number_input("Market price", min_value=0.0)
priority = st.selectbox("Priority", ["low", "medium", "high"])
if st.button("Add Item"):
    if not name.strip():
        st.warning("Please enter an item name.")
    elif my_price <= 0 or market_price <= 0:
        st.warning("Prices must be greater than 0.")
    else:
        item = core.add_item(name, my_price, market_price, priority)
        st.success(f"Added {item['name']}")

# -------------------------
# LIST ITEMS
# -------------------------
st.header("Your Items")
items = core.load_items()
for i, item in enumerate(items):
    col1, col2 = st.columns([4, 1])
    status = "✅" if item["purchased"] else "❌"
    col1.write(f"{status} {item['name']}")
    if not item["purchased"]:
        if col2.button("Mark Bought", key=f"buy_{i}"):
            item["purchased"] = True
            core.save_items(items)
            st.rerun()

# -------------------------
# RECOMMENDATION
# -------------------------
st.header("Recommendation")
if st.button("What should I buy?"):
    best = core.recommend()
    if best:
        savings = best["market_price"] - best["my_price"]
        discount_pct = (savings / best["market_price"]) * 100 if best["market_price"] else 0
        st.success(f"You should buy: {best['name']}")
        st.write("**Reasoning:**")
        st.write(f"- Priority: {best['priority']}")
        if savings >= 0:
            st.write(f"- Discount: {round(discount_pct, 1)}% (${round(savings, 2)} off)")
        else:
            st.write(f"- Over market by: ${round(abs(savings), 2)}")
        st.write(f"- Score: {round(core.score(best), 2)}")
    else:
        st.warning("No good deals right now. You might want to wait.")