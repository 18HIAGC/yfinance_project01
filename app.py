# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu 2021-07-15
# Last Update: 2025-03-21
# Script Name: streamlit_yfinance_v0_6.py
# Description: YFinance dashboard app for Streamlit
#
# Previously deployed app version: ver0.5 (Streamlit 1.30) - 2023-03-15
# Current version: ver0.6.3 (Streamlit 1.43.2)
# @author: 18HIAGC
# =============================================================================

#%% Part 1.1: Imports

import altair as alt
from datetime import datetime as dt
from datetime import timedelta
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf


#%% Part 1.2: Parameters & Additional Setup

SPREADSHEET_URL = st.secrets.connections.gsheets_yfinance.spreadsheet
WORKSHEET_NAME= st.secrets.connections.gsheets_yfinance.worksheet

TICKERS = ['AAPL', 'AMZN', 'GOOG', 'MSFT', 'NFLX', 'TSLA']
SYMBOL_INPUT_DEFAULT = 0

PERIOD_INPUT_DEFAULT = '3M'

#%% Part 1.3: Date Setup


now_time = dt.now().strftime('%Y-%m-%d %H:%M')
# now_date = dt.now().strftime('%Y-%m-%d')
now_date = dt.now().date()

now_date_minus1D = (dt.now().date() - timedelta(days=1))
now_date_minus1W = now_date_minus1D - timedelta(days=7)
now_date_minus3M = now_date_minus1D - timedelta(weeks=13)
now_date_minus6M = now_date_minus1D - timedelta(weeks=26)
now_date_minus1Y = now_date_minus1D - timedelta(weeks=52)
now_year = now_date_minus1D.year

# Ticker data start and end
start_date = now_date_minus1Y
end_date = now_date_minus1D # end_date is yesterday to get yesterday's close


#%% Part 2.1 : Page Setup (st.set_page_config - must be called as the first
# Streamlit command in your script)

# Title and Opening paragraph
st.set_page_config(
    page_title="Stock Price Dashboard",
	page_icon=":dollar:",
	layout="centered",
	initial_sidebar_state="expanded",
    menu_items={'About': "streamlit: yfinance app (ver 0.6 - 2025-03-21) :panda_face: \
                \n Updated: data file formats \
                \n Updated: streamlit_gsheets integration \
                \n \
                \n contact author: 18.HIAGC+STREAMLIT@GMAIL.COM \
                \n "
    }
)

st.title(':dollar: YFinance Stocks Dashboard :pound:')


# %% Part 2.2 : GSheetsConnection : gsheets_yfinance

# Create a connection object with st.connection()
# st.connection() handles secrets retrieval, setup, query caching and retries.
conn_yf = st.connection("gsheets_yfinance", type = GSheetsConnection)


#%% Part 2.3 Session State

if 'count' not in st.session_state:
    st.session_state['count'] = 0
    st.session_state['last_updated'] = dt.now()
    st.session_state['elapsed_time'] = 0


#%% Part 3 : Functions - Fetch Data / Plot Chart

def update_counter():
    """ Function to update the sessons state counters
    """
    st.session_state['count'] += 1
    st.session_state['elapsed_time'] = ( dt.now() - st.session_state['last_updated'] ).total_seconds()

    st.session_state['last_updated'] = dt.now()

    return None


@st.cache_data
def gsheet2df(spreadsheet_name, wsheet_name):
    """ Function to fetch a google sheet and convert it into a df """
    # read from private google sheets worksheet
    df1 = conn_yf.read(spreadsheet=spreadsheet_name,
                       worksheet=wsheet_name)
    # df1.set_index('Date', drop=True, inplace=True)

    return df1


@st.cache_data
def new_closing_feed2(start_date1, end_date1, tickers1):
    """ Function to fetch closing price data from the YFinance feed
        Return: closing_df (df)
    """
    yf_df = yf.download(
    	tickers=tickers1,
    	threads=True,      # built-in multithreading
        start=start_date1,
        end=end_date1,
        auto_adjust=True)  # auto-adjusted prices

    # filter for column level Price = 'Close'
    closing_df = yf_df.xs('Close', axis=1, level='Price')
    # rounding of decimal values to 2 places
    closing_df = closing_df.round(decimals = 2)
    # convert index from data type: datetime.DatetimeIndex to datetime.date
    closing_df.index = closing_df.index.date

    return closing_df


@st.cache_data
def display_closing_chart(source, perc_chg1):
    """ Fn to display closing prices area charts using Altair
    """
    # yrange = (source.price.min(), source.price.max())

    if perc_chg1 > 0:   area_color = 'darkGreen'
    elif perc_chg1 < 0: area_color = 'darkRed'
    else:               area_color = 'yellow'

    # hover = alt.selection_single(
    #     fields=["date:T"],
    #     nearest=True,
    #     on="mouseover",
    #     empty="none",
    #     clear="mouseout"
    # )

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
                # alt.Y('price:Q', scale=alt.Scale(domain=yrange))
                alt.Y('price:Q')
            ).properties(
            width=800, height=400
            )

    # tooltips = alt.Chart(source).mark_rule().encode(
    #         x='date:T',
    #         opacity=alt.condition(hover, alt.value(0.9), alt.value(0)),
    #         tooltip=['date:T', 'price:Q']
    #     ).add_selection(hover)

    # points = chart1.transform_filter(hover).mark_point(color='red')

    st.altair_chart(chart1)# + points + tooltips)


@st.cache_data
def display_historical_chart(source):
    """ Fn to display multiple line charts on a singe axis using Altair
        Input: nasdaq_df from fn: read_historical_csv
    """
    # a selection that chooses the nearest x-value point
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
                            index=SYMBOL_INPUT_DEFAULT,
                            help='Choose one of the stock symbols to display')

    period_input = st.select_slider(label='Display period:',
                                   options=['1Y','6M','3M','1M','1W'],
                                   value=PERIOD_INPUT_DEFAULT,
                                   help='Slide options: 1Year, 6Months, 3Months, 1Month, 1Week')

    period_map = {'1Y': 365,'6M': 182, '3M':91, '1M': 30,'1W': 7}
    period_input_map = period_map.get(period_input)
    now_date_minusT0 = (dt.now().date()) - timedelta(days=period_input_map)

    now_date_minusT1 = (dt.now().date() - timedelta(days=1)) - timedelta(days=period_input_map)

    st.write('selected period input {} days'.format(period_input_map))

    st.write('from date: ', now_date_minusT0)
    st.write('to date: ', now_date_minusT1)

    submit_button = st.form_submit_button(label=' Submit ',
                                          on_click=update_counter(),
                                          help='Click to Submit selections')


# %% Part 5 : Display Headers & Closing Price Plot (PLot 1) and DF

# Fetch data from yfinance feed / gsheets data file
closing_df = new_closing_feed2(start_date1 = now_date_minus1Y,
                               end_date1 = dt.now().date(),
                               tickers1 = TICKERS)

# Filter closing_df data by sidebar selections
period_filter = (closing_df.index >= now_date_minusT1) & \
                    (closing_df.index < now_date)

filtered_df = closing_df[[symbol_input]][period_filter]
filtered_df = filtered_df.reset_index()
filtered_df.columns = ['date', 'price']

# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# if headers data is not blank continue, else display error message
if len(filtered_df) > 0 :

    price_orig = filtered_df.iat[0, 1]
    price_new = filtered_df.iat[-1, 1]

    st.write('1st price: ', price_orig, ' date: ', now_date_minus1Y )
    st.write('last price: ', price_new, ' date: ', now_date )

    period_perc_chg = ((price_new - price_orig) / price_orig) * 100

    st.write('{} stock % change since {}: {:+.2f}%'.format(symbol_input,
                                               now_date_minusT0,
                                               period_perc_chg))

    # Display Atair line-chart
    display_closing_chart(filtered_df, period_perc_chg)

    filtered_df = filtered_df.sort_index(ascending=False)
    # Display raw data as a table
    st.dataframe(filtered_df)

else:
    st.subheader('No data available')


# %% Part 6 : Display Plot 2: Historical Price Plot

st.header('Historical NASDAQ Prices')

# nasdaq_df, npivot_df = read_historical_csv(NSTOCKS_PATH, TICKERS)
nasdaq_df = gsheet2df(SPREADSHEET_URL, WORKSHEET_NAME)

# melt df i.e. unpivot data
df_melt = nasdaq_df.melt(id_vars=['Date'])
df_melt.columns=['date', 'symbol','price']

# Display Atair historical line-chart (using long format nasdaq data)
display_historical_chart(df_melt)

# Display raw data as a table
st.write(nasdaq_df)
