# Single function that returns the weighted IV sum of a stock
# parameter stock is a string.

import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def calculate_iv_sum(stock):
    ticker = yf.Ticker(stock)
    expiration_dates = ticker.options

    today = datetime.today()
    target_date = today + timedelta(days=30)
    expiration_dates_dt = [datetime.strptime(date, '%Y-%m-%d') for date in expiration_dates]

    # Expiration date closest to 30 days from now
    closest_expiration_date = min(expiration_dates_dt, key=lambda x: abs(x - target_date))
    closest_expiration_str = closest_expiration_date.strftime('%Y-%m-%d')
    options_chain = ticker.option_chain(closest_expiration_str)
    current_price = ticker.history(period='1d')['Close'].iloc[0]

    options_chain.calls['strike_diff'] = abs(options_chain.calls['strike'] - current_price)
    options_chain.puts['strike_diff'] = abs(options_chain.puts['strike'] - current_price)

    # Sorted by 'strike_diff'
    sorted_calls = options_chain.calls.sort_values('strike_diff')
    sorted_puts = options_chain.puts.sort_values('strike_diff')

    top_strikes = sorted_calls['strike'].unique()

    sum_weighted_avg_iv = 0
    count = 0  # strikes processed?
    total_oi = 0

    print(type(top_strikes[0]))

    for strike in top_strikes:
        call_option = options_chain.calls[options_chain.calls['strike'] == strike]
        put_option = options_chain.puts[options_chain.puts['strike'] == strike]

        if call_option.empty or put_option.empty:
            continue

        call_option = call_option.iloc[0]
        put_option = put_option.iloc[0]

        call_iv = call_option['impliedVolatility']
        put_iv = put_option['impliedVolatility']

        # NaN IVs not included
        if np.isnan(call_iv) or np.isnan(put_iv):
            continue

        call_iv = abs(call_iv)
        put_iv = abs(put_iv)

        call_oi = call_option['openInterest']
        put_oi = put_option['openInterest']

        total_oi += call_oi + put_oi

        if total_oi > 0:
            weighted_avg_iv = (call_iv * call_oi + put_iv * put_oi)
        else:
            weighted_avg_iv = (call_iv + put_iv)

        sum_weighted_avg_iv += weighted_avg_iv
        count += 1

        if count >= 5:
            break

    return sum_weighted_avg_iv / total_oi
