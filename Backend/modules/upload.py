import pickle
from supabase import create_client, Client
import os
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

def batch_upload_stocktwits_to_supabase(pkl_files, table_name="stocktwits_data"):
    """
    Aggregates mentions and likes from multiple daily .pkl files and batch upserts to Supabase.
    Each .pkl file should be a dict: {ticker: [mentions, likes]}
    """
    # Step 1: Aggregate data
    ticker_data = {}
    for pkl_file in pkl_files:
        with open(pkl_file, "rb") as f:
            day_data = pickle.load(f)
        for ticker, values in day_data.items():
            if ticker is None:
                continue
            mentions, likes = int(values[0]), int(values[1])
            if ticker not in ticker_data:
                ticker_data[ticker] = {"mentions": [], "likes": []}
            ticker_data[ticker]["mentions"].append(mentions)
            ticker_data[ticker]["likes"].append(likes)

    # Step 2: Prepare batch data
    batch = []
    for ticker, data in ticker_data.items():
        batch.append({
            "ticker": ticker,
            "mentions": data["mentions"],
            "likes": data["likes"]
        })

    # Step 3: Batch upsert
    # If your Database class has a batch upsert method, use it:
    # db.batch_upsert_data(table_name, batch)
    # Otherwise, use the official supabase client directly:
    supabase: Client = create_client(url, key)
    # Upsert all rows at once
    supabase.table(table_name).upsert(batch).execute()
    print("Batch upload complete.")


if __name__ == "__main__":
    # Example usage:
    pkl_files = [
        "tickers.txt_results5-12.pkl",
        "tickers.txt_results5-13.pkl",
        "tickers.txt_results5-15.pkl",
        "tickers.txt_results.pkl",
        "results5-21.pkl",
        "5-22.pkl",
        "5-23.pkl",
        "5-24.pkl",
        "5-25.pkl",
        # ...add all your file names here in chronological order
    ]
    batch_upload_stocktwits_to_supabase(pkl_files)