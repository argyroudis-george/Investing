import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta


# initialization for saved time series files
def data_initialization(file):
    df = pd.read_csv(file,names= ['dates','prices'], index_col=['dates'], parse_dates=['dates'])
    df['prices'] = df['prices'].asfreq(pd.infer_freq(df.index))
    # plt.plot(df.prices, color ='r', linestyle ='-', linewidth = 1)
    # plt.show(block = False)
    # plt.pause(1)    # or time.sleep
    # plt.close()
    return df

# initialization for Tickers
def data_initialization2(data):
    df = pd.DataFrame(index=data.index)
    df['prices'] = data['Close']
    df['prices'] = df['prices'].asfreq((pd.infer_freq(df.index)))
    # plt.figure(figsize=(7,7))
    # plt.plot(df.prices, color ='r', linestyle ='-', linewidth = 1)
    # plt.show(block = False)
    # plt.pause(1)    # or time.sleep
    # plt.close()
    return df



while True:
    try:
        answer = input('Do you want to use a ticker from yahoo, or do you have some time series in your computer? '
                       'Press T for Ticker or D for Data.')
    except Exception as e:
        print('Please try again. Choose between T and D.', e)
        continue
    else:
        if answer in  {'T', 't'}:
            while True:
                try:
                    x = yf.Ticker(input('Please enter the name of the Ticker you want: '))
                except Exception as e:
                    print('Please enter a correct Ticker name.')
                    continue
                else:
                    data = x.history(interval='1d',start=(input('Please enter the starting date of the dataset: ')),
                                     end=(input('Please enter the ending date of the dataset: ')))
                    df = data_initialization2(data)
                    break
        elif answer in {'D', 'd'}:
            while True:
                try:
                    x = input('Please enter the file name, including the csv acronym: ')
                    with open(x) as file:
                        df = data_initialization(file.name)
                except IOError as e:
                    print('Please enter a correct name that exists', e)
                    continue
                else:
                    print('The time series were successfully imported')
                    break
        break
print(df.head())
# ----------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------

### create a dataframe that shows when its time to buy and when its a potential selling day

# The function need as input:
# 1. The prices from the previous step
# 2. The number of days with continuous upward price trend to trigger the portfolio investment
# 3. The number of days with continuous downward trend to trigger the share withdrawal
def buying_dates_and_potential_selling_dates(prices, b, s):
    percent_prices = prices.pct_change()[1:]

    def continuous_increase(internal):
        return (internal > 0).all()

    def continuous_decrease(internal):
        return (internal < 0).all()

    buying_dates = percent_prices.rolling(b).apply(continuous_increase)
    selling_dates = percent_prices.rolling(s).apply(continuous_decrease)

    # The function returns a dictionary with ALL the buying dates and ALL the potential selling dates
    return {'buying dates': buying_dates, 'selling dates': selling_dates}

# The function "buying_dates_and_potential_selling_dates" shows all the time series dates.
# We only need the dates where
# either buying date is True or selling date is True.
# Therefore we create a new dataframe bs (buy - sell)
results = buying_dates_and_potential_selling_dates(df.prices, 10, 5)
buying_dates = results['buying dates']
selling_dates = results['selling dates']
bs = pd.DataFrame(index = buying_dates.index)
bs['buying_dates'] = (buying_dates == 1)
bs['selling_dates'] = (selling_dates == 1)
bs['prices'] = df.prices
bs = bs[ bs['buying_dates'] | bs['selling_dates'] ]
print(bs.head(5))




# ----------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------

### Main part of the function, we import the initial information in the function, like current shares and
# current account


def is_the_date_to_buy_question(prices, buying_date, potential_selling_date):
    pct_change_data = prices.pct_change()[1:]
    worth_selling = 1 + pct_change_data[buying_date + timedelta(hours=1):potential_selling_date]
    return worth_selling.product() > 1

def investing(starting_capital):

    # prices
    prices = bs.prices

    # initialize capital
    current_capital = starting_capital

    current_shares = 0

    invest_before = False

    last_buy_date = None

    events = []

    #if there is potential date for buying stocks, BUY
    # we check EVERY row of the dataframe bs above
    for date, data in bs.iterrows():
        if (not invest_before) and data['buying_dates']:
            number_of_shares = int(current_capital / data['prices'] )
            current_shares += number_of_shares
            current_capital -= number_of_shares*data.prices
            last_buy_date = date
            events.append(('b', date))
            invest_before = True
            print('We bought {} shares at {} per share on {} totalling {} dollars'.
                  format(round(current_shares), round(data['prices']), date, round(current_capital)))
        elif invest_before and data['selling_dates']:
            if is_the_date_to_buy_question(prices,last_buy_date, date):
                current_capital += current_shares*data['prices']
                print('We sold {} shares at {} dollars per share on {}, and we made {}'.
                      format(round(current_shares), round(data['prices']), date, round(current_capital)))
                print('----------------------------------------------------------------')
                print('----------------------------------------------------------------')

                current_shares = 0
                invest_before = False
                events.append(('s', date))

    final_price_of_time_series = prices[-1]

    final_portfolio = current_capital + current_shares * final_price_of_time_series

    verdict = (final_portfolio - starting_capital) / starting_capital
    return verdict, events

# -------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------

R, events = investing(1000000)
print(R)

# plot the figure with the buy-sell vertical lines, and some color in between
plt.plot(bs.prices)
for i, time in enumerate(events):

    if time[0] == 'b':
        plt.axvline(time[1], color = 'g')
    else:
        plt.axvline(time[1], color = 'r')
    if time[0] == 's':
        plt.fill_betweenx(bs.prices,time[1], events[i-1][1],color ='k', alpha = 0.2)
plt.show()



