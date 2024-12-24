import nltk
from nltk.corpus import words
import os
nltk.download('words')

def get_tickers_and_path():
    """Get the list of tickers from the tickers.txt file"""
    current_dir = os.path.dirname(__file__)
    ticker_filepath = os.path.join(current_dir, 'tickers.txt')
    with open(ticker_filepath, 'r') as file:
        tickers = file.read().splitlines()
    return tickers, ticker_filepath


def clean_tickers():
    """This function changes depending on what needs to happen to the ticker list. Ex: Removing whitespaces or adding whitespaces to single letter tickers"""
    tickers, ticker_filepath = get_tickers_and_path()
    tickers = [ticker.strip() for ticker in tickers]

    with open(ticker_filepath, 'w') as file:
        file.write('\n'.join(tickers))


def get_tickers_that_are_words():
    """Gets the tickers that are also words in English"""
    english_words = set(words.words())

    current_dir = os.path.dirname(__file__)
    ticker_filepath = os.path.join(current_dir, 'tickers.txt')
    with open(ticker_filepath, 'r') as file:
        tickers = file.read().splitlines()
    
    tickers_that_are_words = [ticker for ticker in tickers if ticker.lower() in english_words]

    return tickers_that_are_words


def main():
    print(get_tickers_that_are_words())


if __name__ == '__main__':
    main()




