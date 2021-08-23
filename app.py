# -*- coding: utf-8 -*-
# =============================================================================
# Created on Thu Jul 15 2021
# Last Update: 23/08/2021
# Script Name: streamlit_yfinance01.py
# Description: YFinance dashboard app for Streamlit
#
# Current app version: ver0.1 (Streamlit 0.87)
# @author: 18HIAGC
# =============================================================================


#%% Part 1: Imports

import yfinance as yf
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np

stock_input1 = 'AAPL'
stock_input2 = 'NFLX'

ticker_start_date = '2020-01-01'
ticker_end_date = '2021-7-31'


#%% Part 2 : Page Setup (set_page_config), Title and Opening paragraph

st.set_page_config(
    page_title="Stock Price Dashboard",
	page_icon=":dollar:",
	layout="centered",
	initial_sidebar_state="expanded")

st.title(':dollar: YFinance Stock Price Dashboard :pound:')


st.markdown(
    """
<style>
.sidebar .sidebar-content {
    background-image: linear-gradient(#2e7bcf,#2e7bcf);
    color: white;
}

.css-1aumxhk {
background-color: #011839;
background-image: none;
color: #ffffff
}
</style>
""",
    unsafe_allow_html=True,
)


#%% Part 3 : Functions - Fetch Data

@st.cache
def ticker_data(stock_input1):
    #define the ticker symbol
    tickerSymbol = stock_input1

    #get data on this ticker
    tickerData = yf.Ticker(tickerSymbol)

    #get the historical prices for this ticker
    tickerDf = tickerData.history(period='3mo')
                    # start = ticker_start_date, end = ticker_end_date)
    ticker_info = tickerData.info

    return tickerDf, ticker_info

def display_line_chart(tickerDf, ticker_info):
    st.write('## Closing Price: ' + ticker_info['shortName'] + ' **(' \
         + ticker_info['symbol'] + ')**')
    st.line_chart(tickerDf.Close)
    # Open	High	Low	Close	Volume	Dividends	Stock Splits

    with st.container():

        # Display df_cs data
        with st.expander(label='Show/Hide data  ' +
                              ticker_info['symbol'], expanded=False):
            st.write(ticker_info['longBusinessSummary'])
            tickerDf[ticker_start_date:]

def display_altair_chart():
    np.random.seed(42)
    source = pd.DataFrame(np.cumsum(np.random.randn(100, 3), 0).round(2),
                        columns=['A', 'B', 'C'], index=pd.RangeIndex(100, name='x'))
    source = source.reset_index().melt('x', var_name='category', value_name='y')

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover',
                            fields=['x'], empty='none')

    # The basic line
    line = alt.Chart(source).mark_line(interpolate='basis').encode(
        x='x:Q',
        y='y:Q',
        color='category:N'
    )

    # Transparent selectors across the chart. This is what tells us
    # the x-value of the cursor
    selectors = alt.Chart(source).mark_point().encode(
        x='x:Q',
        opacity=alt.value(0),
    ).add_selection(
        nearest
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=5, dy=-5).encode(
        text=alt.condition(nearest, 'y:Q', alt.value(' '))
    )

    # Draw a rule at the location of the selection
    rules = alt.Chart(source).mark_rule(color='gray').encode(
        x='x:Q',
    ).transform_filter(
        nearest
    )

    # Put the five layers into a chart and bind the data
    layer = alt.layer(
                line, selectors, points, rules, text
            ).properties(
                width=600, height=300
            )

    st.altair_chart(layer)


#%% Part 4 : Closing Price Plot / tickerDf1 / tickerDf2

tickerDf1, ticker_info1 = ticker_data(stock_input1)
tickerDf2, ticker_info2 = ticker_data(stock_input2)

st.write('\n\n' + 'Stock **closing prices** of '
         + ticker_info1['longName'] +  ' & ' + ticker_info2['longName'] )


display_line_chart(tickerDf1, ticker_info1)
display_line_chart(tickerDf2, ticker_info2)
# display_altair_chart()


