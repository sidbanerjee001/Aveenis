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
        scores = [0] * 30
        scores[0] = datas['daily_score']
        
        # Prepare the data to insert, including the ticker
        data_with_ticker = {
            "ticker": ticker,
            "mentions_hourly": json.dumps(datas["hours"]),
            "likes_hourly": json.dumps(datas["likes"]),
            "mentions_daily": json.dumps(mentions_total_full),
            "likes_daily": json.dumps(likes_total_full),
            "stock_price": json.dumps(datas["stock_price"]),
            "market_cap": json.dumps(datas["market_cap"]),
            "wiv": json.dumps(iv_total_full),
            "daily_score": json.dumps(datas['daily_score']),
            "daily_scores": json.dumps(scores),
            "daily_scores_acceleration": json.dumps([0] * 30)
        }
        supabase_client.table(database_name).insert(data_with_ticker).execute()
        print(f"Inserted new data for {ticker}")
        
    else:
        # # Update mentions_total and likes_total (pop last, push new)
        old_mentions_total = json.loads(response.data[0].get("mentions_daily"))
        old_likes_total = json.loads(response.data[0].get("likes_daily"))
        old_wiv = json.loads(response.data[0].get("wiv"))
        old_daily_scores = json.loads(response.data[0].get("daily_score"))
        old_daily_scores_accel = json.loads(response.data[0].get("daily_scores_acceleration"))
        
        old_mentions_total.pop()
        old_mentions_total.insert(0, datas["total_mentions"])
        
        old_likes_total.pop()
        old_likes_total.insert(0, datas["total_likes"])

        old_wiv.pop()
        old_wiv.insert(0, datas["wiv"])
        
        old_daily_scores.pop()
        old_daily_scores.insert(0, datas['daily_score'])
        
        # Calculate score acceleration
        old_daily_scores_accel = calculate_accels(old_daily_scores)
        
        # Update the existing record with new data
        supabase_client.table(database_name).update({
            "mentions_hourly": json.dumps(datas["hours"]),
            "likes_hourly": json.dumps(datas["likes"]),
            "mentions_daily": json.dumps(old_mentions_total),
            "likes_daily": json.dumps(old_likes_total),
            "stock_price": json.dumps(datas["stock_price"]),
            "market_cap": json.dumps(datas["market_cap"]),
            "wiv": json.dumps(old_wiv),
            "daily_score": json.dumps(datas['daily_score']),
            "daily_scores": json.dumps(old_daily_scores),
            "daily_scores_acceleration": json.dumps(old_daily_scores_accel)
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

def estimation_for_empty_hours(ticker_data):
    ## should probably have done with numpy
    
    map_stocktwits = load_joblib("supervised_results.joblib")
    
    stocktwits_total_hourly_traffic = [0] * 24
    stocktwits_total_hourly_likes = [0] * 24
    for ticker, data in map_stocktwits.items():
        hours = data["hours"]
        stocktwits_total_hourly_traffic = [x + y for x, y in zip(stocktwits_total_hourly_traffic, hours)]
        likes = data["likes"]
        stocktwits_total_hourly_likes = [x + y for x, y in zip(stocktwits_total_hourly_likes, likes)]


    for ticker, data in map_stocktwits.items():
        if data["reached_target_date"]:
            continue
        else:
            latest_hour = data["latest_post_date"].datetime_object.hour
            earliest_hour = data["earliest_post_date"].datetime_object.hour
            # Find all hour indices outside the [earliest_hour, latest_hour] range
            hours = data["hours"]
            likes = data["likes"]
            outside_indices = [i for i in range(len(hours)) if i < earliest_hour or i > latest_hour]

            # Get value of stocktwits_total_hourly_traffic for those indices
            avg_traffic_total = sum([stocktwits_total_hourly_traffic[i] for i in range(len(hours)) if i >= earliest_hour and i <= latest_hour])/ (latest_hour - earliest_hour + 1)
            avg_traffic_stock = sum([hours[i] for i in range(len(hours)) if i >= earliest_hour and i <= latest_hour]) / (latest_hour - earliest_hour + 1)
            
            # Estimate likes
            avg_likes_total = sum([stocktwits_total_hourly_likes[i] for i in range(len(likes)) if i >= earliest_hour and i <= latest_hour]) / (latest_hour - earliest_hour + 1)
            avg_likes_stock = sum([likes[i] for i in range(len(likes)) if i >= earliest_hour and i <= latest_hour]) / (latest_hour - earliest_hour + 1)
            
            for i in outside_indices:
                if hours[i] == 0:
                    # Estimate the value based on the average traffic
                    hours[i] = int(stocktwits_total_hourly_traffic[i] * (avg_traffic_stock / avg_traffic_total))
            
                if likes[i] == 0:
                    # Estimate the value based on the average traffic
                    likes[i] = int(stocktwits_total_hourly_likes[i] * (avg_likes_stock / avg_likes_total))

        map_stocktwits[ticker]["hours"] = hours
        map_stocktwits[ticker]["likes"] = likes
    # Save the updated map_stocktwits back to the file
    with open("supervised_results.joblib", 'wb') as f:
        joblib.dump(map_stocktwits, f)


### For future, modify browser w/ extensions to get rid of loading ads/videos
### (also look into stocktwits feed settings once completed)
def run():
    # Perform scraping
    # Load results
    
    # Debug:
    # with open("ex_reddit.txt", 'r') as file:
    #     text = file.read()
    # map1 = eval(text)
    
    map1 = {} # run_reddit_scrape()
    # map1 = { key.replace('$', ''): value for key, value in map1.items() }
    
    run_stocktwits_scrape()
    map2 = load_joblib("supervised_results.joblib")

    print(map2)
    
    exit()
    # Combine results
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
        # Get combined total likes/mentions
        data['total_likes'] = combined[ticker_data][1]
        data['total_mentions'] = combined[ticker_data][0]

        # Get score
        data['daily_score'] = calculate_function([data['total_mentions'], data['total_likes']])
        
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

    # Uploading to Supabase
    supabase_client = supabase.create_client(url, key)

    # Will transition to batch upsert later
    for ticker, datas in map2.items():
        update_ticker(ticker, datas, supabase_client)
        print(f"Updated {ticker} in Supabase")
        
    return 0

if __name__ == "__main__":
    run()
