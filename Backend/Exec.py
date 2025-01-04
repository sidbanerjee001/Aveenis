# Executed file every <interval> hrs
from DataProcessing import calculate_function
from stocktwits_helper import perform_stocktwits_scrape
from RedditAPI import run_reddit_scrape


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

    # save the dictionary "combined" into the supabase (append metrics)

    # pull data to calculate relative metrics (accel, change, etc.)

    # save relative metrics

    return combined
