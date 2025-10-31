import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output

# Load the datasets
ohlc_file = "Fortnightly_Sector_Indices.csv"
fpi_file = "Updated_FPI_Data_Formatted.csv"

df_ohlc = pd.read_csv(ohlc_file)
df_fpi = pd.read_csv(fpi_file)

# Standardize date formats
df_ohlc['date'] = pd.to_datetime(df_ohlc['date'], errors='coerce').dt.strftime('%d-%b-%y')
df_fpi.rename(columns={'Date': 'date', 'Sector': 'sector'}, inplace=True)
df_fpi['date'] = pd.to_datetime(df_fpi['date'], errors='coerce').dt.strftime('%d-%b-%y')

# Drop missing dates
df_ohlc.dropna(subset=['date'], inplace=True)
df_fpi.dropna(subset=['date'], inplace=True)

# Convert back to datetime for filtering
df_ohlc['date'] = pd.to_datetime(df_ohlc['date'], format='%d-%b-%y')
df_fpi['date'] = pd.to_datetime(df_fpi['date'], format='%d-%b-%y')

# Get available sectors
sectors = df_ohlc['sector'].dropna().unique()

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Sector Analysis Dashboard"),
    
    html.Label("Select Start Date:"),
    dcc.DatePickerSingle(
        id='start-date',
        min_date_allowed=df_ohlc['date'].min(),
        max_date_allowed=df_ohlc['date'].max(),
        date=df_ohlc['date'].min()
    ),
    
    html.Label("Select End Date:"),
    dcc.DatePickerSingle(
        id='end-date',
        min_date_allowed=df_ohlc['date'].min(),
        max_date_allowed=df_ohlc['date'].max(),
        date=df_ohlc['date'].max()
    ),
    
    html.Label("Select Sector:"),
    dcc.Dropdown(
        id='sector-dropdown',
        options=[{'label': sector, 'value': sector} for sector in sectors],
        value=sectors[0]
    ),
    
    dcc.Graph(id='candlestick-chart'),
    dcc.Graph(id='fpi-inflow-chart')
])

@app.callback(
    [Output('candlestick-chart', 'figure'),
     Output('fpi-inflow-chart', 'figure')],
    [Input('start-date', 'date'),
     Input('end-date', 'date'),
     Input('sector-dropdown', 'value')]
)
def update_charts(start_date, end_date, sector):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter OHLC data
    df_filtered = df_ohlc[(df_ohlc['date'] >= start_date) & (df_ohlc['date'] <= end_date) & (df_ohlc['sector'] == sector)]
    
    # Candlestick Chart
    fig_candle = go.Figure()
    fig_candle.add_trace(go.Candlestick(
        x=df_filtered['date'],
        open=df_filtered['open'],
        high=df_filtered['high'],
        low=df_filtered['low'],
        close=df_filtered['close'],
        name=f'{sector} Candlestick'
    ))
    fig_candle.update_layout(title=f"{sector} Candlestick Chart")
    
    # Filter FPI data
    df_fpi_filtered = df_fpi[(df_fpi['date'] >= start_date) & (df_fpi['date'] <= end_date) & (df_fpi['sector'] == sector)]
    
    # FPI Inflow Chart
    fig_fpi = go.Figure()
    fig_fpi.add_trace(go.Scatter(
        x=df_fpi_filtered['date'],
        y=df_fpi_filtered['Net FPI Change'],
        mode='lines+markers',
        name=f'{sector} FPI Inflow'
    ))
    fig_fpi.update_layout(title=f"{sector} FPI Inflow")
    
    return fig_candle, fig_fpi

if __name__ == '__main__':
    app.run(debug=True)



