import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Load your cleaned data
print("Loading data...")
df = pd.read_csv('nyc_crashes_integrated_clean.csv', low_memory=False)

# Convert date column
df['CRASH_DATE_DT'] = pd.to_datetime(df['CRASH_DATE_DT'])

print(f"Data loaded: {len(df):,} records")

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # For deployment

# Define the layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("NYC Motor Vehicle Crashes Dashboard",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Interactive analysis of 1.97M crash records (2012-2025)",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

    # Enhanced Filter Panel with MORE filters
    html.Div([
        html.H3("Filters", style={'color': '#2c3e50'}),

        html.Div([
            # Borough Filter
            html.Div([
                html.Label("Borough:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='borough-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': b, 'value': b} for b in sorted(df['BOROUGH'].unique())],
                    value='All',
                    clearable=False
                )
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            # Year Filter
            html.Div([
                html.Label("Year:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='year-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': y, 'value': y} for y in sorted(df['YEAR'].unique())],
                    value='All',
                    clearable=False
                )
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            # Vehicle Type Filter (NEW!)
            html.Div([
                html.Label("Vehicle Type:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='vehicle-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': v, 'value': v} for v in sorted(df['VEHICLE_TYPE_STANDARD'].unique())],
                    value='All',
                    clearable=False
                )
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            # Severity Filter
            html.Div([
                html.Label("Severity:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='severity-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': s, 'value': s} for s in df['CRASH_SEVERITY'].unique()],
                    value='All',
                    clearable=False
                )
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            # Time of Day Filter (NEW!)
            html.Div([
                html.Label("Time of Day:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='timeofday-filter',
                    options=[{'label': 'All', 'value': 'All'}] +
                            [{'label': t, 'value': t} for t in df['TIME_OF_DAY'].unique()],
                    value='All',
                    clearable=False
                )
            ], style={'width': '18%', 'display': 'inline-block'})
        ]),

        # Search Box (NEW!)
        html.Div([
            html.Label("Search (e.g., 'Brooklyn 2022 pedestrian'):",
                       style={'fontWeight': 'bold', 'marginTop': '20px'}),
            dcc.Input(
                id='search-input',
                type='text',
                placeholder='Enter search terms...',
                style={'width': '70%', 'padding': '10px', 'marginRight': '2%'}
            ),
            html.Button('Clear Search', id='clear-search-btn', n_clicks=0,
                        style={'padding': '10px 20px', 'backgroundColor': '#95a5a6',
                               'color': 'white', 'border': 'none', 'cursor': 'pointer'})
        ], style={'marginTop': '20px'}),

        # Generate Report Button
        html.Div([
            html.Button('🔍 Generate Report', id='generate-btn', n_clicks=0,
                        style={'padding': '15px 40px', 'fontSize': '18px', 'backgroundColor': '#3498db',
                               'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer',
                               'marginTop': '20px'})
        ], style={'textAlign': 'center'})

    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px'}),

    # Summary Stats
    html.Div(id='summary-stats', style={'padding': '20px', 'backgroundColor': '#fff', 'marginBottom': '20px'}),

    # Visualizations (6 charts now!)
    html.Div([
        html.Div([
            dcc.Graph(id='crashes-over-time')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='severity-pie')
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),

    html.Div([
        html.Div([
            dcc.Graph(id='borough-bar')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='hourly-bar')  # NEW CHART!
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),

    html.Div([
        dcc.Graph(id='heatmap')  # NEW CHART!
    ]),

    html.Div([
        dcc.Graph(id='map-scatter')  # NEW CHART!
    ])

], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


# Enhanced callback with MORE outputs
@app.callback(
    [Output('summary-stats', 'children'),
     Output('crashes-over-time', 'figure'),
     Output('severity-pie', 'figure'),
     Output('borough-bar', 'figure'),
     Output('hourly-bar', 'figure'),
     Output('heatmap', 'figure'),
     Output('map-scatter', 'figure')],
    [Input('generate-btn', 'n_clicks')],
    [State('borough-filter', 'value'),
     State('year-filter', 'value'),
     State('vehicle-filter', 'value'),
     State('severity-filter', 'value'),
     State('timeofday-filter', 'value'),
     State('search-input', 'value')]
)
def update_dashboard(n_clicks, borough, year, vehicle, severity, timeofday, search_text):
    # Start with full dataset
    filtered_df = df.copy()

    # Apply ALL filters
    if borough != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == borough]
    if year != 'All':
        filtered_df = filtered_df[filtered_df['YEAR'] == year]
    if vehicle != 'All':
        filtered_df = filtered_df[filtered_df['VEHICLE_TYPE_STANDARD'] == vehicle]
    if severity != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_SEVERITY'] == severity]
    if timeofday != 'All':
        filtered_df = filtered_df[filtered_df['TIME_OF_DAY'] == timeofday]

    # Apply search
    if search_text:
        search_lower = search_text.lower()
        mask = (
                filtered_df['BOROUGH'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['VEHICLE_TYPE_STANDARD'].str.lower().str.contains(search_lower, na=False) |
                filtered_df['CONTRIBUTING FACTOR VEHICLE 1'].str.lower().str.contains(search_lower, na=False)
        )
        filtered_df = filtered_df[mask]

    # Summary statistics
    total_crashes = len(filtered_df)
    total_injuries = filtered_df['NUMBER OF PERSONS INJURED'].sum()
    total_fatalities = filtered_df['NUMBER OF PERSONS KILLED'].sum()
    ped_crashes = filtered_df['PEDESTRIAN_INVOLVED'].sum()

    summary = html.Div([
        html.H3("📊 Summary Statistics", style={'color': '#2c3e50'}),
        html.Div([
            html.Div([
                html.H2(f"{total_crashes:,}", style={'color': '#3498db', 'margin': '0'}),
                html.P("Total Crashes", style={'margin': '0'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '1%'}),

            html.Div([
                html.H2(f"{int(total_injuries):,}", style={'color': '#f39c12', 'margin': '0'}),
                html.P("Injuries", style={'margin': '0'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '1%'}),

            html.Div([
                html.H2(f"{int(total_fatalities):,}", style={'color': '#e74c3c', 'margin': '0'}),
                html.P("Fatalities", style={'margin': '0'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '1%'}),

            html.Div([
                html.H2(f"{int(ped_crashes):,}", style={'color': '#9b59b6', 'margin': '0'}),
                html.P("Pedestrian Involved", style={'margin': '0'})
            ], style={'width': '23%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '20px', 'backgroundColor': '#ecf0f1', 'margin': '1%'})
        ])
    ])

    # Chart 1: Crashes over time
    yearly_data = filtered_df.groupby('YEAR').size().reset_index(name='count')
    fig1 = px.line(yearly_data, x='YEAR', y='count',
                   title='Crashes Over Time',
                   labels={'count': 'Number of Crashes', 'YEAR': 'Year'})
    fig1.update_traces(line_color='#3498db', line_width=3)
    fig1.update_layout(template='plotly_white', height=400)

    # Chart 2: Severity pie
    severity_data = filtered_df['CRASH_SEVERITY'].value_counts()
    fig2 = px.pie(values=severity_data.values, names=severity_data.index,
                  title='Crash Severity Distribution',
                  color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c'])
    fig2.update_layout(template='plotly_white', height=400)

    # Chart 3: Borough bar
    borough_data = filtered_df['BOROUGH'].value_counts().head(10)
    fig3 = px.bar(x=borough_data.index, y=borough_data.values,
                  title='Crashes by Borough',
                  labels={'x': 'Borough', 'y': 'Number of Crashes'})
    fig3.update_traces(marker_color='#3498db')
    fig3.update_layout(template='plotly_white', height=400)

    # Chart 4: Hourly distribution (NEW!)
    hourly_data = filtered_df['HOUR'].value_counts().sort_index()
    fig4 = px.bar(x=hourly_data.index, y=hourly_data.values,
                  title='Crashes by Hour of Day',
                  labels={'x': 'Hour', 'y': 'Number of Crashes'})
    fig4.update_traces(marker_color='#e67e22')
    fig4.update_layout(template='plotly_white', height=400)

    # Chart 5: Heatmap (NEW!)
    heatmap_data = filtered_df.groupby(['DAY_OF_WEEK_NUM', 'HOUR']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='DAY_OF_WEEK_NUM', columns='HOUR', values='count')

    fig5 = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        colorscale='YlOrRd'
    ))
    fig5.update_layout(
        title='Crash Heatmap: Day × Hour',
        xaxis_title='Hour of Day',
        yaxis_title='Day of Week',
        template='plotly_white',
        height=500
    )

    # Chart 6: Map (NEW!)
    map_sample = filtered_df[filtered_df['LATITUDE'].notna()].sample(
        n=min(5000, len(filtered_df)), random_state=42
    )
    fig6 = px.scatter_mapbox(
        map_sample,
        lat='LATITUDE',
        lon='LONGITUDE',
        color='CRASH_SEVERITY',
        color_discrete_map={
            'Fatal': '#e74c3c',
            'Injury': '#f39c12',
            'Property Damage Only': '#2ecc71'
        },
        title=f'Crash Locations (Sample of {len(map_sample):,})',
        zoom=10,
        height=600
    )
    fig6.update_layout(mapbox_style="open-street-map")

    return summary, fig1, fig2, fig3, fig4, fig5, fig6


# Callback to clear search (NEW!)
@app.callback(
    Output('search-input', 'value'),
    Input('clear-search-btn', 'n_clicks')
)
def clear_search(n_clicks):
    if n_clicks > 0:
        return ''
    return dash.no_update


if __name__ == '__main__':
    app.run(debug=True, port=8050)
