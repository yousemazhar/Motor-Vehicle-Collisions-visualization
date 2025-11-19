import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Load data
print("Loading data...")
df = pd.read_csv('nyc_crashes_integrated_clean.csv', low_memory=False)
df['CRASH_DATE_DT'] = pd.to_datetime(df['CRASH_DATE_DT'])
print(f"Data loaded: {len(df):,} records")

# Initialize app
app = dash.Dash(__name__)
server = app.server

# Define smart column choices for each graph type
TEMPORAL_COLS = ['YEAR', 'MONTH', 'DAY_OF_WEEK', 'HOUR', 'TIME_OF_DAY']
CATEGORICAL_COLS = ['BOROUGH', 'CRASH_SEVERITY', 'VEHICLE_TYPE_STANDARD',
                    'CONTRIBUTING FACTOR VEHICLE 1', 'DAY_OF_WEEK', 'TIME_OF_DAY']
NUMERIC_COLS = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'NUMBER OF PEDESTRIANS INJURED', 'NUMBER OF CYCLIST INJURED',
                'NUMBER OF MOTORIST INJURED']

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("NYC Motor Vehicle Crashes Dashboard - Dynamic Edition",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Interactive analysis with customizable visualizations",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

    # Filter Panel
    html.Div([
        html.H3("Filters", style={'color': '#2c3e50'}),
        html.Div([
            html.Div([
                html.Label("Borough:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='borough-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': b, 'value': b} for b in sorted(df['BOROUGH'].dropna().unique())],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Year:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='year-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': y, 'value': y} for y in sorted(df['YEAR'].unique())],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Vehicle Type:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='vehicle-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': v, 'value': v} for v in
                                      sorted(df['VEHICLE_TYPE_STANDARD'].dropna().unique())],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Severity:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='severity-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': s, 'value': s} for s in df['CRASH_SEVERITY'].unique()],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Time of Day:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='timeofday-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': t, 'value': t} for t in df['TIME_OF_DAY'].unique()],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block'})
        ]),

        html.Div([
            html.Button('🔍 Generate Report', id='generate-btn', n_clicks=0,
                        style={'padding': '15px 40px', 'fontSize': '18px', 'backgroundColor': '#3498db',
                               'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer',
                               'marginTop': '20px'})
        ], style={'textAlign': 'center'})

    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px'}),

    # Summary Stats
    html.Div(id='summary-stats', style={'backgroundColor': '#fff', 'marginBottom': '20px'}),

    # Row 1: Chart 1 and Chart 2 side by side
    html.Div([
        # Chart 1: Time Series (Editable)
        html.Div([
            html.Div([
                html.H4("Trend Analysis", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("X-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart1-x',
                                 options=[{'label': c, 'value': c} for c in TEMPORAL_COLS],
                                 value='YEAR', clearable=False,
                                 style={'width': '140px', 'display': 'inline-block', 'marginRight': '15px'}),
                    html.Label("Y-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart1-y',
                                 options=[{'label': 'Count', 'value': 'count'}] +
                                         [{'label': c, 'value': c} for c in NUMERIC_COLS],
                                 value='count', clearable=False,
                                 style={'width': '240px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='chart1', style={'marginTop': '0'}),
            html.Div(id='insight1', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        # Chart 2: Severity Pie (Not Editable)
        html.Div([
            html.Div([
                html.H4("Severity Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='severity-pie', style={'marginTop': '0'}),
            html.Div(id='insight2', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 2: Chart 3 and Chart 4 side by side
    html.Div([
        # Chart 3: Categorical Bar (Editable)
        html.Div([
            html.Div([
                html.H4("Categorical Analysis", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("Category:", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                    dcc.Dropdown(id='chart3-x',
                                 options=[{'label': c, 'value': c} for c in CATEGORICAL_COLS],
                                 value='BOROUGH', clearable=False,
                                 style={'width': '120px', 'display': 'inline-block', 'marginRight': '10px'}),
                    html.Label("Y-axis:", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                    dcc.Dropdown(id='chart3-y',
                                 options=[{'label': 'Count', 'value': 'count'}] +
                                         [{'label': c, 'value': c} for c in NUMERIC_COLS],
                                 value='count', clearable=False,
                                 style={'width': '240px', 'display': 'inline-block', 'marginRight': '10px'}),
                    html.Label("Top:", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                    dcc.Input(id='chart3-top', type='number', value=10, min=5, max=20,
                              style={'width': '55px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='chart3', style={'marginTop': '0'}),
            html.Div(id='insight3', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        # Chart 4: Time Distribution (Editable)
        html.Div([
            html.Div([
                html.H4("Time Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("X-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart4-x',
                                 options=[{'label': c, 'value': c} for c in TEMPORAL_COLS],
                                 value='HOUR', clearable=False,
                                 style={'width': '140px', 'display': 'inline-block', 'marginRight': '15px'}),
                    html.Label("Y-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart4-y',
                                 options=[{'label': 'Count', 'value': 'count'}] +
                                         [{'label': c, 'value': c} for c in NUMERIC_COLS],
                                 value='count', clearable=False,
                                 style={'width': '240px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='chart4', style={'marginTop': '0'}),
            html.Div(id='insight4', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 3: Chart 5 (Heatmap) - Full Width
    html.Div([
        html.Div([
            html.H4("Day × Hour Heatmap", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='heatmap', style={'marginTop': '0'}),
        html.Div(id='insight5', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                       'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

    # Row 4: Chart 6 (Map) - Full Width
    html.Div([
        html.Div([
            html.H4("Geographic Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='map-scatter', style={'marginTop': '0'}),
        html.Div(id='insight6', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                       'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})

], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff',
          'maxWidth': '1400px', 'margin': '0 auto', 'padding': '20px'})


@app.callback(
    [Output('summary-stats', 'children'),
     Output('chart1', 'figure'), Output('insight1', 'children'),
     Output('severity-pie', 'figure'), Output('insight2', 'children'),
     Output('chart3', 'figure'), Output('insight3', 'children'),
     Output('chart4', 'figure'), Output('insight4', 'children'),
     Output('heatmap', 'figure'), Output('insight5', 'children'),
     Output('map-scatter', 'figure'), Output('insight6', 'children')],
    [Input('generate-btn', 'n_clicks')],
    [State('borough-filter', 'value'), State('year-filter', 'value'),
     State('vehicle-filter', 'value'), State('severity-filter', 'value'),
     State('timeofday-filter', 'value'),
     State('chart1-x', 'value'), State('chart1-y', 'value'),
     State('chart3-x', 'value'), State('chart3-y', 'value'), State('chart3-top', 'value'),
     State('chart4-x', 'value'), State('chart4-y', 'value')]
)
def update_dashboard(n_clicks, borough, year, vehicle, severity, timeofday,
                     c1_x, c1_y, c3_x, c3_y, c3_top, c4_x, c4_y):
    # Filter data
    filtered_df = df.copy()
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

    if len(filtered_df) == 0:
        empty_msg = html.Div([
            html.H3("⚠️ No Data Found", style={'color': '#e74c3c', 'textAlign': 'center'}),
            html.P("Adjust your filters.", style={'textAlign': 'center', 'color': '#7f8c8d'})
        ])
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data", xref="paper", yref="paper",
                                 x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))
        return (empty_msg, empty_fig, "", empty_fig, "", empty_fig, "",
                empty_fig, "", empty_fig, "", empty_fig, "")

    # Summary Statistics (6 stats now!)
    total_crashes = len(filtered_df)
    total_injuries = filtered_df['NUMBER OF PERSONS INJURED'].sum()
    total_fatalities = filtered_df['NUMBER OF PERSONS KILLED'].sum()
    ped_crashes = filtered_df['PEDESTRIAN_INVOLVED'].sum()
    cyclist_crashes = filtered_df['CYCLIST_INVOLVED'].sum()
    avg_vehicles = filtered_df[[c for c in df.columns if 'VEHICLE TYPE CODE' in c]].notna().sum(axis=1).mean()

    summary = html.Div([
        html.H3("📊 Summary Statistics", style={'color': '#2c3e50'}),
        html.Div([
            html.Div([
                html.H2(f"{total_crashes:,}", style={'color': '#3498db', 'margin': '0'}),
                html.P("Total Crashes", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(total_injuries):,}", style={'color': '#f39c12', 'margin': '0'}),
                html.P("Injuries", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(total_fatalities):,}", style={'color': '#e74c3c', 'margin': '0'}),
                html.P("Fatalities", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(ped_crashes):,}", style={'color': '#9b59b6', 'margin': '0'}),
                html.P("Pedestrian Involved", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(cyclist_crashes):,}", style={'color': '#16a085', 'margin': '0'}),
                html.P("Cyclist Involved", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{avg_vehicles:.1f}", style={'color': '#34495e', 'margin': '0'}),
                html.P("Avg Vehicles/Crash", style={'margin': '0'})
            ], style={'width': '13.5%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'})
        ])
    ])

    # Chart 1: Time Series
    if c1_y == 'count':
        chart1_data = filtered_df.groupby(c1_x).size().reset_index(name='count')
        y_label = 'Number of Crashes'
    else:
        chart1_data = filtered_df.groupby(c1_x)[c1_y].sum().reset_index()
        y_label = c1_y

    fig1 = px.line(chart1_data, x=c1_x, y=chart1_data.columns[1],
                   labels={chart1_data.columns[1]: y_label, c1_x: c1_x})
    fig1.update_traces(line_color='#3498db', line_width=3)
    fig1.update_layout(template='plotly_white', height=400)

    max_val = chart1_data[chart1_data.columns[1]].max()
    min_val = chart1_data[chart1_data.columns[1]].min()
    max_cat = chart1_data.loc[chart1_data[chart1_data.columns[1]].idxmax(), c1_x]
    min_cat = chart1_data.loc[chart1_data[chart1_data.columns[1]].idxmin(), c1_x]
    insight1 = html.Div([
        html.Strong("📈 Insight: "),
        f"Peak at {max_cat} ({max_val:,.0f}), lowest at {min_cat} ({min_val:,.0f})"
    ])

    # Chart 2: Severity Pie
    severity_data = filtered_df['CRASH_SEVERITY'].value_counts()
    fig2 = px.pie(values=severity_data.values, names=severity_data.index,
                  color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c'])
    fig2.update_layout(template='plotly_white', height=400)

    most_common = severity_data.idxmax()
    pct = (severity_data.max() / severity_data.sum() * 100)
    insight2 = html.Div([
        html.Strong("🥧 Insight: "),
        f"Most common severity: {most_common} ({pct:.1f}% of crashes)"
    ])

    # Chart 3: Categorical Bar
    if c3_y == 'count':
        chart3_data = filtered_df[c3_x].value_counts().head(c3_top)
        y_label = 'Number of Crashes'
    else:
        chart3_data = filtered_df.groupby(c3_x)[c3_y].sum().sort_values(ascending=False).head(c3_top)
        y_label = c3_y

    fig3 = px.bar(x=chart3_data.index, y=chart3_data.values,
                  labels={'x': c3_x, 'y': y_label})
    fig3.update_traces(marker_color='#3498db')
    fig3.update_layout(template='plotly_white', height=400)

    max_cat3 = chart3_data.idxmax()
    min_cat3 = chart3_data.idxmin()
    insight3 = html.Div([
        html.Strong("📊 Insight: "),
        f"Highest: {max_cat3} ({chart3_data.max():,.0f}), Lowest: {min_cat3} ({chart3_data.min():,.0f})"
    ])

    # Chart 4: Time Distribution
    if c4_y == 'count':
        chart4_data = filtered_df[c4_x].value_counts().sort_index()
        y_label = 'Number of Crashes'
    else:
        chart4_data = filtered_df.groupby(c4_x)[c4_y].sum().sort_index()
        y_label = c4_y

    fig4 = px.bar(x=chart4_data.index, y=chart4_data.values,
                  labels={'x': c4_x, 'y': y_label})
    fig4.update_traces(marker_color='#e67e22')
    fig4.update_layout(template='plotly_white', height=400)

    max_cat4 = chart4_data.idxmax()
    min_cat4 = chart4_data.idxmin()
    insight4 = html.Div([
        html.Strong("⏰ Insight: "),
        f"Peak time: {max_cat4} ({chart4_data.max():,.0f}), Quietest: {min_cat4} ({chart4_data.min():,.0f})"
    ])

    # Chart 5: Heatmap
    heatmap_data = filtered_df.groupby(['DAY_OF_WEEK_NUM', 'HOUR']).size().reset_index(name='count')
    if len(heatmap_data) > 0:
        heatmap_pivot = heatmap_data.pivot(index='DAY_OF_WEEK_NUM', columns='HOUR', values='count')
        fig5 = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            colorscale='YlOrRd'
        ))
        fig5.update_layout(xaxis_title='Hour of Day', yaxis_title='Day of Week',
                           template='plotly_white', height=500)

        max_day = heatmap_pivot.sum(axis=1).idxmax()
        max_hour = heatmap_pivot.sum(axis=0).idxmax()
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        insight5 = html.Div([
            html.Strong("🗓️ Insight: "),
            f"Busiest day: {day_names[max_day]}, Busiest hour: {max_hour}:00"
        ])
    else:
        fig5 = go.Figure()
        insight5 = ""

    # Chart 6: Map
    map_sample = filtered_df[filtered_df['LATITUDE'].notna()]
    if len(map_sample) > 0:
        map_sample = map_sample.sample(n=min(5000, len(map_sample)), random_state=42)
        fig6 = px.scatter_map(
            map_sample, lat='LATITUDE', lon='LONGITUDE', color='CRASH_SEVERITY',
            color_discrete_map={'Fatal': '#e74c3c', 'Injury': '#f39c12',
                                'Property Damage Only': '#2ecc71'},
            title=f'Crash Locations (Sample of {len(map_sample):,})',
            zoom=10, height=600
        )
        fig6.update_layout(map_style="open-street-map")

        fatal_pct = (map_sample['CRASH_SEVERITY'] == 'Fatal').sum() / len(map_sample) * 100
        insight6 = html.Div([
            html.Strong("🗺️ Insight: "),
            f"Showing {len(map_sample):,} locations, {fatal_pct:.1f}% are fatal crashes"
        ])
    else:
        fig6 = go.Figure()
        insight6 = ""

    return (summary, fig1, insight1, fig2, insight2, fig3, insight3,
            fig4, insight4, fig5, insight5, fig6, insight6)


if __name__ == '__main__':
    app.run(debug=False, port=8050)