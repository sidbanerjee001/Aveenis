# Executed file every <interval> hrs
from DataProcessing import calculate_function
from stocktwits_helper import perform_stocktwits_scrape
from RedditAPI import run_reddit_scrape
from modules.database import Data, Database
import pickle

def run():
    # Perform scraping
    map1 = run_reddit_scrape()
    perform_stocktwits_scrape()
    
    # Load stocktwits scrape from pickl object
    map2 = {}
    with open("test.txt_results.pkl", 'rb') as f:
        map2 = pickle.load(f)
    flattened = [(ticker, calculate_function(values)) for ticker, values in map1.items()]
    flattened.extend([(ticker, values[0]) for ticker, values in map2.items()])
    combined = {}
    lengths = set([])

    for e in flattened:
        ticker = e[0]
        values = e[1]
        combined[ticker] = [
            sum(x)
            for x in zip(combined.get(ticker, [0]), [values])
        ]

    print(combined)
    # return dict(map(lambda e: (e[0], calculate_function(e[1])), combined.items()))

    db = Database()
    
    # calculate IV with call to wiv.py, requires yfinance and numpy

    # save the dictionary "combined" into the supabase (append metrics) + WIV

    for ticker, score in combined.items():
        data = db.get_data("final_db", ticker)
        if data:
            if len(data.get_value("data_today")) == 24:
                data.pop_value("data_today", 0)
            data.append_value("data_today", score)
            # Add append_value for wiv data
            db.upsert_data(ticker, data)


    return 0

if __name__ == "__main__":
    run()