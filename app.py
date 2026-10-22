import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

st.set_page_config(page_title='Value Call Opportunity Lab', page_icon='📈', layout='wide')
st.title('Value Call Opportunity Lab')
st.caption('Research dashboard • Uploaded CSV snapshots, not live prices • Scores are experimental, not investment advice')

@st.cache_data
def load_csv(name):
    path = Path(__file__).parent / name
    if not path.exists():
        return None
    return pd.read_csv(path)

stocks = load_csv('value_stock_rankings.csv')
options = load_csv('call_option_rankings.csv')
if stocks is None or options is None:
    st.error('Upload value_stock_rankings.csv and call_option_rankings.csv to the same GitHub folder as app.py.')
    st.stop()

stock_ticker = 'Ticker' if 'Ticker' in stocks.columns else None
option_ticker = 'Ticker' if 'Ticker' in options.columns else None
if not stock_ticker or not option_ticker:
    st.error('Both CSV files need a Ticker column.')
    st.stop()

all_sectors = sorted(stocks['Sector'].dropna().astype(str).unique()) if 'Sector' in stocks else []
selected_sectors = st.sidebar.multiselect('Sectors', all_sectors, default=all_sectors)
if all_sectors:
    stocks = stocks[stocks['Sector'].astype(str).isin(selected_sectors)]
selected_tickers = set(stocks['Ticker'].astype(str))
options = options[options['Ticker'].astype(str).isin(selected_tickers)]

c1, c2, c3 = st.columns(3)
c1.metric('Stocks in snapshot', f'{len(stocks):,}')
c2.metric('Option contracts', f'{len(options):,}')
c3.metric('Highest value score', f"{stocks['Value_Score'].max():.1f}" if len(stocks) and 'Value_Score' in stocks else 'N/A')

tab1, tab2, tab3 = st.tabs(['Value stock rankings', 'Call option rankings', 'Company details'])
with tab1:
    st.subheader('Value stock rankings')
    st.dataframe(stocks, use_container_width=True, hide_index=True)
    if {'FCF_Yield','Momentum_6M','Value_Score'}.issubset(stocks.columns):
        plot_df = stocks.dropna(subset=['FCF_Yield','Momentum_6M','Value_Score']).copy()
        if not plot_df.empty:
            kwargs = {'size': 'Market_Cap'} if 'Market_Cap' in plot_df.columns and (pd.to_numeric(plot_df['Market_Cap'], errors='coerce') > 0).all() else {}
            fig = px.scatter(plot_df, x='FCF_Yield', y='Momentum_6M', color='Value_Score', hover_name='Ticker', title='Free cash flow yield vs six-month momentum', **kwargs)
            st.plotly_chart(fig, use_container_width=True)
    st.download_button('Download filtered stocks', stocks.to_csv(index=False), 'filtered_value_stocks.csv', 'text/csv')
with tab2:
    st.subheader('Call option rankings')
    st.warning('Option quotes may be stale. Scores do not establish expected returns or probabilities of profit.')
    if 'Combined_Score' in options:
        options = options.sort_values('Combined_Score', ascending=False)
    st.dataframe(options, use_container_width=True, hide_index=True)
    if {'Value_Score','Option_Score','Combined_Score'}.issubset(options.columns):
        plot_df = options.dropna(subset=['Value_Score','Option_Score','Combined_Score'])
        if not plot_df.empty:
            fig = px.scatter(plot_df, x='Value_Score', y='Option_Score', color='Combined_Score', hover_name='Ticker', hover_data=[c for c in ['Strike','Expiration','Contract_Cost'] if c in plot_df.columns], title='Value strength vs option characteristics')
            st.plotly_chart(fig, use_container_width=True)
    st.download_button('Download filtered options', options.to_csv(index=False), 'filtered_call_options.csv', 'text/csv')
with tab3:
    names = sorted(stocks['Ticker'].dropna().astype(str).unique())
    if names:
        ticker = st.selectbox('Select a ticker', names)
        st.subheader(f'{ticker}: stock data')
        st.dataframe(stocks[stocks['Ticker'].astype(str) == ticker], use_container_width=True, hide_index=True)
        st.subheader('Available contracts in your snapshot')
        subset = options[options['Ticker'].astype(str) == ticker]
        if subset.empty:
            st.info('No qualifying contracts for this ticker in the uploaded snapshot.')
        else:
            st.dataframe(subset, use_container_width=True, hide_index=True)
    else:
        st.info('No stocks match the current sector selection.')
