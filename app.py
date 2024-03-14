from flask import Flask, render_template_string
from dash import Dash, html, dcc, Input, Output
import pandas as pd
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

# Read data from CSV file
data_air = pd.read_csv("clean_data_air4thai.csv")
data_air["DATETIMEDATA"] = pd.to_datetime(data_air["DATETIMEDATA"], format="%Y-%m-%d %H:%M:%S")
data_air.sort_values("DATETIMEDATA", inplace=True)

# Read data from CSV file for prediction
data_pred = pd.read_csv("merged_data.csv")
data_pred["DATETIMEDATA"] = pd.to_datetime(data_pred["DATETIMEDATA"], format="%Y-%m-%d %H:%M:%S")
data_pred.sort_values("DATETIMEDATA", inplace=True)

# Define external stylesheets
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# Initialize Flask app
server = Flask(__name__)

# Initialize Dash app
app = Dash(__name__, server=server, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Air Quality Analytics: Understand Air Quality!"

navbar = html.Div(
    className="navbar",  # Added a class name for styling
    children=[
        html.Nav(
            className="nav",
            children=[
                html.A(' Analysis ', href='/'),
                html.A(' Prediction ', href='/page-2'),
            ]
        )
    ]
)

# Define layout of the Dash app
main = html.Div(
    children=[
        navbar,
        html.Div(
            children=[
                html.P(children="💨☁️💨", className="header-emoji"),
                html.H1(
                    children="Air Quality Analytics", className="header-title"
                ),
                html.P(
                    children="Analyze the air quality data",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Parameter", className="menu-title"),
                        dcc.Dropdown(
                            id="parameter-filter",
                            options=[
                                {"label": param, "value": param}
                                for param in data_air.columns[1:]
                            ],
                            value="PM25",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range",
                            className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=pd.to_datetime(data_air["DATETIMEDATA"]).min(),
                            max_date_allowed=pd.to_datetime(data_air["DATETIMEDATA"]).max(),
                            start_date=data_air["DATETIMEDATA"].min(),
                            end_date=data_air["DATETIMEDATA"].max(),
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Chart Type",
                            className="menu-title"
                        ),
                        dcc.Dropdown(
                            id="chart-type",
                            options=[
                                {"label": "Line Chart", "value": "line"},
                                {"label": "Bar Chart", "value": "bar"},
                                {"label": "Scatter Plot", "value": "scatter"},
                            ],
                            value="line",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="daily-stats", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            className="menu-title"
                        ),
                        html.Div(
                            id="stats-table",
                            className="stats-table"
                        ),
                    ],
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

# Define app callbacks

@app.callback(
    Output("stats-table", "children"),
    [
        Input("parameter-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_stats_table(selected_parameter, start_date, end_date):
    mask = (
        (data_air["DATETIMEDATA"] >= start_date)
        & (data_air["DATETIMEDATA"] <= end_date)
    )
    filtered_data = data_air.loc[mask]
    stats = filtered_data[selected_parameter].describe().reset_index().round(2)
    stats.columns = ["Statistic", "Value"]
    
    # Get the minimum and maximum values and their dates
    min_val = filtered_data[selected_parameter].min()
    min_date = filtered_data.loc[filtered_data[selected_parameter].idxmin()]["DATETIMEDATA"]
    max_val = filtered_data[selected_parameter].max()
    max_date = filtered_data.loc[filtered_data[selected_parameter].idxmax()]["DATETIMEDATA"]
    

    min_val_str = f"{min_val} ({min_date})"
    max_val_str = f"{max_val} ({max_date})"
    
    # Replace the min and max values in the stats dataframe
    stats.loc[stats["Statistic"] == "min", "Value"] = min_val_str
    stats.loc[stats["Statistic"] == "max", "Value"] = max_val_str
    
    # Remove rows corresponding to percentiles
    stats = stats[~stats["Statistic"].isin(['25%', '50%', '75%'])]
    
    stats_table = dbc.Table.from_dataframe(stats, striped=True, bordered=True, hover=True, className="custom-table")
    
    title = html.Div(children=f"Statistics - {selected_parameter}", className="menu-title")
    
    return [title, stats_table]

# Callback for updating chart
@app.callback(
    Output("chart", "figure"),
    [
        Input("parameter-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("chart-type", "value"),
    ],
)
def update_chart(selected_parameter, start_date, end_date, chart_type):
    mask = (
        (data_air["DATETIMEDATA"] >= start_date)
        & (data_air["DATETIMEDATA"] <= end_date)
    )
    filtered_data = data_air.loc[mask]
    
    if chart_type == "line":
        trace = {
            "x": filtered_data["DATETIMEDATA"],
            "y": filtered_data[selected_parameter],
            "type": "line",
        }
    elif chart_type == "scatter":
        trace = {
            "x": filtered_data["DATETIMEDATA"],
            "y": filtered_data[selected_parameter],
            "mode": "markers",  # Scatter plot with markers
            "type": "scatter",
        }
    elif chart_type == "bar":
        trace = {
            "x": filtered_data["DATETIMEDATA"],
            "y": filtered_data[selected_parameter],
            "type": "bar",
        }
        
    layout = {
        "title": f"Air Quality Over Time - {selected_parameter}",
        "xaxis": {"title": "Datetime"},
        "yaxis": {"title": selected_parameter},
        "colorway": ["#17B897"],  # or any other color
    }
    return {"data": [trace], "layout": layout}

# Callback for updating daily statistics chart
@app.callback(
    Output("daily-stats", "figure"),
    [
        Input("parameter-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_daily_stats(selected_parameter, start_date, end_date):
    mask = (
        (data_air["DATETIMEDATA"] >= start_date)
        & (data_air["DATETIMEDATA"] <= end_date)
    )
    filtered_data = data_air.loc[mask]

    # Group by date and calculate daily maximum, minimum, and mean values
    daily_stats = filtered_data.groupby(filtered_data["DATETIMEDATA"].dt.date)[selected_parameter].agg(['max', 'min', 'mean']).reset_index()

    # Create traces for each statistic
    traces = []
    for stat in ['max', 'min', 'mean']:
        traces.append(go.Scatter(
            x=daily_stats["DATETIMEDATA"],
            y=daily_stats[stat],
            mode='lines',
            name=stat.capitalize()  # Capitalize the statistic name for legend
        ))

    layout = {
        "title": f"Daily Statistics - {selected_parameter}",
        "xaxis": {"title": "Date"},
        "yaxis": {"title": selected_parameter},
        "colorway": ["#ECB365", "#064663", "#041C32"],  # Different color for each statistic
    }

    return {"data": traces, "layout": layout}



# Modify predict_layout to include the graph using data_pred
predict_layout = html.Div(
    children=[
        navbar,
        html.Div(
            children=[
                html.P(children="💨  😷  💨", className="header-emoji"),
                html.H1(
                    children="Predictions", className="header-title"
                ),
                html.P(
                    children="Visualize the predictions made by the model",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Parameter", className="menu-title"),
                        dcc.Dropdown(
                            id="parameter-filter-predict",
                            options=[
                                {"label": param, "value": param}
                                for param in data_pred.columns[1:]
                            ],
                            value="PM25",  # Adjust this according to your data
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
            ],
            
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="chart-predict", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            className="menu-title"
                        ),
                        html.Div(
                            id="stats-table-predict",
                            className="stats-table"
                        ),
                    ],
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)

# Callback for updating statistics table for prediction layout
@app.callback(
    Output("stats-table-predict", "children"),
    [
        Input("parameter-filter-predict", "value"),
    ],
)
def update_stats_table_predict(selected_parameter):
    start_date = data_pred["DATETIMEDATA"].min()
    end_date = data_pred["DATETIMEDATA"].max()
    
    mask = (
        (data_pred["DATETIMEDATA"] >= start_date)
        & (data_pred["DATETIMEDATA"] <= end_date)
    )
    filtered_data = data_pred.loc[mask]
    stats = filtered_data[selected_parameter].describe().reset_index().round(2)
    stats.columns = ["Statistic", "Value"]
    
    # Get the minimum and maximum values and their dates
    min_val = filtered_data[selected_parameter].min()
    min_date = filtered_data.loc[filtered_data[selected_parameter].idxmin()]["DATETIMEDATA"]
    max_val = filtered_data[selected_parameter].max()
    max_date = filtered_data.loc[filtered_data[selected_parameter].idxmax()]["DATETIMEDATA"]
    
    # Format strings for minimum and maximum values with dates
    min_val_str = f"{min_val} ({min_date})"
    max_val_str = f"{max_val} ({max_date})"
    
    # Replace the min and max values in the stats dataframe
    stats.loc[stats["Statistic"] == "min", "Value"] = min_val_str
    stats.loc[stats["Statistic"] == "max", "Value"] = max_val_str
    
    stats = stats[~stats["Statistic"].isin(['25%', '50%', '75%'])]

    stats_table = dbc.Table.from_dataframe(stats, striped=True, bordered=True, hover=True, className="custom-table")
    
    title = html.Div(children=f"Statistics - {selected_parameter}", className="menu-title")
    
    return [title, stats_table]

@app.callback(
    Output("chart-predict", "figure"),
    [
        Input("parameter-filter-predict", "value"),
    ],
)

def update_prediction_chart(selected_parameter):
    # Set threshold values for color coding
    low_threshold = 25
    high_threshold = 50
    very_high_threshold = 100

    # Generate graph
    trace = {
        "x": data_pred["DATETIMEDATA"],
        "y": data_pred[selected_parameter],
        "type": "bar",
        "marker": {
            "color": [
                "green" if val <= low_threshold else "orange" if low_threshold < val <= high_threshold else "yellow" if high_threshold < val <= very_high_threshold else "red" for val in data_pred[selected_parameter]
            ],
        },
    }

    

    layout = {
        "title": f"Predictions - {selected_parameter}",
        "xaxis": {"title": "Datetime"},
        "yaxis": {"title": selected_parameter},
    }
    return {"data": [trace], "layout": layout}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Interval(id='interval-component',interval=60000)
    ]
)

# Define Flask route to serve Dash app
@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/':
        return main
    elif pathname == '/page-2':
        return predict_layout

# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)