import datetime
import pandas as pd
import numpy as np
import yfinance as yf

import mplfinance as mpf

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates

import plotly.graph_objects as go
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")
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
    
    Parameters
    ----------
    None
    
    Returns
    -------
    df_concat : pd.DataFreme
        concatenated dataframe of the stocks to search for
        this is a concatenation of all stocks present before the 2000s and those which didn't have a date present in them.
    df_sector_dict_short_sorted : dict
        dict of sectors stocks belong to
    symbols : list
        list of symbols to search for
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
    
    Parameters
    ----------
    symbols : list
        List of ticker values
    df_sector_dict : dict
        Dictionary of sectors the different stocks belong to.
        
    Returns
    -------
    df : pd.DataFrame
        Closing prices of stocks by date.
    not_done_for : list
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
            hist = ticker.history(start="2000-01-01",  end="2022-06-01")
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
    
    Parameters
    ----------
    symbol : str
        Ticker value (example: 'AAPL')
    plot_type : int
        if 1 then uses mpf
        else uses plotly
    
    Returns
    -------
    None
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

def ticker_val_locations(df, start = 1):
    """
    Get locations for ticker values
    
    Parameters
    ----------
    df : pd.DataFrame
    start : int
        if start == 1: then ticker values are plotted at the start
        else ticker values are plotted in the center.
    Returns
    -------
        dict_col : dict
            dictionary that stores locations to plot the ticker values.
    """
    col_names = []
    for element in list(df.columns):
        col_names.append(element[:2])
    dict_col = {}
    i = 0
    if start == 1:
        for col in col_names:
            i += 1
            if col not in dict_col:
                dict_col[col] = i
    else:
        for col in col_names:
            i += 1
            if col not in dict_col:
                dict_col[col] = [i, i]
            else:
                dict_col[col][1] += 1

        for key, value in dict_col.items():
            dict_col[key] = (dict_col[key][0] + dict_col[key][1]) // 2
    
    return dict_col
        
def plot_corr_mat(df):
    """
    Takes dataframe to plot correlation matrix
    
    Parameters
    ----------
    df : pd.DataFrame
        dataframe to plot the correlation matrix for
        
    Returns
    -------
    None
    """
    dict_col = ticker_val_locations(df)
    sns.heatmap(df.corr("pearson"))
    plt.xticks(ticks=list(dict_col.values()), labels=list(dict_col.keys()))
    plt.yticks(ticks=list(dict_col.values()), labels=list(dict_col.keys()))
    plt.show()
    
def plot_all_charts(df):
    """
    Takes dataframe to plot all the charts in nx3 format.
    
    Parameters
    ----------
    df : pd.DataFrame
    
    Returns
    -------
    None
    """
    fig, axes = plt.subplots(len(df.columns[1:])//3 + 1, 3, figsize=(20,len(df.columns[1:])//3 * 5))
    df.head()
    count = 0
    for i in df.columns[1:]:
        sns.lineplot(df["date"], df[i], ax=axes[count//3, count%3])
        count += 1
        
def plot_all_charts_2(df):
    """
    Takes dataframe to plot all the charts in 3x3 format.
    
    Parameters
    ----------
    df : pd.DataFrame
    
    Returns
    -------
    None
    """
    ticker_count = 1
    col_list = df.columns[1:]
    # for a in range(0, len(df.columns[1:])//9 + 1):
    for a in range(0, 30):
        fig = plt.figure(figsize=(13, 10))
        outer = gridspec.GridSpec(3, 3, wspace=0.24, hspace=0)
        try:
            for i in range(9):
                inner = gridspec.GridSpecFromSubplotSpec(1, 1,
                                subplot_spec=outer[i], wspace=0, hspace=0)
                for j in range(1):
                    ax = plt.Subplot(fig, inner[j])
                    ax.plot(df.iloc[:, 0], df.iloc[:, ticker_count])
                    ticker_count += 1
                    ax.set(ylabel=col_list[ticker_count])
                    # t = ax.text(0., 0., col_list[ticker_count], horizontalalignment='center', verticalalignment='top', transform = ax.transAxes)
                    if i in (8, 7, 6):
                        ax.set_xticks(["2000", "2012", "2022"])
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
                        # Rotates and right-aligns the x labels so they don't crowd each other.
                        for label in ax.get_xticklabels(which='major'):
                            label.set(rotation=30, horizontalalignment='right')
                    else:
                        ax.set_xticks([])
                    fig.add_subplot(ax)
            fig.show()
        except:
            pass