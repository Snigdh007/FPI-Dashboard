import os
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

# Fix column names for FPI data (trim spaces and standardize)
fpi_df.rename(columns={"Date": "date", "Sector": "sector", "sector ": "sector"}, inplace=True)

# Convert 'date' columns to datetime format
ohlc_df["date"] = pd.to_datetime(ohlc_df["date"], errors="coerce")
fpi_df["date"] = pd.to_datetime(fpi_df["date"], errors="coerce")

# Drop rows with invalid dates
ohlc_df.dropna(subset=["date"], inplace=True)
fpi_df.dropna(subset=["date"], inplace=True)

# Merge both datasets based on date and sector
merged_df = pd.merge(ohlc_df, fpi_df, on=["date", "sector"], how="left")

# Fill NaN values in FPI column with 0 for plotting
merged_df["Net FPI Change"] = merged_df["Net FPI Change"].fillna(0)

# Get unique sectors
sectors = sorted(merged_df["sector"].dropna().unique())

# Initialize Dash App
app = dash.Dash(__name__)
server = app.server  # Expose Flask server for Gunicorn

# App Layout
app.layout = html.Div(
    style={
        "backgroundColor": "#0f0f0f",
        "color": "#ffffff",
        "fontFamily": "Arial, sans-serif",
        "minHeight": "100vh",
        "padding": "20px"
    },
    children=[
        html.Div(
            style={
                "maxWidth": "1400px",
                "margin": "0 auto",
                "backgroundColor": "#1a1a1a",
                "borderRadius": "10px",
                "padding": "30px",
                "boxShadow": "0 4px 6px rgba(0, 0, 0, 0.3)"
            },
            children=[
                html.H1(
                    "📊 Sector Analysis Dashboard",
                    style={
                        "textAlign": "center",
                        "color": "#4CAF50",
                        "marginBottom": "30px",
                        "fontSize": "2.5em"
                    }
                ),
                
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
                        "gap": "20px",
                        "marginBottom": "30px"
                    },
                    children=[
                        # Sector Selection
                        html.Div([
                            html.Label(
                                "Select Sector:",
                                style={"color": "#b0b0b0", "fontWeight": "bold", "marginBottom": "10px", "display": "block"}
                            ),
                            dcc.Dropdown(
                                id="sector-dropdown",
                                options=[{"label": sec, "value": sec} for sec in sectors],
                                value=sectors[0] if len(sectors) > 0 else None,
                                clearable=False,
                                style={
                                    "backgroundColor": "#2e2e2e",
                                    "color": "#000000",
                                    "borderRadius": "5px"
                                }
                            ),
                        ]),
                        
                        # Date Range Selection
                        html.Div([
                            html.Label(
                                "Select Date Range:",
                                style={"color": "#b0b0b0", "fontWeight": "bold", "marginBottom": "10px", "display": "block"}
                            ),
                            dcc.DatePickerRange(
                                id="date-picker",
                                min_date_allowed=merged_df["date"].min(),
                                max_date_allowed=merged_df["date"].max(),
                                start_date=merged_df["date"].min(),
                                end_date=merged_df["date"].max(),
                                display_format="DD-MMM-YYYY",
                                style={"borderRadius": "5px"}
                            ),
                        ]),
                    ]
                ),
                
                # Combined Chart
                html.Div([
                    html.H3(
                        "Candlestick Chart with FPI Net Change",
                        style={"color": "#e0e0e0", "marginBottom": "15px"}
                    ),
                    dcc.Graph(
                        id="candlestick-chart",
                        config={"displayModeBar": True, "displaylogo": False},
                        style={"height": "600px"}
                    )
                ]),
                
                # Statistics Section
                html.Div(
                    id="stats-section",
                    style={
                        "marginTop": "30px",
                        "padding": "20px",
                        "backgroundColor": "#252525",
                        "borderRadius": "8px",
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
                        "gap": "15px"
                    }
                )
            ]
        )
    ]
)


@app.callback(
    [Output("candlestick-chart", "figure"),
     Output("stats-section", "children")],
    [Input("sector-dropdown", "value"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date")]
)
def update_dashboard(selected_sector, start_date, end_date):
    # Filter data based on selections
    filtered_df = merged_df[
        (merged_df["sector"] == selected_sector) &
        (merged_df["date"] >= pd.to_datetime(start_date)) &
        (merged_df["date"] <= pd.to_datetime(end_date))
    ].sort_values("date")
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Add Candlestick chart
    fig.add_trace(go.Candlestick(
        x=filtered_df["date"],
        open=filtered_df["open"],
        high=filtered_df["high"],
        low=filtered_df["low"],
        close=filtered_df["close"],
        name="Price",
        increasing_line_color="#26A69A",
        decreasing_line_color="#EF5350"
    ))
    
    # Add FPI Bar Chart on secondary y-axis
    fig.add_trace(go.Bar(
        x=filtered_df["date"],
        y=filtered_df["Net FPI Change"],
        name="Net FPI Change",
        marker_color="rgba(100, 150, 255, 0.6)",
        yaxis="y2",
        hovertemplate="<b>Date:</b> %{x}<br><b>FPI Change:</b> %{y:.2f}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{selected_sector} - Candlestick & FPI Analysis",
        xaxis_title="Date",
        yaxis_title="Stock Price",
        yaxis2=dict(
            title="Net FPI Change",
            overlaying="y",
            side="right",
            showgrid=False
        ),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor="#1a1a1a",
        paper_bgcolor="#1a1a1a",
        font=dict(color="#e0e0e0"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    # Calculate statistics
    if not filtered_df.empty:
        stats = [
            create_stat_card("Total Records", f"{len(filtered_df)}"),
            create_stat_card("Avg Close", f"₹{filtered_df['close'].mean():.2f}"),
            create_stat_card("Highest", f"₹{filtered_df['high'].max():.2f}"),
            create_stat_card("Lowest", f"₹{filtered_df['low'].min():.2f}"),
            create_stat_card("Total FPI Change", f"₹{filtered_df['Net FPI Change'].sum():.2f}M"),
            create_stat_card("Avg FPI Change", f"₹{filtered_df['Net FPI Change'].mean():.2f}M"),
        ]
    else:
        stats = [html.Div("No data available for selected filters.", style={"color": "#ff6b6b"})]
    
    return fig, stats


def create_stat_card(label, value):
    """Helper function to create stat cards"""
    return html.Div(
        style={
            "textAlign": "center",
            "padding": "15px",
            "backgroundColor": "#303030",
            "borderRadius": "8px",
            "border": "1px solid #404040"
        },
        children=[
            html.Div(label, style={"color": "#b0b0b0", "fontSize": "0.9em", "marginBottom": "5px"}),
            html.Div(value, style={"color": "#4CAF50", "fontSize": "1.4em", "fontWeight": "bold"})
        ]
    )


# Run the app
if __name__ == "__main__":
    # Get port from environment variable (Render sets this automatically)
    port = int(os.environ.get("PORT", 8050))
    # Run in production mode
    app.run(debug=False, host="0.0.0.0", port=port)