
# -*- coding: utf-8 -*-
# =============================================================================
# Created on: 2022-03-21
# Script Name: app_test2.py
# Description: YFinance dashboard app for Streamlit
#
# Previously deployed app version: ver0.4 (Streamlit 1.30) - 2021-12-24
# Current version: ver0.5 (Streamlit 1.7.0)
# @author: 18HIAGC
# =============================================================================

#%% Part 1.1: Imports

from datetime import datetime as dt
from datetime import timedelta

import altair as alt
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials as sac
import pandas as pd
import pandas_datareader.data as web
import streamlit as st
# import yfinance as yf


FILE_DIR = './data/' # base folder is the current directory

NSTOCKS_FILE = 'nasdaq_stocks_2010-22.csv'
CLOSING_FILE = 'yf_closing_2021.csv'

NSTOCKS_PATH = FILE_DIR + NSTOCKS_FILE
CLOSING_PATH = FILE_DIR + CLOSING_FILE


#%% Part 1.1: Ticker codes and date setup

TICKERS = ['AAPL', 'AMZN', 'GOOG', 'MSFT', 'NFLX', 'TSLA']
symbol_input_default = TICKERS.index('AAPL')
PERIOD_INPUT_DEFAULT = '3M'

now_time = dt.now().strftime('%Y-%m-%d %H:%M')

now_date = dt.now().strftime('%Y-%m-%d')
now_date_minus3M = (dt.now().date() - timedelta(days=1)) - timedelta(weeks=13)
now_date_minus1Y = (dt.now().date() - timedelta(days=1)) - timedelta(weeks=52)
now_date_minus1d = (dt.now().date() - timedelta(days=1))

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
    menu_items={'About': "streamlit: yfinance app (ver 0.5 - 2022-03-15) :panda_face: \
                \n Updated: data file formats \
                \n Added: GSheets integration"
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
def read_historical_csv(nstocks_path1, tickers1):
    """ Functon to read locallly stored csv file for historical nasdaq stock
        prices and return df
    """
    npivot_df1 = pd.read_csv(nstocks_path1, parse_dates=['date'])
    nasdaq_df1 = npivot_df1.melt(id_vars = ['date'], value_vars = tickers1)
    nasdaq_df1.columns = ['date', 'symbol', 'price']

    return nasdaq_df1, npivot_df1

@st.cache
def read_closing_csv(closing_path1):
    """ Functon to read locallly stored csv file for closing stock
        prices and return df
    """
    closing_df1 = pd.read_csv(closing_path1, index_col=[0], parse_dates=['Date'])

    return closing_df1

@st.cache
def fetch_pdr_quote(tickers1):
    """ Fn to fetch stock summary data for a list of stock codes
        Return: quote dataframe
    """
    quote_df1 = web.get_quote_yahoo(tickers1)

    return quote_df1

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

    tooltips = alt.Chart(source).mark_rule().encode(
            x='date:T',
            opacity=alt.condition(hover, alt.value(0.9), alt.value(0)),
            tooltip=['date:T', 'price:Q']
        ).add_selection(hover)

    points = chart1.transform_filter(hover).mark_point(color='red')

    st.altair_chart(chart1 + tooltips + points)


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

    symbol_input = st.radio(label='Stock Symbol:', options=TICKERS,
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


# %% Part 5.1 : Plot 1: Closing Price Plot - Read/Fetch Data

# fetch last update time session state variable to feed to fetch_pdr_quote()
# the time variable indicates a change to time and necessity for fn rerun
last_update_time = st.session_state['last_updated'].strftime('%Y-%m-%d %H:%M')

quote_fetch_df = fetch_pdr_quote(TICKERS)
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
st.write('Last Update: {}'.format(mkt_time))


# %% Part 5.3 : Plot 1: Display Headers Closing Price Plot and DF


# Fetch data from yfinance feed / gsheets data file
closing_df = read_closing_csv(CLOSING_PATH)

# Filter closing_df data by sidebar selections
period_filter = (closing_df.index >= now_date_minusT1) & \
                    (closing_df.index < now_date)

filtered_df = closing_df[[symbol_input]][period_filter]
filtered_df = filtered_df.reset_index()
filtered_df.columns = ['date', 'price']
filtered_df = filtered_df.sort_index(ascending=False)

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# if headers data is not blank continue, else display error message
if len(filtered_df) > 0 :

    p0 = filtered_df.iat[-1, 1]
    p1 = filtered_df.iat[0, 1]
    period_perc_chg = (100*(p1 - p0)) / p0

    nowT0_formatted = now_date_minusT0.strftime('%Y-%m-%d')
    st.write('perc. change since {}: {:+.2f}%'.format(nowT0_formatted, period_perc_chg))

    # Display Atair line-chart
    display_closing_chart(filtered_df, period_perc_chg)

    # Display raw data as a table
    st.write(filtered_df.style.format(precision=2,formatter={'date': '{:%Y-%m-%d}'}))
else:
    st.subheader('No data available')


# %% Part 6 : Display Plot 2,: Historical Price Plot

st.header('Historical NASDAQ Prices')

nasdaq_df, npivot_df = read_historical_csv(NSTOCKS_PATH, TICKERS)

# Display Atair historical line-chart (using long format nasdaq data)
display_historical_chart(nasdaq_df)

# Display raw data as a table (using short format / pivoted nasdaq data)
st.dataframe(npivot_df.style.format(precision=2,
                formatter={'date': '{:%Y-%m-%d}'}, na_rep='-' ))
