import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import plotly.express as px
import numpy as np

# Function to parse HTML and create a DataFrame
def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = []
    table = soup.find('table')
    rows = table.find_all('tr')[2:]
    for row in rows:
        cols = row.find_all('td')
        data.append([col.text.strip() for col in cols])
    columns = ['Ticket', 'Open Time', 'Type', 'Size', 'Item', 'Open Price', 'S/L', 'T/P', 'Close Time', 'Close Price', 'Commission', 'Taxes', 'Swap', 'Profit']
    df = pd.DataFrame(data, columns=columns)
    numeric_cols = ['Size', 'Open Price', 'Close Price', 'Commission', 'Taxes', 'Swap', 'Profit']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].replace({',': ''}, regex=True), errors='coerce')
    df['Open Time'] = pd.to_datetime(df['Open Time'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
    return df

# Function to calculate trading metrics
def calculate_metrics(df):
    df['Profit/Loss'] = df['Profit']
    df['Cumulative Profit/Loss'] = df['Profit/Loss'].cumsum()
    roll_max = df['Cumulative Profit/Loss'].cummax()
    daily_drawdown = df['Cumulative Profit/Loss'] - roll_max
    df['Drawdown'] = daily_drawdown
    return df

# Function to plot interactive area charts
def plot_interactive_area_chart(data, title, xlabel, ylabel):
    fig = px.area(data, x=xlabel, y=ylabel, title=title)
    fig.update_traces(line=dict(width=0.5), marker=dict(size=4),
                      mode='lines+markers', hoverinfo='text+name', text=ylabel)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#E1E1E1',
        title_font_color='#E1E1E1',
        hovermode="x unified",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig, use_container_width=True)

# Streamlit app layout
st.title('Financial Statement Analysis')
st.markdown("##")

uploaded_file = st.file_uploader("Upload your HTML statement file", type=['html'], key='unique_uploader_key')
if uploaded_file is not None:
    html_content = uploaded_file.read().decode("utf-8")
    df = parse_html(html_content)
    df = calculate_metrics(df)
    
    max_drawdown = np.min(df['Drawdown'])
    st.metric(label="Max Drawdown", value=f"{max_drawdown:.2f}")

    if st.checkbox('Show parsed data with metrics'):
        st.dataframe(df[['Ticket', 'Profit/Loss', 'Cumulative Profit/Loss', 'Drawdown']])
    
    col1, col2 = st.columns(2)
    with col1:
        profit_df = df[df['Profit/Loss'] > 0]
        if not profit_df.empty:
            plot_interactive_area_chart(profit_df, 'Profit over Time', 'Open Time', 'Profit/Loss')
        loss_df = df[df['Profit/Loss'] < 0]
        if not loss_df.empty:
            plot_interactive_area_chart(loss_df, 'Loss over Time', 'Open Time', 'Profit/Loss')
    
    with col2:
        if not df.empty:
            plot_interactive_area_chart(df, 'Cumulative Profit/Loss Over Time', 'Open Time', 'Cumulative Profit/Loss')
            plot_interactive_area_chart(df, 'Account Balance Growth Over Time', 'Open Time', 'Cumulative Profit/Loss')
