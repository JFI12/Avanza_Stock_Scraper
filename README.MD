Avanza_Stock_Scraper
Bot that scrapes Avanza Companies and rank them by news-hype, AI-labeled, profits last 3 months exc...

In Base_scripts

get_avanza_company_names_and_orderID.py

fetch_avanza_data.py

plot_top_hype_potential.py

value = quote.get('totalValueTraded', None)
market_cap_div_owners = (market_cap / owners) 

hype_potential = (market_cap_div_owners * value) 
