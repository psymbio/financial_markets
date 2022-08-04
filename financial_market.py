import datetime
import pandas as pd
import yfinance as yf

import mplfinance as mpf

import matplotlib.pyplot as plt
import plotly.graph_objects as go

def load_dataframe():
    """
    This loads the dataframe.
    Rules:
        1. Renamed for better indexing (removed spaces, lower case).
        2. Changed extra dates in brackets for AT&T to a single date.
        3. Take all the stocks present before the 2000s
        4. Take all the stocks which have a NaN in the date_first_added (because we don't know about the date when first added, so we'll collect the data on them and decide whether or not to include them later.)
    """
    df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    df.columns = df.columns.str.replace(" ", "_")
    df.columns = [x.lower() for x in df.columns]
    df['date_first_added'][df.loc[df['symbol'] == "T"].index[0]] = "1983-11-30"
    df = df.sort_values(by=["date_first_added"])
    df_nan = df[df['date_first_added'].isnull()]
    df_2000 = df[df['date_first_added'] < "2000-00-00"]
    df_concat = pd.concat([df_2000, df_nan], axis=0)
    return df_concat

def get_closing_prices(symbols):
    """
    This loads the closing prices of all stocks present before the 2000s in a single dataframe.
    Returns
    -------
    df : pd.Dataframe
        Closing prices of stocks by date.
    not_done_for : List
        Symbols the data wasn't not collected for.
    """
    df = pd.DataFrame()
    not_done_for = []
    i = 0
    for symbol in symbols:
        # print(symbol)
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start="2000-01-01",  end="2022-01-01")
            hist.reset_index(drop=False, inplace=True)
            # print(hist.iloc[0]["Date"])
            if hist["Date"][0] != datetime.datetime(1999, 12, 31):
                print(symbol, "not in past")
            else:
                # print(symbol, "okay to go")
                if i == 0:
                    df_to_add = pd.DataFrame(hist["Date"].tolist(), columns=["date"])
                    df = pd.concat([df, df_to_add], axis=1)
                    i += 1
                df_to_add = pd.DataFrame(hist["Close"].values.tolist(), columns=[symbol])
                df = pd.concat([df, df_to_add], axis=1)
        except:
            print(symbol, "delisted")
            not_done_for.append(symbol)
    return df, not_done_for

def plot_candlesticks(symbol, plot_type = 1):
    """
    Downloads the data for a specific stock suymbol and plots the candlesticks for data in between 2000-01-01 and 2022-01-01.
    """
    data = yf.download(tickers=symbol, start="2000-01-01",  end="2022-01-01")
    if plot_type == 1:
        mpf.plot(data, type='candle', mav = (3, 6, 9), volume = True)
    else:
        fig = go.Figure(data=[go.Candlestick(x=data.index,
                                             open=data['Open'],
                                             high=data['High'],
                                             low=data['Low'],
                                             close=data['Close'])])

        fig.show()