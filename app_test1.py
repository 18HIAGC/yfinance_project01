# =============================================================================
# Created on Tue Sep  8 2020
# Last Update: 08/09/2020
# Script Name: app_test1.py
# Description: How to Build Your First Data Science Web App in Python
#   (Streamlit Tutorial Part 3) Pengiuns Dataset
#
# Link: https://www.youtube.com/watch?v=Eai1jaZrRDs&list=PLtqF5YXg7GLmCvTswG32NqQypOuYkPRUE&index=3
#       https://github.com/dataprofessor/code/tree/master/streamlit/part3
# Docs : https://www.streamlit.io/
#        https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet
# @author: Data_Professor
# =============================================================================

# To Run App in Browser:
# streamlit run Data_Prof_Streamlit_Tut3_penguins-app.py

#%% setup
import streamlit as st
import pandas as pd

FILE_DIR = './data/' # base folder is the current directory

#%% fn
def user_input_features():
    island = st.sidebar.selectbox('Island',('Biscoe','Dream','Torgersen'))
    sex = st.sidebar.selectbox('Sex',('male','female'))
    bill_length_mm = st.sidebar.slider('Bill length (mm)', 32.1,59.6,43.9)
    bill_depth_mm = st.sidebar.slider('Bill depth (mm)', 13.1,21.5,17.2)
    flipper_length_mm = st.sidebar.slider('Flipper length (mm)', 172.0,231.0,201.0)
    body_mass_g = st.sidebar.slider('Body mass (g)', 2700.0,6300.0,4207.0)
    data = {'island': island,
            'bill_length_mm': bill_length_mm,
            'bill_depth_mm': bill_depth_mm,
            'flipper_length_mm': flipper_length_mm,
            'body_mass_g': body_mass_g,
            'sex': sex}
    features = pd.DataFrame(data, index=[0])
    return features

#%% webpage markdown
st.write("""
# Penguin Prediction App :penguin:
This app predicts the **Palmer Penguin** species!
Data obtained from the [palmerpenguins library](https://github.com/allisonhorst/palmerpenguins) in R by Allison Horst.
""")

st.sidebar.header('User Input Features')

st.sidebar.markdown("""
[Example CSV input file](https://raw.githubusercontent.com/dataprofessor/data/master/penguins_example.csv)
""")

# Collects user input features into dataframe
uploaded_file = st.sidebar.file_uploader(FILE_DIR+'penguins_cleaned.csv', type=["csv"])
if uploaded_file is not None:
    input_df = pd.read_csv(uploaded_file)
else:
    input_df = user_input_features()

# Combines user input features with entire penguins dataset
# This will be useful for the encoding phase
penguins_raw = pd.read_csv(FILE_DIR+'penguins_cleaned.csv')
penguins = penguins_raw.drop(columns=['species'])
df = pd.concat([input_df,penguins],axis=0)

st.write(df)

# Encoding of ordinal features
# https://www.kaggle.com/pratik1120/penguin-dataset-eda-classification-and-clustering
encode = ['sex','island']
for col in encode:
    dummy = pd.get_dummies(df[col], prefix=col)
    df = pd.concat([df,dummy], axis=1)
    del df[col]
df = df[:1] # Selects only the first row (the user input data)

# Displays the user input features
st.subheader('User Input features')



