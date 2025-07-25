# Executed file every <interval> hrs
from DataProcessing import calculate_function
from RedditAPI import run_reddit_scrape
from modules.database import Data, Database
import joblib
import supabase
import os
import wiv
from DataProcessing import calculate_accels
import json
from stocktwits.process_supervisor import run_supervised_scraping, MonitoringConfig, ScrapingConfig

# Should make this cleaner
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

def load_joblib(path):
    try:
        with open(path, 'rb') as f:
            file = joblib.load(f)
    except FileNotFoundError:
        return {}

    return {k.lower(): v for k, v in file.items()}

def update_ticker(ticker, datas, supabase_client, database_name="full_data_with_accel"):
    if not isinstance(datas, dict):
        print(f"Skipping {ticker} as it is not a dictionary.")
        return

    # Check if the ticker already exists in the table
    response = supabase_client.table(database_name) \
        .select("*") \
        .filter("ticker", "eq", ticker) \
        .execute()

    if not response.data:  # If no data is returned, insert new data
        mentions_total_full = [0] * 30
        mentions_total_full[0] = datas["total_mentions"]
        likes_total_full = [0] * 30
        likes_total_full[0] = datas["total_likes"]
        iv_total_full = [0] * 30
        iv_total_full[0] = datas["wiv"]

        # Prepare the data to insert, including the ticker
        data_with_ticker = {
            "ticker": ticker,
            "mentions_hourly": json.dumps(datas["hours"]),
            "likes_hourly": json.dumps(datas["likes"]),
            "mentions_daily": json.dumps(mentions_total_full),
            "likes_daily": json.dumps(likes_total_full),
            "mentions_hourly_acceleration": json.dumps(datas["hourly_mentions_acceleration"]),
            "likes_hourly_acceleration": json.dumps(datas["hourly_likes_acceleration"]),
            "stock_price": json.dumps(datas["stock_price"]),
            "market_cap": json.dumps(datas["market_cap"]),
            "hourly_stock_price_acceleration": json.dumps(datas["hourly_stock_price_acceleration"]),
            "hourly_market_cap_acceleration": json.dumps(datas["hourly_market_cap_acceleration"]),
            "wiv": json.dumps(iv_total_full),
        }
        supabase_client.table(database_name).insert(data_with_ticker).execute()
        print(f"Inserted new data for {ticker}")
        
    else:
        # # Update mentions_total and likes_total (pop last, push new)
        old_mentions_total = json.loads(response.data[0].get("mentions_daily"))
        old_likes_total = json.loads(response.data[0].get("likes_daily"))
        old_wiv = json.loads(response.data[0].get("wiv"))
        
        old_mentions_total.pop()
        old_mentions_total.insert(0, datas["total_mentions"])
        
        old_likes_total.pop()
        old_likes_total.insert(0, datas["total_likes"])

        old_wiv.pop()
        old_wiv.insert(0, datas["wiv"])
        
        # Update the existing record with new data
        supabase_client.table(database_name).update({
            "mentions_hourly": json.dumps(datas["hours"]),
            "likes_hourly": json.dumps(datas["likes"]),
            "mentions_daily": json.dumps(old_mentions_total),
            "likes_daily": json.dumps(old_likes_total),
            "mentions_hourly_acceleration": json.dumps(datas["hourly_mentions_acceleration"]),
            "likes_hourly_acceleration": json.dumps(datas["hourly_likes_acceleration"]),
            "stock_price": json.dumps(datas["stock_price"]),
            "market_cap": json.dumps(datas["market_cap"]),
            "hourly_stock_price_acceleration": json.dumps(datas["hourly_stock_price_acceleration"]),
            "hourly_market_cap_acceleration": json.dumps(datas["hourly_market_cap_acceleration"]),
            "wiv": json.dumps(old_wiv),
        }).eq("ticker", ticker).execute()

def run_stocktwits_scrape():
    
    # Configuration
    monitoring_config = MonitoringConfig(
        max_file_age=120,
        min_runtime=60,
        max_restarts=5
    )
    
    scraping_config = ScrapingConfig(
        hours_back=24,
        max_retries=2
    )
    
    with open('tickers.txt', 'r') as f:
        tickers = [line.strip().lower() for line in f if line.strip()]
        
    # Run supervised scraping
    run_supervised_scraping(
        username=os.getenv("STOCK_USER"),
        password=os.getenv("STOCK_PASS"),
        tickers= ["NKE", "AMD", "AACG", "AAPL", "TSLA"],
        output_file="supervised_results.joblib",
        monitoring_config=monitoring_config,
        scraping_config=scraping_config
    )
    
    return 0

def run():
    # Perform scraping
    # Load results
    map1 = run_reddit_scrape()
    map1 = { key.replace('$', ''): value for key, value in map1.items() }
    
    # run_stocktwits_scrape()
    map2 = load_joblib("supervised_results.joblib")

    # Debug: check data types
    # for ticker, values in map1.items():
    #     print(f"map1 - {ticker}: {type(values)} = {values}")
    # for ticker, values in map2.items():
    #     print(f"map2 - {ticker}: {type(values)} = {values}")

    flattened = [(ticker, (int(values[0]), int(values[1]))) for ticker, values in map1.items()]
    flattened.extend([(ticker, (int(values['total_likes']), int(values["total_mentions"]))) for ticker, values in map2.items() if isinstance(values, dict)])
    combined = {}
    
    for e in flattened:
        ticker = e[0].casefold()
        values = e[1]
        combined[ticker] = tuple(
            a + b for a, b in zip(combined.get(ticker, (0, 0)), values)
        )
    
    # only adds to supabase if ticker also in map2 (map2 will contain all NYSE tickers)
    for ticker_data, data in map2.items():
        data['total_likes'] = combined[ticker_data][1]
        data['total_mentions'] = combined[ticker_data][0]

        # Add IV_sum, daily value
        try:
            data['wiv'] = int(wiv.calculate_iv_sum(ticker_data))
        except Exception as e:
            print(f"Error calculating WIV for {ticker_data}: {e}")
            data['wiv'] = 0

        # Adding hourly stock price data from market open to close
        data['stock_price'] = wiv.get_stockprice_last_day(ticker_data)
        
        # Adding market cap, hourly
        data['market_cap'] = wiv.get_marketcap_last_day(ticker_data)

        # Adding accelerations for likes, mentions, stock_price
        # check calculate_accels; not sure if im seeing the vision
        mentions_accel = calculate_accels(data['hours'])
        likes_accel = calculate_accels(data['likes'])
        stock_price_accel = calculate_accels(data['stock_price'])
        market_cap_accel = calculate_accels(data['market_cap'])

        data['hourly_mentions_acceleration'] = mentions_accel
        data['hourly_likes_acceleration'] = likes_accel
        data['hourly_stock_price_acceleration'] = stock_price_accel
        data['hourly_market_cap_acceleration'] = market_cap_accel

    # Uploading to Supabase
    supabase_client = supabase.create_client(url, key)

    # Will transition to batch upsert later
    for ticker, datas in map2.items():
        update_ticker(ticker, datas, supabase_client)
        print(f"Updated {ticker} in Supabase")
        
    # return dict(map(lambda e: (e[0], calculate_function(e[1])), combined.items()))

    # db = Database()
    
    # calculate IV with call to wiv.py, requires yfinance and numpy

    # save the dictionary "combined" into the supabase (append metrics) + WIV

    
    # for ticker, score in combined.items():
    #     data = db.get_data("full_data", ticker)
    #     if data:
    #         if len(data.get_value("data_today")) == 24:
    #             data.pop_value("data_today", 0)
    #         data.append_value("data_today", score)
    #         # Add append_value for wiv data
    #         db.upsert_data(ticker, data)
    #     else: 
    #         data = Data(_type="ticker", _stock_ticker=ticker)
    #         data.set_value("data_today", [score])
    #         db.upsert_data(ticker, data)

    # return 0

if __name__ == "__main__":
    run()
