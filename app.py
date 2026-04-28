import streamlit as st
from assistant_core import *

st.title("🧠 Purchase Assistant")

# Add item
st.header("Add Item")

name = st.text_input("Item name")
my_price = st.number_input("Your price", min_value=0.0)
market_price = st.number_input("Market price", min_value=0.0)
priority = st.selectbox("Priority", ["low", "medium", "high"])

if st.button("Add Item"):
    items = load_items()
    items.append({
        "name": name,
        "my_price": my_price,
        "market_price": market_price,
        "priority": priority,
        "purchased": False
    })
    save_items(items)
    st.success("Item added!")

# List items
st.header("Your Items")

items = load_items()
for i, item in enumerate(items):
    status = "✅" if item["purchased"] else "❌"
    st.write(f"{status} {item['name']}")

# Recommend
st.header("Recommendation")

if st.button("What should I buy?"):
    items = load_items()
    valid_items = [
        i for i in items
        if not i["purchased"]
    ]
    if valid_items:
        best = max(valid_items, key=score)
        st.success(f"You should buy: {best['name']}")
    else:
        st.warning("No items to recommend.")