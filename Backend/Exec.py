# Executed file every <interval> hrs
from DataProcessing import calculate_function
from stocktwits_helper import perform_stocktwits_scrape

def run():
    map1 = {
        "t1": [1,2,3,4],
        "t2": [1,2,3,4],
        "t3": [1,2,3,4],
        "t4": [1,2,3,4],
        "t5": [1,2,3,4],
    } # replace with call to Reddit scrape
    # map2 = {
    #     "t1": [1,2,3,4],
    #     "t2": [1,1,1,1],
    #     "t3": [1,2,3],
    #     "t4": [1,2,3,4],
    #     "t6": [1,2,3,4],
    # } # replace with call to Stocktwits scrape
    map2 = perform_stocktwits_scrape()

    flattened = [(ticker, values) for ticker, values in map1.items()]
    flattened.extend([(ticker, values) for ticker, values in map2.items()])
    combined = {}

    lengths = set([])

    for e in flattened:
        ticker = e[0]
        values = e[1]
        lengths.add(len(values))
        combined[ticker] = [sum(x) for x in zip(combined.get(ticker, [0 for _ in range(len(values))]), values)]
    
    if len(lengths) > 1:
        print("Malformed data; lengths of sizes", lengths, "exist in scraped data.")
        return None

    return dict(map(lambda e: (e[0], calculate_function(e[1])), combined.items()))