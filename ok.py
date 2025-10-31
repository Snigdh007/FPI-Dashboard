import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# File paths
ohlc_file = "Fortnightly_Sector_Indices.csv"
fpi_file = "Updated_FPI_Data_Formatted.csv"

# Load OHLC data
ohlc_df = pd.read_csv(ohlc_file)

# Load FPI data
fpi_df = pd.read_csv(fpi_file)

# Fix column names for FPI data (trim spaces)
fpi_df.rename(columns={"Date": "date", "sector ": "sector"}, inplace=True)

# Convert 'date' columns to datetime format
ohlc_df["date"] = pd.to_datetime(ohlc_df["date"], errors="coerce")
fpi_df["date"] = pd.to_datetime(fpi_df["date"], errors="coerce")

# Merge both datasets based on date and sector
merged_df = pd.merge(ohlc_df, fpi_df, on=["date", "sector"], how="left")

# Fill NaN values in FPI column with 0 for plotting
merged_df["Net FPI Change"] = merged_df["Net FPI Change"].fillna(0)

# Get unique sectors
sectors = merged_df["sector"].dropna().unique()

# Dash App
app = dash.Dash(__name__)

app.layout = html.Div(style={"backgroundColor": "#1e1e1e", "color": "white", "padding": "20px"}, children=[
    html.H1("Candlestick & FPI Bar Chart", style={"textAlign": "center", "color": "white"}),

    # Dropdown for Sector Selection
    html.Label("Select Sector:", style={"color": "white"}),
    dcc.Dropdown(
        id="sector-dropdown",
        options=[{"label": sec, "value": sec} for sec in sectors],
        value=sectors[0],  # Default selection
        clearable=False,
        style={"backgroundColor": "#2e2e2e", "color": "black"}
    ),

    # Date Picker for Start and End Date
    html.Label("Select Date Range:", style={"color": "white"}),
    dcc.DatePickerRange(
        id="date-picker",
        min_date_allowed=merged_df["date"].min(),
        max_date_allowed=merged_df["date"].max(),
        start_date=merged_df["date"].min(),
        end_date=merged_df["date"].max(),
        display_format="YYYY-MM-DD"
    ),

    # Graph
    dcc.Graph(id="candlestick-chart", style={"backgroundColor": "#1e1e1e", "color": "white"})
])


@app.callback(
    Output("candlestick-chart", "figure"),
    Input("sector-dropdown", "value"),
    Input("date-picker", "start_date"),
    Input("date-picker", "end_date")
)
def update_chart(selected_sector, start_date, end_date):
    # Filter data
    filtered_df = merged_df[
        (merged_df["sector"] == selected_sector) &
        (merged_df["date"] >= pd.to_datetime(start_date)) &
        (merged_df["date"] <= pd.to_datetime(end_date))
    ]

    # Create Figure
    fig = go.Figure()

    # Add Candlestick
    fig.add_trace(go.Candlestick(
        x=filtered_df["date"],
        open=filtered_df["open"],
        high=filtered_df["high"],
        low=filtered_df["low"],
        close=filtered_df["close"],
        name="Candlestick"
    ))

    # Add FPI Bar Chart
    fig.add_trace(go.Bar(
        x=filtered_df["date"],
        y=filtered_df["Net FPI Change"],
        name="Net FPI Change",
        marker_color="blue",
        yaxis="y2"
    ))

    # Update Layout
    fig.update_layout(
        title=f"Candlestick & FPI Chart ({selected_sector})",
        xaxis_title="Date",
        yaxis_title="Stock Price",
        yaxis2=dict(
            title="Net FPI Change",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig


# Run Server
if __name__ == "__main__":
    app.run(debug=True)




