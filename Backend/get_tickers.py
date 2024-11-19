with open ('stocks.txt', 'r') as file:
    lines = file.readlines()
tickers = [line.split('\t')[1] for line in lines]

with open ('tickers.txt', 'w') as write_file:
    write_file.write('\n'.join(tickers))
    