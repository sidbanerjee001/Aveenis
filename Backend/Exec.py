# Executed file every <interval> hrs
from DataProcessing import calculate_function
from stocktwits_helper import perform_stocktwits_scrape
from RedditAPI import run_reddit_scrape
from modules.database import Data, Database

def run():
    map1 = run_reddit_scrape()
    map2 = perform_stocktwits_scrape()

    flattened = [(ticker, calculate_function(values)) for ticker, values in map1.items()]
    flattened.extend([(ticker, values[1]) for ticker, values in map2.items()])
    combined = {}

    lengths = set([])

    for e in flattened:
        ticker = e[0]
        values = e[1]
        lengths.add(len(values))
        combined[ticker] = [
            sum(x)
            for x in zip(combined.get(ticker, [0 for _ in range(len(values))]), values)
        ]

    if len(lengths) > 1:
        print("Malformed data; lengths of sizes", lengths, "exist in scraped data.")
        return None

    # return dict(map(lambda e: (e[0], calculate_function(e[1])), combined.items()))

    db = Database()
    
    # calculate IV with call to wiv.py, requires yfinance and numpy

    # save the dictionary "combined" into the supabase (append metrics) + WIV

    for ticker, score in combined.items():
        data = db.get_data("final_db", ticker)
        if data:
            if len(data.get_value("data_today") == 24):
                data.pop_value("data_today", 0)
            data.append_value("data_today", score)
            # Add append_value for wiv data
            db.upsert_data(ticker, data)


    return 0
