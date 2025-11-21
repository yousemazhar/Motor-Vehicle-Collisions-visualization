import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Load data
print("Loading data...")
df = pd.read_parquet('nyc_crashes_integrated_clean.parquet')
df['CRASH DATE'] = pd.to_datetime(df['CRASH DATE'])
print(f"Data loaded: {len(df):,} records")

# Clean vehicle types - whitelist of valid categories
VALID_VEHICLE_TYPES = [
    'SEDAN', 'STATION WAGON/SPORT UTILITY VEHICLE', 'TAXI', 'PICK-UP TRUCK',
    'BOX TRUCK', 'VAN', 'MOTORCYCLE', 'SCOOTER', 'MOPED', 'E-SCOOTER', 'E-BIKE',
    'BICYCLE', 'BUS', 'AMBULANCE', 'FIRE TRUCK', 'TRACTOR TRUCK DIESEL',
    'TRACTOR TRUCK GASOLINE', 'DUMP', 'FLAT BED', 'GARBAGE OR REFUSE',
    'CONCRETE MIXER', 'REFRIGERATED VAN', 'TRUCK', 'LIVERY VEHICLE',
    'PASSENGER VEHICLE', '2 DR SEDAN', '4 DR SEDAN', 'CONVERTIBLE',
    'SPORT UTILITY / STATION WAGON', 'LIMOUSINE', 'UNKNOWN'
]

# Replace invalid vehicle types with 'OTHER'
df['VEHICLE TYPE CODE 1'] = df['VEHICLE TYPE CODE 1'].apply(
    lambda x: x if x in VALID_VEHICLE_TYPES else 'OTHER'
)
df['VEHICLE TYPE CODE 2'] = df['VEHICLE TYPE CODE 2'].apply(
    lambda x: x if x in VALID_VEHICLE_TYPES or x == 'NO SECOND VEHICLE' else 'OTHER'
)

print(f"Cleaned vehicle types. Valid categories: {len(df['VEHICLE TYPE CODE 1'].unique())}")

# Initialize app
app = dash.Dash(__name__)
server = app.server

# Define smart column choices for each graph type
TEMPORAL_COLS = ['CRASH_YEAR', 'CRASH_MONTH', 'CRASH_DAYOFWEEK', 'CRASH_HOUR']
CATEGORICAL_COLS = ['BOROUGH', 'PERSON_TYPE', 'PERSON_INJURY',
                    'CONTRIBUTING FACTOR VEHICLE 1', 'VEHICLE TYPE CODE 1',
                    'PERSON_SEX', 'SAFETY_EQUIPMENT', 'POSITION_IN_VEHICLE',
                    'EJECTION', 'EMOTIONAL_STATUS']
NUMERIC_COLS = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'NUMBER OF PEDESTRIANS INJURED', 'NUMBER OF PEDESTRIANS KILLED',
                'NUMBER OF CYCLIST INJURED', 'NUMBER OF CYCLIST KILLED',
                'NUMBER OF MOTORIST INJURED', 'NUMBER OF MOTORIST KILLED']

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("NYC Motor Vehicle Crashes Dashboard - Enhanced Analytics",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Comprehensive analysis with 5.7M+ crash records",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

    # Filter Panel - Row 1
    html.Div([
        html.H3("Filters", style={'color': '#2c3e50', 'marginBottom': '15px'}),

        # First row of filters
        html.Div([
            html.Div([
                html.Label("Borough:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='borough-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': b, 'value': b} for b in sorted(df['BOROUGH'].dropna().unique()) if str(b) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '14%', 'display': 'inline-block', 'marginRight': '1.5%'}),

            html.Div([
                html.Label("Year:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='year-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': int(y), 'value': int(y)} for y in sorted(df['CRASH_YEAR'].unique())],
                             value='All', clearable=False)
            ], style={'width': '14%', 'display': 'inline-block', 'marginRight': '1.5%'}),

            html.Div([
                html.Label("Month:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='month-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': m, 'value': m} for m in sorted(df['CRASH_MONTH'].unique())],
                             value='All', clearable=False)
            ], style={'width': '14%', 'display': 'inline-block', 'marginRight': '1.5%'}),

            html.Div([
                html.Label("Day of Week:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='dow-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d], 'value': d}
                                      for d in sorted(df['CRASH_DAYOFWEEK'].unique())],
                             value='All', clearable=False)
            ], style={'width': '14%', 'display': 'inline-block', 'marginRight': '1.5%'}),

            html.Div([
                html.Label("Hour Range:", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(id='hour-filter',
                                min=0, max=23, step=1, value=[0, 23],
                                marks={0: '0', 6: '6', 12: '12', 18: '18', 23: '23'},
                                tooltip={"placement": "bottom", "always_visible": False})
            ], style={'width': '27.5%', 'display': 'inline-block', 'paddingTop': '8px'})
        ], style={'marginBottom': '15px'}),

        # Second row of filters
        html.Div([
            html.Div([
                html.Label("Vehicle Type 1:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='vehicle-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': v, 'value': v} for v in sorted(VALID_VEHICLE_TYPES + ['OTHER'])],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Person Type:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='person-type-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': s, 'value': s} for s in sorted(df['PERSON_TYPE'].dropna().unique()) if str(s) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Person Injury:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='injury-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': t, 'value': t} for t in sorted(df['PERSON_INJURY'].dropna().unique()) if str(t) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Gender:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='gender-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': {'M': 'Male', 'F': 'Female', 'U': 'Unknown'}.get(g, g), 'value': g}
                                      for g in sorted(df['PERSON_SEX'].dropna().unique()) if str(g) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Safety Equipment:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='safety-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': s, 'value': s} for s in sorted(df['SAFETY_EQUIPMENT'].dropna().unique())
                                      if str(s) not in ['nan', 'NOT APPLICABLE', 'NOT REPORTED', 'DOES NOT APPLY']][:15],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block'})
        ]),

        html.Div([
            html.Button('🔍 Generate Report', id='generate-btn', n_clicks=0,
                        style={'padding': '15px 40px', 'fontSize': '18px', 'backgroundColor': '#3498db',
                               'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer',
                               'marginTop': '20px', 'marginRight': '10px'}),
            html.Button('🔄 Reset Filters', id='reset-btn', n_clicks=0,
                        style={'padding': '15px 40px', 'fontSize': '18px', 'backgroundColor': '#95a5a6',
                               'color': 'white', 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer',
                               'marginTop': '20px'})
        ], style={'textAlign': 'center'})

    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'marginBottom': '20px'}),

    # Summary Stats
    html.Div(id='summary-stats', style={'backgroundColor': '#fff', 'marginBottom': '20px'}),

    # Row 1: Chart 1 and Chart 2 side by side
    html.Div([
        html.Div([
            html.Div([
                html.H4("Trend Analysis", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("X-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart1-x',
                                 options=[{'label': c, 'value': c} for c in TEMPORAL_COLS],
                                 value='CRASH_YEAR', clearable=False,
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

        html.Div([
            html.Div([
                html.H4("Person Type Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='chart2-pie', style={'marginTop': '0'}),
            html.Div(id='insight2', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 2: Chart 3 and Chart 4 side by side
    html.Div([
        html.Div([
            html.Div([
                html.H4("Categorical Analysis", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("Category:", style={'fontWeight': 'bold', 'marginRight': '6px'}),
                    dcc.Dropdown(id='chart3-x',
                                 options=[{'label': c, 'value': c} for c in CATEGORICAL_COLS],
                                 value='BOROUGH', clearable=False,
                                 style={'width': '200px', 'display': 'inline-block', 'marginRight': '10px'}),
                    html.Label("Y-axis:", style={'fontWeight': 'bold', 'marginRight': '6px'}),
                    dcc.Dropdown(id='chart3-y',
                                 options=[{'label': 'Count', 'value': 'count'}] +
                                         [{'label': c, 'value': c} for c in NUMERIC_COLS],
                                 value='count', clearable=False,
                                 style={'width': '220px', 'display': 'inline-block', 'marginRight': '10px'}),
                    html.Label("Top:", style={'fontWeight': 'bold', 'marginRight': '0px'}),
                    dcc.Input(id='chart3-top', type='number', value=10, min=5, max=20,
                              style={'width': '30px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='chart3', style={'marginTop': '0'}),
            html.Div(id='insight3', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                           'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.H4("Time Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("X-axis:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='chart4-x',
                                 options=[{'label': c, 'value': c} for c in TEMPORAL_COLS],
                                 value='CRASH_HOUR', clearable=False,
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

    # Row 3: New Comparison Chart
    html.Div([
        html.Div([
            html.H4("Injury Rate Comparison", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
            html.Div([
                html.Label("Compare by:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Dropdown(id='compare-category',
                             options=[{'label': 'Borough', 'value': 'BOROUGH'},
                                      {'label': 'Vehicle Type', 'value': 'VEHICLE TYPE CODE 1'},
                                      {'label': 'Person Type', 'value': 'PERSON_TYPE'},
                                      {'label': 'Safety Equipment', 'value': 'SAFETY_EQUIPMENT'},
                                      {'label': 'Hour', 'value': 'CRASH_HOUR'}],
                             value='BOROUGH', clearable=False,
                             style={'width': '200px', 'display': 'inline-block'})
            ], style={'padding': '0 12px 12px 12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='comparison-chart', style={'marginTop': '0'}),
        html.Div(id='insight-compare', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                              'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

    # Row 4: Heatmap
    html.Div([
        html.Div([
            html.H4("Day × Hour Heatmap", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='heatmap', style={'marginTop': '0'}),
        html.Div(id='insight5', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                       'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

    # Row 5: Map
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
     Output('chart2-pie', 'figure'), Output('insight2', 'children'),
     Output('chart3', 'figure'), Output('insight3', 'children'),
     Output('chart4', 'figure'), Output('insight4', 'children'),
     Output('comparison-chart', 'figure'), Output('insight-compare', 'children'),
     Output('heatmap', 'figure'), Output('insight5', 'children'),
     Output('map-scatter', 'figure'), Output('insight6', 'children')],
    [Input('generate-btn', 'n_clicks')],
    [State('borough-filter', 'value'), State('year-filter', 'value'),
     State('month-filter', 'value'), State('dow-filter', 'value'), State('hour-filter', 'value'),
     State('vehicle-filter', 'value'), State('person-type-filter', 'value'),
     State('injury-filter', 'value'), State('gender-filter', 'value'), State('safety-filter', 'value'),
     State('chart1-x', 'value'), State('chart1-y', 'value'),
     State('chart3-x', 'value'), State('chart3-y', 'value'), State('chart3-top', 'value'),
     State('chart4-x', 'value'), State('chart4-y', 'value'),
     State('compare-category', 'value')]
)
def update_dashboard(n_clicks, borough, year, month, dow, hour_range, vehicle, person_type, person_injury,
                     gender, safety, c1_x, c1_y, c3_x, c3_y, c3_top, c4_x, c4_y, compare_cat):

    # Filter data
    filtered_df = df.copy()
    if borough != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == borough]
    if year != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_YEAR'] == year]
    if month != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_MONTH'] == month]
    if dow != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_DAYOFWEEK'] == dow]
    if hour_range:
        filtered_df = filtered_df[(filtered_df['CRASH_HOUR'] >= hour_range[0]) &
                                  (filtered_df['CRASH_HOUR'] <= hour_range[1])]
    if vehicle != 'All':
        filtered_df = filtered_df[filtered_df['VEHICLE TYPE CODE 1'] == vehicle]
    if person_type != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_TYPE'] == person_type]
    if person_injury != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_INJURY'] == person_injury]
    if gender != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_SEX'] == gender]
    if safety != 'All':
        filtered_df = filtered_df[filtered_df['SAFETY_EQUIPMENT'] == safety]

    if len(filtered_df) == 0:
        empty_msg = html.Div([
            html.H3("⚠️ No Data Found", style={'color': '#e74c3c', 'textAlign': 'center'}),
            html.P("Adjust your filters.", style={'textAlign': 'center', 'color': '#7f8c8d'})
        ])
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data", xref="paper", yref="paper",
                                 x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))
        return (empty_msg, empty_fig, "", empty_fig, "", empty_fig, "",
                empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, "")

    # Summary Statistics
    total_records = len(filtered_df)
    total_injuries = filtered_df['NUMBER OF PERSONS INJURED'].sum()
    total_fatalities = filtered_df['NUMBER OF PERSONS KILLED'].sum()
    ped_injuries = filtered_df['NUMBER OF PEDESTRIANS INJURED'].sum()
    cyclist_injuries = filtered_df['NUMBER OF CYCLIST INJURED'].sum()
    motorist_injuries = filtered_df['NUMBER OF MOTORIST INJURED'].sum()

    # Calculate injury rate
    injury_rate = (total_injuries / total_records * 100) if total_records > 0 else 0
    fatality_rate = (total_fatalities / total_records * 100) if total_records > 0 else 0

    summary = html.Div([
        html.H3("📊 Summary Statistics", style={'color': '#2c3e50'}),
        html.Div([
            html.Div([
                html.H2(f"{total_records:,}", style={'color': '#3498db', 'margin': '0'}),
                html.P("Total Records", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(total_injuries):,}", style={'color': '#f39c12', 'margin': '0'}),
                html.P("Total Injuries", style={'margin': '0'}),
                html.P(f"({injury_rate:.2f}%)", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(total_fatalities):,}", style={'color': '#e74c3c', 'margin': '0'}),
                html.P("Total Fatalities", style={'margin': '0'}),
                html.P(f"({fatality_rate:.2f}%)", style={'margin': '0', 'fontSize': '12px', 'color': '#7f8c8d'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(ped_injuries):,}", style={'color': '#9b59b6', 'margin': '0'}),
                html.P("Pedestrian Injuries", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(cyclist_injuries):,}", style={'color': '#16a085', 'margin': '0'}),
                html.P("Cyclist Injuries", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(motorist_injuries):,}", style={'color': '#34495e', 'margin': '0'}),
                html.P("Motorist Injuries", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{len(filtered_df['COLLISION_ID'].unique()):,}", style={'color': '#2c3e50', 'margin': '0'}),
                html.P("Unique Crashes", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{(total_records / len(filtered_df['COLLISION_ID'].unique())):.1f}", style={'color': '#27ae60', 'margin': '0'}),
                html.P("Avg Persons/Crash", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'})
        ])
    ])

    # Chart 1: Time Series
    if c1_y == 'count':
        chart1_data = filtered_df.groupby(c1_x).size().reset_index(name='count')
        y_label = 'Number of Records'
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

    # Chart 2: Person Type Distribution
    person_type_data = filtered_df['PERSON_TYPE'].value_counts()
    fig2 = px.pie(values=person_type_data.values, names=person_type_data.index,
                  color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c', '#3498db'])
    fig2.update_layout(template='plotly_white', height=400)

    most_common = person_type_data.idxmax()
    pct = (person_type_data.max() / person_type_data.sum() * 100)
    insight2 = html.Div([
        html.Strong("🥧 Insight: "),
        f"Most common person type: {most_common} ({pct:.1f}% of records)"
    ])

    # Chart 3: Categorical Bar
    if c3_y == 'count':
        chart3_data = filtered_df[c3_x].value_counts().head(c3_top)
        y_label = 'Number of Records'
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
        y_label = 'Number of Records'
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

    # NEW: Comparison Chart - Injury Rate Analysis
    compare_data = filtered_df.groupby(compare_cat).agg({
        'COLLISION_ID': 'count',
        'NUMBER OF PERSONS INJURED': 'sum',
        'NUMBER OF PERSONS KILLED': 'sum'
    }).reset_index()
    compare_data.columns = [compare_cat, 'Total_Records', 'Total_Injuries', 'Total_Fatalities']
    compare_data['Injury_Rate'] = (compare_data['Total_Injuries'] / compare_data['Total_Records'] * 100)
    compare_data['Fatality_Rate'] = (compare_data['Total_Fatalities'] / compare_data['Total_Records'] * 100)
    compare_data = compare_data.sort_values('Injury_Rate', ascending=False).head(15)

    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        x=compare_data[compare_cat],
        y=compare_data['Injury_Rate'],
        name='Injury Rate (%)',
        marker_color='#f39c12'
    ))
    fig_compare.add_trace(go.Bar(
        x=compare_data[compare_cat],
        y=compare_data['Fatality_Rate'],
        name='Fatality Rate (%)',
        marker_color='#e74c3c'
    ))
    fig_compare.update_layout(
        barmode='group',
        template='plotly_white',
        height=400,
        xaxis_title=compare_cat,
        yaxis_title='Rate (%)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    highest_injury = compare_data.loc[compare_data['Injury_Rate'].idxmax()]
    highest_fatal = compare_data.loc[compare_data['Fatality_Rate'].idxmax()]
    insight_compare = html.Div([
        html.Strong("⚠️ Insight: "),
        f"Highest injury rate: {highest_injury[compare_cat]} ({highest_injury['Injury_Rate']:.2f}%), "
        f"Highest fatality rate: {highest_fatal[compare_cat]} ({highest_fatal['Fatality_Rate']:.2f}%)"
    ])

    # Chart 5: Heatmap
    heatmap_data = filtered_df.groupby(['CRASH_DAYOFWEEK', 'CRASH_HOUR']).size().reset_index(name='count')
    if len(heatmap_data) > 0:
        heatmap_pivot = heatmap_data.pivot(index='CRASH_DAYOFWEEK', columns='CRASH_HOUR', values='count')
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

    # Chart 6: Map (sample for performance)
    map_sample = filtered_df[(filtered_df['LATITUDE'].notna()) &
                             (filtered_df['LATITUDE'] != 0) &
                             (filtered_df['LATITUDE'] > 40) &
                             (filtered_df['LATITUDE'] < 41)]
    if len(map_sample) > 0:
        map_sample = map_sample.sample(n=min(3000, len(map_sample)), random_state=42)

        map_sample['COLOR_LABEL'] = map_sample['PERSON_INJURY'].fillna('Unknown')

        fig6 = px.scatter_map(
            map_sample, lat='LATITUDE', lon='LONGITUDE', color='COLOR_LABEL',
            title=f'Crash Locations (Sample of {len(map_sample):,})',
            zoom=10, height=600
        )
        fig6.update_layout(map_style="open-street-map")

        injury_types = map_sample['PERSON_INJURY'].value_counts()
        top_injury = injury_types.idxmax() if len(injury_types) > 0 else "N/A"
        insight6 = html.Div([
            html.Strong("🗺️ Insight: "),
            f"Showing {len(map_sample):,} locations, most common injury type: {top_injury}"
        ])
    else:
        fig6 = go.Figure()
        insight6 = ""

    return (summary, fig1, insight1, fig2, insight2, fig3, insight3,
            fig4, insight4, fig_compare, insight_compare, fig5, insight5, fig6, insight6)


# Reset button callback
@app.callback(
    [Output('borough-filter', 'value'),
     Output('year-filter', 'value'),
     Output('month-filter', 'value'),
     Output('dow-filter', 'value'),
     Output('hour-filter', 'value'),
     Output('vehicle-filter', 'value'),
     Output('person-type-filter', 'value'),
     Output('injury-filter', 'value'),
     Output('gender-filter', 'value'),
     Output('safety-filter', 'value')],
    [Input('reset-btn', 'n_clicks')]
)
def reset_filters(n_clicks):
    if n_clicks > 0:
        return 'All', 'All', 'All', 'All', [0, 23], 'All', 'All', 'All', 'All', 'All'
    return dash.no_update


if __name__ == '__main__':
    app.run(debug=False, port=8050)