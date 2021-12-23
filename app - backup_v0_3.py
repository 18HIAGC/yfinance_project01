# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu Jul 15 2021
# Last Update: 23/11/2021
# Script Name: streamlit_yfinance_v0_3.py
# Description: YFinance dashboard app for Streamlit
#
# Current app version: ver0.3 (Streamlit 1.00)
# @author: 18HIAGC
#
# =============================================================================

#%% Part 1.1: Imports

from datetime import datetime as dt
from datetime import timedelta
from timeit import default_timer

import altair as alt
from  pandas import concat as pd_concat
from  pandas import read_csv as pd_read_csv
import pandas_datareader.data as web
import streamlit as st

FILE_DIR = './data/' # base folder is the current directory
NSTOCKS_FILE = 'nasdaq_stocks_2010-21.csv'
YF_CLOSING_FILE = 'yf_closing_2021.csv'


#%% Part 1.1: Ticker codes and date setup

tickers = ['AAPL', 'AMZN', 'GOOG', 'MSFT', 'NFLX', 'TSLA']
symbol_input_default = tickers.index('AAPL')
PERIOD_INPUT_DEFAULT = '3M'

now_time = dt.now().strftime('%Y-%m-%d %H:%M')

now_date = dt.now().strftime('%Y-%m-%d')
now_date_minus3M = (dt.now() - timedelta(days=1)) - timedelta(weeks=13)
now_date_minus1Y = (dt.now() - timedelta(days=1)) - timedelta(weeks=52)
now_date_minus1d = (dt.now() - timedelta(days=1))

# Ticker data start and end
start_date = now_date_minus1Y
end_date = now_date_minus1d


#%% Part 2.1 : Page Setup (st.set_page_config)

# Title and Opening paragraph
st.set_page_config(
    page_title="Stock Price Dashboard",
	page_icon=":dollar:",
	layout="centered",
	initial_sidebar_state="expanded",
    menu_items={'About': "streamlit: yfinance app (ver 0.3) :panda_face: \
                \n added: live price quotes section \
                \n added: historical data graph \
                \n added: chart1 tooltips"
    }
)

st.title(':dollar: YFinance Stocks Dashboard :pound:')


#%% Part 2.2 Session State

if 'count' not in st.session_state:
    st.session_state['count'] = 0
    st.session_state['last_updated'] = dt.now()
    st.session_state['elapsed_time'] = 0


#%% Part 3 : Functions - Fetch Data / Plot Chart

def update_counter():
    """ Function to update the sessons state counters
    """
    st.session_state['count'] += 1
    st.session_state['elapsed_time'] = (dt.now() - st.session_state['last_updated']).total_seconds()
    st.session_state['last_updated'] = dt.now()


@st.cache
def read_historical_csv(nstocks_file):
    """ Functon to read fie for historical nasdaq stock prices and return df
    """
    nasdaq_df1 = pd_read_csv(FILE_DIR+nstocks_file, parse_dates=['date'])

    npivot_df1 = nasdaq_df1.pivot(index='date', columns='symbol', values='price')
    npivot_df1.reset_index(inplace=True)

    return nasdaq_df1, npivot_df1

@st.cache
def fetch_pdr_quote(tickers1, last_update_time1):
    """ Fn to fetch stock summary data for a list of stock codes
        Return: quote dataframe
    """
    quote_df1 = web.get_quote_yahoo(tickers1)

    return quote_df1


@st.cache
def fetch_closing_data(tickers1, yf_closing_file1):
    """ Fn to fetch pandas_data_reader up-to-date closing prices for listed
        stock codes and append to existing file data
        Return: ticker closing prices dataframe
    """
    old_closing_df = pd_read_csv(FILE_DIR+yf_closing_file1, parse_dates=['date'], index_col=0)
    old_closing_df = old_closing_df.reset_index()

    start_date1 =  old_closing_df['date'].max() + timedelta(days=1)
    end_date1 = now_date_minus1d

    if start_date1 < end_date1:
        new_closing_df = web.DataReader(name=tickers1, data_source='yahoo',
                                          start = start_date1, end = end_date1) \
                        .loc[:, 'Close'].reset_index()

        new_closing_df = new_closing_df.melt(id_vars = ['Date'], value_vars = tickers1)
        new_closing_df.columns = ['date', 'symbol', 'price']

        # join old and new data (axis=0 ~ join on rows)
        rclosing_df = pd_concat([old_closing_df, new_closing_df], axis=0, ignore_index=True)
        rclosing_df.sort_values(by=[ 'symbol','date'], inplace=True)

        # write closing data to file for later retrieval
        rclosing_df.to_csv(FILE_DIR+yf_closing_file1, index=False)

    else:
        rclosing_df = old_closing_df

    return rclosing_df


@st.cache
def read_closing_csv(yf_closing_file1):
    """ Functon to read file for up to date yfinance ticker stock closing prices
        Return: ticker closing prices dataframe
    """
    rclosing_df = pd_read_csv(FILE_DIR+yf_closing_file1, parse_dates=['date'], index_col=0)
    rclosing_df = rclosing_df.reset_index()

    return rclosing_df


def display_closing_chart(source, perc_chg1):
    """ Fn to display closing prices area charts using Altair
    """
    yrange = (source.price.min(), source.price.max())

    if perc_chg1 > 0:   area_color = 'darkGreen'
    elif perc_chg1 < 0: area_color = 'darkRed'
    else:               area_color = 'yellow'

    hover = alt.selection_single(
        fields=["date:T"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout"
    )

    chart1 = alt.Chart(source).mark_area(
                line={'color':area_color},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='white', offset=0),
                           alt.GradientStop(color=area_color, offset=1)],
                    x1=1,
                    x2=1,
                    y1=1,
                    y2=0
                )
            ).encode(
                alt.X('date:T'),
                alt.Y('price:Q', scale=alt.Scale(domain=yrange))
            ).properties(
            width=800, height=400
            )

    points = chart1.transform_filter(hover).mark_circle(opacity=1)

    tooltips = alt.Chart(source).mark_rule().encode(
            x='date:T',
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=['date:T', 'price:Q']
        ).add_selection(hover)

    # (chart1 + points + tooltips).show()
    st.altair_chart(chart1 + points + tooltips)


def display_historical_chart(source):
    """ Fn to display multiple line charts on a singe axis using Altair
        Input: nasdaq_df from fn: read_historical_csv
    """

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['date'], empty='none')

    selection_legend = alt.selection_multi(fields=['symbol'], bind='legend')

    # Define the basic line
    line = alt.Chart(source).mark_line().encode(
        x=alt.X('date:T', axis = alt.Axis(format=("%Y"))),

        y=alt.Y('price:Q',
                axis=alt.Axis(title='price ($)'),
                # scale=alt.Scale(domain=(0, 3750))
                ),
        color='symbol:N',
        opacity=alt.condition(selection_legend, alt.value(3), alt.value(0.2)),
        size=alt.value(4)
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='right', dx=-10, dy=-5).encode(
        text=alt.condition(nearest, 'price:Q', alt.value(''), format='.2f'),
        opacity=alt.condition(selection_legend, alt.value(1), alt.value(0.5)),
        size=alt.condition(selection_legend, alt.value(20), alt.value(10))
    )

    # Transparent selectors across the chart, tells us x-value of the cursor
    selectors = alt.Chart(source).mark_point().encode(
        x='date:T',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='right', dx=-10, dy=-5).encode(
        text=alt.condition(nearest, 'price:Q', alt.value(''), format='.2f'),
        opacity=alt.condition(selection_legend, alt.value(1), alt.value(0.5)),
        size=alt.condition(selection_legend, alt.value(20), alt.value(10))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(source).mark_rule(color='gray').encode(
        x='date:T',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    layer = alt.layer(
                line, selectors, points, rules, text
            ).properties(
                width=800, height=400
            ).add_selection(
                selection_legend
            )

    st.altair_chart(layer)


# %% Part 4 : Sidebar (Select Stock Symbol & Display Period)

# Sidebar Header
st.sidebar.header('User Inputs for closing prices')

with st.sidebar.form(key='sidebar_form'):
    st.subheader(':star: Make selection & click Submit')

    symbol_input = st.radio(label='Stock Symbol:', options=tickers,
                            index=symbol_input_default,
                            help='Choose one of the stock symbols to display')

    period_input = st.select_slider(label='Display period:',
                                   options=['1Y','6M', '3M','1M','1W'],
                                   value=PERIOD_INPUT_DEFAULT,
                                   help='Slide options: 1Year, 6Months, 3Months, 1Month, 1Week')

    period_map = {'1Y': 365,'6M': 182, '3M':91, '1M': 30,'1W': 7}
    period_input_map = period_map.get(period_input)
    now_date_minusT0 = (dt.now()) - timedelta(days=period_input_map)
    now_date_minusT1 = (dt.now() -timedelta(days=1)) - timedelta(days=period_input_map)

    st.write('selected period input {} days with start date: {}'
             .format(period_input_map, now_date_minusT0.strftime('%Y-%m-%d')))

    submit_button = st.form_submit_button(label=' Submit ',
                                          on_click=update_counter(),
                                          help='Click to Submit selections')


#%% Part 5.1 : Plot 1: Closing Price Plot - Read/Fetch Data

last_update_time = st.session_state['last_updated'].strftime('%Y-%m-%d %H:%M')

quote_fetch_df = fetch_pdr_quote(tickers, last_update_time)
quote_df = quote_fetch_df.loc[symbol_input, :]


# %% Part 5.2 : Plot 1: Display Quote live ticker data

st.header('**{}** Stock Closing Prices'.
          format(quote_df['displayName'].upper()) )

st.write('{} [{}]'.format(quote_df['longName'], symbol_input))
st.write('Current Price : {} {}'.format(quote_df['price'], quote_df['currency']))

st.write('Mkt State: {}'.format(quote_df['marketState']))

if quote_df['marketState'] == 'REGULAR':
    quote_mkt_time = quote_df['regularMarketTime']
elif quote_df['marketState'] == 'PREPRE':
    quote_mkt_time = quote_df['postMarketTime']
elif quote_df['marketState'] == 'PRE':
    quote_mkt_time = quote_df['preMarketTime']
elif  quote_df['marketState'] == 'CLOSED':
    quote_mkt_time = quote_df['postMarketTime']
else:
    quote_mkt_time = dt.now()

mkt_time = (dt.fromtimestamp(quote_mkt_time)).strftime('%Y-%m-%d %H:%M')
st.write('Last Update:  {}'.format(mkt_time))


t1 = default_timer()

# Fetch data from yfinance feed (no caching) on session start
if st.session_state['count'] < 2:
    closing_df = fetch_closing_data(tickers, YF_CLOSING_FILE)
else:
    # Fetch data from yf_closing file on subsequent updates
    closing_df = read_closing_csv(YF_CLOSING_FILE)

symbol_filter = closing_df['symbol'] == symbol_input
period_filter = (closing_df['date'] >= now_date_minusT1) & \
                    (closing_df['date'] < now_date)

filtered_df = closing_df[symbol_filter & period_filter]
filtered_df = filtered_df.sort_values(by=['date'], ascending=False)

filtered_df.reset_index(drop=True, inplace=True)


# %% Part 5.3 : Plot 1: Display Headers Closing Price Plot and DF


# if headers data is not blank continue, else display error message
if len(filtered_df) > 0 :

    p0 = filtered_df.iat[-1, 2]
    p1 = filtered_df.iat[0, 2]
    perc_chg = ((p1/p0)-1)*100

    nowT0_formatted = now_date_minusT0.strftime('%Y-%m-%d')
    st.write('perc. change since {}: {:+.2f}%'.format(nowT0_formatted, perc_chg))

    # Display Atair line-chart
    display_closing_chart(filtered_df, perc_chg)

    # Display raw data as a table
    st.write(filtered_df.style.format(precision=2,
                                          formatter={'date': '{:%Y-%m-%d}'}))
else:
    st.subheader('No data available')


# %% Part 6 : Display Plot 2,: Historical Price Plot

st.header('Historical NASDAQ Prices')

nasdaq_df, npivot_df = read_historical_csv(NSTOCKS_FILE)

# Display Atair historical line-chart
display_historical_chart(nasdaq_df)

# Display raw data as a table
st.dataframe(npivot_df.style.format(precision=2,
                formatter={'date': '{:%Y-%m-%d}'}, na_rep='-' ))
