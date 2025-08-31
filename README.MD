# Avanza Stock Scraper 📈  

A Python bot that scrapes company data from [Avanza](https://www.avanza.se/) and ranks stocks by:  
- 📰 News hype (AI-labeled sentiment)  
- 💰 Profits over the last 3 months  
- 📊 Custom trading metrics, e.g. `(company_value * value_traded_today) / avanza_owners` to see hype potential

---

## 🚀 Features  
- Fetches company names and IDs from Avanza  
- Collects trading & financial data  
- Calculates custom metrics (e.g. **hype potential**)  
- Plots and visualizes the top candidates  

---

## 📂 Project Structure  
`Base_scripts/` contains the core functionality:  
- `get_avanza_company_names_and_orderID.py` → fetches company names & IDs  
- `fetch_avanza_data.py` → retrieves financial & trading data  
- `plot_top_hype_potential.py` → visualizes top hype potential stocks  

---

## 🧮 Example Metric: Hype Potential  
```python
value = quote.get('totalValueTraded', None)
market_cap_div_owners = market_cap / owners
hype_potential = market_cap_div_owners * value

