----------------------------------------------------------------------------
This is my attempt at learning Python to make my own personal AI assistant
----------------------------------------------------------------------------
* Install Python extension 
* run in Terminal/Bash: 
  - "pip install streamlit"
  - "streamlit run app.py"
----------------------------------------------------------------------------
FILES:
  - data.json : stores json formatted data of purchases the user enters
  - main.py : python code to parse user input and perform correlating action
----------------------------------------------------------------------------
HOW TO USE:
 -> select main.py file in IDE, and run (without debugging)
 -> *AI program will power up and prompt user to start convo

 FEATURES:
   - Add        (Insert new entry into data.json)
   - List       (List all items to purchase)
   - Recommend  (Compare items for best purchase/deal)
   - Buy        (Mark item in data.json as bought/purchased)

 TEST:
   -> "I found a new amd gpu for 650 and it is usually 600 medium priority"
   -> "What should I buy?"
   -> "I bought the epomaker keyboard"
----------------------------------------------------------------------------
STRUCTURE OF DATA:
{
   "name": "epomaker aula f75 max",
   "my_price": 69.99,
   "market_price": 79.99,
   "priority": "medium",
   "purchased": true
},
----------------------------------------------------------------------------