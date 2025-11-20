import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Load data
print("Loading data...")
df = pd.read_parquet('nyc_crashes_integrated_clean.parquet')
df['CRASH DATE'] = pd.to_datetime(df['CRASH DATE'])
print(f"Data loaded: {len(df):,} records")

# Initialize app
app = dash.Dash(__name__)
server = app.server

# Define smart column choices for each graph type
TEMPORAL_COLS = ['CRASH_YEAR', 'CRASH_MONTH', 'CRASH_DAYOFWEEK', 'CRASH_HOUR']
CATEGORICAL_COLS = ['BOROUGH', 'PERSON_TYPE', 'PERSON_INJURY',
                    'CONTRIBUTING FACTOR VEHICLE 1', 'VEHICLE TYPE CODE 1',
                    'PERSON_SEX', 'SAFETY_EQUIPMENT', 'POSITION_IN_VEHICLE']
NUMERIC_COLS = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'NUMBER OF PEDESTRIANS INJURED', 'NUMBER OF PEDESTRIANS KILLED',
                'NUMBER OF CYCLIST INJURED', 'NUMBER OF CYCLIST KILLED',
                'NUMBER OF MOTORIST INJURED', 'NUMBER OF MOTORIST KILLED']

# Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("NYC Motor Vehicle Crashes Dashboard - Advanced Analytics",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
        html.P("Comprehensive trend analysis and research insights",
               style={'textAlign': 'center', 'color': '#7f8c8d'})
    ], style={'padding': '20px', 'backgroundColor': '#ecf0f1'}),

    # Enhanced Filter Panel with MORE filters
    html.Div([
        html.H3("🔍 Filters", style={'color': '#2c3e50'}),

        # Row 1: Basic Filters
        html.Div([
            html.Div([
                html.Label("Borough:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='borough-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': b, 'value': b} for b in sorted(df['BOROUGH'].dropna().unique()) if str(b) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Year Range:", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id='year-range-filter',
                    min=int(df['CRASH_YEAR'].min()),
                    max=int(df['CRASH_YEAR'].max()),
                    value=[int(df['CRASH_YEAR'].min()), int(df['CRASH_YEAR'].max())],
                    marks={int(year): str(int(year)) for year in df['CRASH_YEAR'].unique()},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%', 'paddingTop': '10px'}),

            html.Div([
                html.Label("Month Range:", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id='month-range-filter',
                    min=1, max=12,
                    value=[1, 12],
                    marks={i: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i-1] for i in range(1, 13)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'paddingTop': '10px'})
        ]),

        # Row 2: Person & Vehicle Filters
        html.Div([
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
                html.Label("Vehicle Type:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='vehicle-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': v, 'value': v} for v in sorted(df['VEHICLE TYPE CODE 1'].dropna().unique()) if str(v) != 'nan'][:50],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Person Sex:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='sex-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': s, 'value': s} for s in sorted(df['PERSON_SEX'].dropna().unique()) if str(s) != 'nan'],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Safety Equipment:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='safety-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': s, 'value': s} for s in sorted(df['SAFETY_EQUIPMENT'].dropna().unique()) if str(s) != 'nan'][:20],
                             value='All', clearable=False)
            ], style={'width': '18%', 'display': 'inline-block'})
        ], style={'marginTop': '15px'}),

        # Row 3: Time & Contributing Factor Filters
        html.Div([
            html.Div([
                html.Label("Hour Range:", style={'fontWeight': 'bold'}),
                dcc.RangeSlider(
                    id='hour-range-filter',
                    min=0, max=23,
                    value=[0, 23],
                    marks={i: f"{i}:00" if i % 3 == 0 else '' for i in range(0, 24)},
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%', 'paddingTop': '10px'}),

            html.Div([
                html.Label("Day of Week:", style={'fontWeight': 'bold'}),
                dcc.Checklist(
                    id='day-filter',
                    options=[
                        {'label': 'Mon', 'value': 0}, {'label': 'Tue', 'value': 1},
                        {'label': 'Wed', 'value': 2}, {'label': 'Thu', 'value': 3},
                        {'label': 'Fri', 'value': 4}, {'label': 'Sat', 'value': 5},
                        {'label': 'Sun', 'value': 6}
                    ],
                    value=[0,1,2,3,4,5,6],
                    inline=True,
                    style={'marginTop': '5px'}
                )
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.Label("Contributing Factor:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(id='factor-filter',
                             options=[{'label': 'All', 'value': 'All'}] +
                                     [{'label': f, 'value': f} for f in sorted(df['CONTRIBUTING FACTOR VEHICLE 1'].dropna().unique()) if str(f) != 'nan'][:30],
                             value='All', clearable=False)
            ], style={'width': '30%', 'display': 'inline-block'})
        ], style={'marginTop': '15px'}),

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

    # Row 1: Trend Analysis Charts
    html.Div([
        html.Div([
            html.Div([
                html.H4("Yearly Trend Analysis", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("Metric:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Dropdown(id='trend-metric',
                                 options=[{'label': 'Count', 'value': 'count'}] +
                                         [{'label': c, 'value': c} for c in NUMERIC_COLS],
                                 value='count', clearable=False,
                                 style={'width': '240px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='trend-chart', style={'marginTop': '0'}),
            html.Div(id='trend-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.H4("Person Type Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='person-pie', style={'marginTop': '0'}),
            html.Div(id='person-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                 'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 2: Comparative Analysis
    html.Div([
        html.Div([
            html.Div([
                html.H4("Top Contributing Factors", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'}),
                html.Div([
                    html.Label("Show Top:", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                    dcc.Input(id='top-factors', type='number', value=15, min=5, max=30,
                              style={'width': '50px', 'display': 'inline-block'})
                ], style={'padding': '0 12px 12px 12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='factors-chart', style={'marginTop': '0'}),
            html.Div(id='factors-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                  'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.H4("Injury Rate by Borough", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='borough-comparison', style={'marginTop': '0'}),
            html.Div(id='borough-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                  'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 3: Time-based Analysis
    html.Div([
        html.Div([
            html.Div([
                html.H4("Hourly Distribution by Day Type", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='hourly-comparison', style={'marginTop': '0'}),
            html.Div(id='hourly-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                 'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'marginRight': '2%', 'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.H4("Monthly Seasonality Pattern", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
            ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
            dcc.Graph(id='monthly-pattern', style={'marginTop': '0'}),
            html.Div(id='monthly-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                                  'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top',
                  'backgroundColor': '#fff', 'borderRadius': '5px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})
    ]),

    # Row 4: Heatmap
    html.Div([
        html.Div([
            html.H4("Day × Hour Heatmap", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='heatmap', style={'marginTop': '0'}),
        html.Div(id='heatmap-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                              'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),

    # Row 5: Map
    html.Div([
        html.Div([
            html.H4("Geographic Distribution", style={'color': '#2c3e50', 'margin': '0', 'padding': '12px'})
        ], style={'backgroundColor': '#f8f9fa', 'marginBottom': '0', 'borderRadius': '5px 5px 0 0'}),
        dcc.Graph(id='map-scatter', style={'marginTop': '0'}),
        html.Div(id='map-insight', style={'padding': '10px 12px', 'backgroundColor': '#e8f5e9',
                                          'borderLeft': '4px solid #4caf50', 'borderRadius': '0 0 5px 5px'})
    ], style={'backgroundColor': '#fff', 'borderRadius': '5px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'})

], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff',
          'maxWidth': '1600px', 'margin': '0 auto', 'padding': '20px'})


@app.callback(
    [Output('summary-stats', 'children'),
     Output('trend-chart', 'figure'), Output('trend-insight', 'children'),
     Output('person-pie', 'figure'), Output('person-insight', 'children'),
     Output('factors-chart', 'figure'), Output('factors-insight', 'children'),
     Output('borough-comparison', 'figure'), Output('borough-insight', 'children'),
     Output('hourly-comparison', 'figure'), Output('hourly-insight', 'children'),
     Output('monthly-pattern', 'figure'), Output('monthly-insight', 'children'),
     Output('heatmap', 'figure'), Output('heatmap-insight', 'children'),
     Output('map-scatter', 'figure'), Output('map-insight', 'children')],
    [Input('generate-btn', 'n_clicks')],
    [State('borough-filter', 'value'), State('year-range-filter', 'value'),
     State('month-range-filter', 'value'), State('hour-range-filter', 'value'),
     State('day-filter', 'value'), State('person-type-filter', 'value'),
     State('injury-filter', 'value'), State('vehicle-filter', 'value'),
     State('sex-filter', 'value'), State('safety-filter', 'value'),
     State('factor-filter', 'value'), State('trend-metric', 'value'),
     State('top-factors', 'value')]
)
def update_dashboard(n_clicks, borough, year_range, month_range, hour_range, days,
                     person_type, person_injury, vehicle, sex, safety, factor,
                     trend_metric, top_factors):

    # Filter data
    filtered_df = df.copy()

    if borough != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == borough]

    filtered_df = filtered_df[
        (filtered_df['CRASH_YEAR'] >= year_range[0]) &
        (filtered_df['CRASH_YEAR'] <= year_range[1])
        ]

    filtered_df = filtered_df[
        (filtered_df['CRASH_MONTH'] >= month_range[0]) &
        (filtered_df['CRASH_MONTH'] <= month_range[1])
        ]

    filtered_df = filtered_df[
        (filtered_df['CRASH_HOUR'] >= hour_range[0]) &
        (filtered_df['CRASH_HOUR'] <= hour_range[1])
        ]

    filtered_df = filtered_df[filtered_df['CRASH_DAYOFWEEK'].isin(days)]

    if person_type != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_TYPE'] == person_type]
    if person_injury != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_INJURY'] == person_injury]
    if vehicle != 'All':
        filtered_df = filtered_df[filtered_df['VEHICLE TYPE CODE 1'] == vehicle]
    if sex != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_SEX'] == sex]
    if safety != 'All':
        filtered_df = filtered_df[filtered_df['SAFETY_EQUIPMENT'] == safety]
    if factor != 'All':
        filtered_df = filtered_df[filtered_df['CONTRIBUTING FACTOR VEHICLE 1'] == factor]

    if len(filtered_df) == 0:
        empty_msg = html.Div([
            html.H3("⚠️ No Data Found", style={'color': '#e74c3c', 'textAlign': 'center'}),
            html.P("Adjust your filters.", style={'textAlign': 'center', 'color': '#7f8c8d'})
        ])
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data", xref="paper", yref="paper",
                                 x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))
        return (empty_msg, empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, "",
                empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, "")

    # Summary Statistics
    total_records = len(filtered_df)
    total_injuries = filtered_df['NUMBER OF PERSONS INJURED'].sum()
    total_fatalities = filtered_df['NUMBER OF PERSONS KILLED'].sum()
    ped_injuries = filtered_df['NUMBER OF PEDESTRIANS INJURED'].sum()
    cyclist_injuries = filtered_df['NUMBER OF CYCLIST INJURED'].sum()
    motorist_injuries = filtered_df['NUMBER OF MOTORIST INJURED'].sum()

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
                html.P("Total Injuries", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{int(total_fatalities):,}", style={'color': '#e74c3c', 'margin': '0'}),
                html.P("Total Fatalities", style={'margin': '0'})
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
                html.H2(f"{injury_rate:.1f}%", style={'color': '#e67e22', 'margin': '0'}),
                html.P("Injury Rate", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'}),

            html.Div([
                html.H2(f"{fatality_rate:.2f}%", style={'color': '#c0392b', 'margin': '0'}),
                html.P("Fatality Rate", style={'margin': '0'})
            ], style={'width': '11%', 'display': 'inline-block', 'textAlign': 'center',
                      'padding': '15px', 'backgroundColor': '#ecf0f1', 'margin': '0.5%'})
        ])
    ])

    # Chart 1: Yearly Trend
    if trend_metric == 'count':
        trend_data = filtered_df.groupby('CRASH_YEAR').size().reset_index(name='value')
        y_label = 'Number of Records'
    else:
        trend_data = filtered_df.groupby('CRASH_YEAR')[trend_metric].sum().reset_index(name='value')
        y_label = trend_metric

    fig1 = px.line(trend_data, x='CRASH_YEAR', y='value',
                   labels={'value': y_label, 'CRASH_YEAR': 'Year'},
                   markers=True)
    fig1.update_traces(line_color='#3498db', line_width=3, marker=dict(size=8))
    fig1.update_layout(template='plotly_white', height=400)

    if len(trend_data) > 1:
        pct_change = ((trend_data['value'].iloc[-1] - trend_data['value'].iloc[0]) / trend_data['value'].iloc[0] * 100)
        trend_direction = "📈 increased" if pct_change > 0 else "📉 decreased"
        insight1 = html.Div([
            html.Strong("Trend: "),
            f"{y_label} {trend_direction} by {abs(pct_change):.1f}% from {int(trend_data['CRASH_YEAR'].iloc[0])} to {int(trend_data['CRASH_YEAR'].iloc[-1])}"
        ])
    else:
        insight1 = ""

    # Chart 2: Person Type Pie
    person_data = filtered_df['PERSON_TYPE'].value_counts()
    fig2 = px.pie(values=person_data.values, names=person_data.index,
                  color_discrete_sequence=px.colors.qualitative.Set3)
    fig2.update_layout(template='plotly_white', height=400)

    most_common = person_data.idxmax()
    pct = (person_data.max() / person_data.sum() * 100)
    insight2 = html.Div([
        html.Strong("🥧 Distribution: "),
        f"{most_common} accounts for {pct:.1f}% of all records"
    ])

    # Chart 3: Top Contributing Factors
    factors_data = filtered_df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(top_factors)
    fig3 = px.bar(x=factors_data.values, y=factors_data.index, orientation='h',
                  labels={'x': 'Count', 'y': 'Contributing Factor'})
    fig3.update_traces(marker_color='#e74c3c')
    fig3.update_layout(template='plotly_white', height=400, yaxis={'categoryorder':'total ascending'})

    top_factor = factors_data.idxmax()
    insight3 = html.Div([
        html.Strong("⚠️ Top Factor: "),
        f"{top_factor} ({factors_data.max():,} incidents, {factors_data.max()/len(filtered_df)*100:.1f}%)"
    ])

    # Chart 4: Borough Comparison (Injury Rate)
    borough_stats = filtered_df.groupby('BOROUGH').agg({
        'NUMBER OF PERSONS INJURED': 'sum',
        'BOROUGH': 'count'
    }).rename(columns={'BOROUGH': 'count'})
    borough_stats['injury_rate'] = (borough_stats['NUMBER OF PERSONS INJURED'] / borough_stats['count'] * 100)
    borough_stats = borough_stats.sort_values('injury_rate', ascending=False)

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=borough_stats.index,
        y=borough_stats['injury_rate'],
        name='Injury Rate (%)',
        marker_color='#f39c12'
    ))
    fig4.update_layout(
        template='plotly_white',
        height=400,
        yaxis_title='Injury Rate (%)',
        xaxis_title='Borough'
    )

    highest_borough = borough_stats['injury_rate'].idxmax()
    lowest_borough = borough_stats['injury_rate'].idxmin()
    insight4 = html.Div([
        html.Strong("🏙️ Borough Analysis: "),
        f"Highest injury rate: {highest_borough} ({borough_stats.loc[highest_borough, 'injury_rate']:.1f}%), "
        f"Lowest: {lowest_borough} ({borough_stats.loc[lowest_borough, 'injury_rate']:.1f}%)"
    ])

    # Chart 5: Hourly Distribution (Weekday vs Weekend)
    filtered_df['is_weekend'] = filtered_df['CRASH_DAYOFWEEK'].isin([5, 6])
    hourly_weekday = filtered_df[~filtered_df['is_weekend']].groupby('CRASH_HOUR').size()
    hourly_weekend = filtered_df[filtered_df['is_weekend']].groupby('CRASH_HOUR').size()

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=hourly_weekday.index, y=hourly_weekday.values,
                              mode='lines+markers', name='Weekday',
                              line=dict(color='#3498db', width=3)))
    fig5.add_trace(go.Scatter(x=hourly_weekend.index, y=hourly_weekend.values,
                              mode='lines+markers', name='Weekend',
                              line=dict(color='#e74c3c', width=3)))
    fig5.update_layout(
        template='plotly_white',
        height=400,
        xaxis_title='Hour of Day',
        yaxis_title='Number of Records'
    )

    weekday_peak = hourly_weekday.idxmax()
    weekend_peak = hourly_weekend.idxmax()
    insight5 = html.Div([
        html.Strong("⏰ Peak Hours: "),
        f"Weekday: {weekday_peak}:00 ({hourly_weekday.max():,}), "
        f"Weekend: {weekend_peak}:00 ({hourly_weekend.max():,})"
    ])

    # Chart 6: Monthly Seasonality
    monthly_data = filtered_df.groupby('CRASH_MONTH').size()
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    fig6 = px.bar(x=[month_names[i-1] for i in monthly_data.index], y=monthly_data.values,
                  labels={'x': 'Month', 'y': 'Number of Records'})
    fig6.update_traces(marker_color='#16a085')
    fig6.update_layout(template='plotly_white', height=400)

    peak_month = month_names[monthly_data.idxmax()-1]
    low_month = month_names[monthly_data.idxmin()-1]
    insight6 = html.Div([
        html.Strong("📅 Seasonality: "),
        f"Peak month: {peak_month} ({monthly_data.max():,}), "
        f"Lowest: {low_month} ({monthly_data.min():,})"
    ])

    # Chart 7: Heatmap
    heatmap_data = filtered_df.groupby(['CRASH_DAYOFWEEK', 'CRASH_HOUR']).size().reset_index(name='count')
    if len(heatmap_data) > 0:
        heatmap_pivot = heatmap_data.pivot(index='CRASH_DAYOFWEEK', columns='CRASH_HOUR', values='count')
        fig7 = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            colorscale='YlOrRd',
            colorbar=dict(title="Count")
        ))
        fig7.update_layout(
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            template='plotly_white',
            height=500
        )

        max_day_idx = heatmap_pivot.sum(axis=1).idxmax()
        max_hour = heatmap_pivot.sum(axis=0).idxmax()
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        insight7 = html.Div([
            html.Strong("🗓️ Hotspot: "),
            f"Busiest combination: {day_names[max_day_idx]} at {max_hour}:00"
        ])
    else:
        fig7 = go.Figure()
        insight7 = ""

    # Chart 8: Map
    map_sample = filtered_df[(filtered_df['LATITUDE'].notna()) &
                             (filtered_df['LATITUDE'] != 0) &
                             (filtered_df['LATITUDE'] > 40) &
                             (filtered_df['LATITUDE'] < 41)]

    if len(map_sample) > 0:
        sample_size = min(5000, len(map_sample))
        map_sample = map_sample.sample(n=sample_size, random_state=42)

        map_sample['COLOR_LABEL'] = map_sample['PERSON_INJURY'].fillna('Unknown')

        fig8 = px.scatter_map(
            map_sample,
            lat='LATITUDE',
            lon='LONGITUDE',
            color='COLOR_LABEL',
            title=f'Crash Locations (Sample of {sample_size:,} from {len(filtered_df):,} records)',
            zoom=10,
            height=600
        )
        fig8.update_layout(map_style="open-street-map")

        injury_types = map_sample['PERSON_INJURY'].value_counts()
        top_injury = injury_types.idxmax() if len(injury_types) > 0 else "N/A"
        insight8 = html.Div([
            html.Strong("🗺️ Geographic Pattern: "),
            f"Displaying {sample_size:,} locations. Most common injury: {top_injury} ({injury_types.max():,} cases)"
        ])
    else:
        fig8 = go.Figure()
        fig8.add_annotation(
            text="No location data available with current filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig8.update_layout(height=600)
        insight8 = html.Div([
            html.Strong("⚠️ Note: "),
            "No geographic data available for current filter selection"
        ])

    return (summary, fig1, insight1, fig2, insight2, fig3, insight3, fig4, insight4,
            fig5, insight5, fig6, insight6, fig7, insight7, fig8, insight8)


# Reset filters callback
@app.callback(
    [Output('borough-filter', 'value'),
     Output('year-range-filter', 'value'),
     Output('month-range-filter', 'value'),
     Output('hour-range-filter', 'value'),
     Output('day-filter', 'value'),
     Output('person-type-filter', 'value'),
     Output('injury-filter', 'value'),
     Output('vehicle-filter', 'value'),
     Output('sex-filter', 'value'),
     Output('safety-filter', 'value'),
     Output('factor-filter', 'value')],
    [Input('reset-btn', 'n_clicks')]
)
def reset_filters(n_clicks):
    if n_clicks > 0:
        return ('All',
                [int(df['CRASH_YEAR'].min()), int(df['CRASH_YEAR'].max())],
                [1, 12],
                [0, 23],
                [0,1,2,3,4,5,6],
                'All', 'All', 'All', 'All', 'All', 'All')
    return dash.no_update


if __name__ == '__main__':

    app.run(debug=False, host='0.0.0.0', port=8080)
