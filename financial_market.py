import datetime
import pandas as pd
import numpy as np
import yfinance as yf

import mplfinance as mpf

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
plt.rcParams["figure.figsize"] = (15, 15)

def load_dataframe():
    """
    This loads the dataframe and returns a dictionary with the key = symbol and value = sector the stock belongs to.
    Rules:
        1. Renamed for better indexing (removed spaces, lower case).
        2. Changed extra dates in brackets for AT&T to a single date.
        3. Take all the stocks present before the 2000s
        4. Take all the stocks which have a NaN in the date_first_added (because we don't know about the date when first added, so we'll collect the data on them and decide whether or not to include them later.)
        5. Sort values by gics_sector so we get it sector wise.
    """
    df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    
    # renaming columns
    df.columns = df.columns.str.replace(" ", "_")
    df.columns = [x.lower() for x in df.columns]
    
    # handling date exceptions
    df['date_first_added'][df.loc[df['symbol'] == "T"].index[0]] = "1983-11-30"
    
    # sorting by date
    df = df.sort_values(by=["date_first_added"])
    
    # taking those stocks where date is NaN
    df_nan = df[df['date_first_added'].isnull()]
    
    # taking those stocks where stock is present in the market before 2000s
    df_2000 = df[df['date_first_added'] < "2000-00-00"]
    
    # concatenating both NaN df and 2000s df
    df_concat = pd.concat([df_2000, df_nan], axis=0)
    
    # handling sectors
    df_concat.sort_values(by=['gics_sector'], inplace=True)  
    df_sector_dict = dict(zip(df_concat.symbol, df_concat.gics_sector))
    rename_sectors = {"Communication Services": "TC", "Consumer Discretionary": "CD", 
                      "Consumer Staples": "CS", "Energy": "EG", "Financials": "FN", "Health Care": "HC",
                      "Industrials": "ID", "Information Technology": "IT", "Materials": "MT",
                      "Real Estate": "RE", "Utilities": "UT"
                     }

    df_sector_dict_short = {}
    for key, value in df_sector_dict.items():
        df_sector_dict_short[key] = rename_sectors[value]
    df_sector_dict_short_sorted = dict(sorted(df_sector_dict_short.items(), key=lambda kv: kv[1]))
    
    symbols = [key for key in df_sector_dict_short_sorted]
    return df_concat, df_sector_dict_short_sorted, symbols

def get_closing_prices(symbols, df_sector_dict):
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
    df_sector = pd.DataFrame()
    df_both = pd.DataFrame()
    
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
                    df_sector = pd.concat([df_sector, df_to_add], axis=1)
                    df_both = pd.concat([df_both, df_to_add], axis=1)
                    i += 1
                
                df_to_add = pd.DataFrame(hist["Close"].values.tolist(), columns=[symbol])
                df = pd.concat([df, df_to_add], axis=1)
                
                df_to_add_2 = pd.DataFrame(hist["Close"].tolist(), columns=[df_sector_dict[symbol]])
                df_sector = pd.concat([df_sector, df_to_add_2], axis=1)
                
                df_to_add_3 = pd.DataFrame(hist["Close"].tolist(), columns=[symbol + "_" + df_sector_dict[symbol]])
                df_both = pd.concat([df_both, df_to_add_3], axis=1)
        except:
            print(symbol, "delisted")
            not_done_for.append(symbol)
    return df, df_sector, df_both, not_done_for

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