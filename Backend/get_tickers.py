with open('/Users/hanj/Desktop/Aveenis/Backend/stocks.txt', 'r') as file:
    lines = file.readlines()

tickers = [line.split('\t')[1] for line in lines if len(line.split('\t')) > 1]

with open('/Users/hanj/Desktop/Aveenis/Backend/tickers.txt', 'w') as write_file:
    write_file.write('\n'.join(tickers))