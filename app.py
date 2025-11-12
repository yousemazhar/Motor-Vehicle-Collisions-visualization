# Save this as: app.py (PUSH 1)

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
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

    # Simple Filter Panel
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
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),

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
            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '3%'}),

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
            ], style={'width': '30%', 'display': 'inline-block'})
        ]),

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

    # Basic Visualizations (3 charts)
    html.Div([
        html.Div([
            dcc.Graph(id='crashes-over-time')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='severity-pie')
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),

    html.Div([
        dcc.Graph(id='borough-bar')
    ])

], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#ffffff'})


# Callback for updating charts
@app.callback(
    [Output('summary-stats', 'children'),
     Output('crashes-over-time', 'figure'),
     Output('severity-pie', 'figure'),
     Output('borough-bar', 'figure')],
    [Input('generate-btn', 'n_clicks')],
    [State('borough-filter', 'value'),
     State('year-filter', 'value'),
     State('severity-filter', 'value')]
)
def update_dashboard(n_clicks, borough, year, severity):
    # Start with full dataset
    filtered_df = df.copy()

    # Apply filters
    if borough != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == borough]
    if year != 'All':
        filtered_df = filtered_df[filtered_df['YEAR'] == year]
    if severity != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_SEVERITY'] == severity]

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

    return summary, fig1, fig2, fig3


if __name__ == '__main__':
    app.run(debug=True, port=8050)