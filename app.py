import gradio as gr
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import warnings
import re

# Suppress deprecation warnings to keep notebook/logs clean
warnings.filterwarnings('ignore', category=DeprecationWarning)

# -----------------------------
# Load and prepare base dataset
# -----------------------------

# Load integrated crashes + persons data from local Parquet file
print("Loading data...")
df = pd.read_parquet('nyc_crashes_integrated_clean.parquet')

# Ensure CRASH DATE is a proper datetime for any temporal analysis
df['CRASH DATE'] = pd.to_datetime(df['CRASH DATE'])
print(f"Data loaded: {len(df):,} records")

# -----------------------------------
# Clean and normalize vehicle type columns
# -----------------------------------

# Allowed/normalized vehicle type values that we consider "valid"
VALID_VEHICLE_TYPES = [
    'SEDAN', 'STATION WAGON/SPORT UTILITY VEHICLE', 'TAXI', 'PICK-UP TRUCK',
    'BOX TRUCK', 'VAN', 'MOTORCYCLE', 'SCOOTER', 'MOPED', 'E-SCOOTER', 'E-BIKE',
    'BICYCLE', 'BUS', 'AMBULANCE', 'FIRE TRUCK', 'TRACTOR TRUCK DIESEL',
    'TRACTOR TRUCK GASOLINE', 'DUMP', 'FLAT BED', 'GARBAGE OR REFUSE',
    'CONCRETE MIXER', 'REFRIGERATED VAN', 'TRUCK', 'LIVERY VEHICLE',
    'PASSENGER VEHICLE', '2 DR SEDAN', '4 DR SEDAN', 'CONVERTIBLE',
    'SPORT UTILITY / STATION WAGON', 'LIMOUSINE', 'UNKNOWN'
]

# Map any unexpected vehicle types in VEHICLE TYPE CODE 1 to 'OTHER'
df['VEHICLE TYPE CODE 1'] = df['VEHICLE TYPE CODE 1'].apply(
    lambda x: x if x in VALID_VEHICLE_TYPES else 'OTHER'
)

# For second vehicle: keep valid, or 'NO SECOND VEHICLE'; others go to 'OTHER'
df['VEHICLE TYPE CODE 2'] = df['VEHICLE TYPE CODE 2'].apply(
    lambda x: x if x in VALID_VEHICLE_TYPES or x == 'NO SECOND VEHICLE' else 'OTHER'
)

print(f"Cleaned vehicle types. Valid categories: {len(df['VEHICLE TYPE CODE 1'].unique())}")

# -----------------------------
# Column groups for dropdowns
# -----------------------------

# Temporal columns used for trend/time charts
TEMPORAL_COLS = ['CRASH_YEAR', 'CRASH_MONTH', 'CRASH_DAYOFWEEK', 'CRASH_HOUR']

# Categorical dimensions we might want to group by or filter on
CATEGORICAL_COLS = ['BOROUGH', 'PERSON_TYPE', 'PERSON_INJURY',
                    'CONTRIBUTING FACTOR VEHICLE 1', 'VEHICLE TYPE CODE 1',
                    'PERSON_SEX', 'SAFETY_EQUIPMENT', 'POSITION_IN_VEHICLE',
                    'EJECTION', 'EMOTIONAL_STATUS']

# Numeric outcome variables used for aggregations/sums
NUMERIC_COLS = ['NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
                'NUMBER OF PEDESTRIANS INJURED', 'NUMBER OF PEDESTRIANS KILLED',
                'NUMBER OF CYCLIST INJURED', 'NUMBER OF CYCLIST KILLED',
                'NUMBER OF MOTORIST INJURED', 'NUMBER OF MOTORIST KILLED']

# -----------------------------
# Pre-compute dropdown options
# -----------------------------

# Unique boroughs + "All" option
boroughs = ['All'] + sorted([b for b in df['BOROUGH'].dropna().unique() if str(b) != 'nan'])

# Unique years + "All"
years = ['All'] + sorted([int(y) for y in df['CRASH_YEAR'].unique()])

# Months 1–12 + "All"
months = ['All'] + list(range(1, 13))

# Vehicle types list + "All"
vehicles = ['All'] + sorted(VALID_VEHICLE_TYPES + ['OTHER'])

# Person types + "All"
person_types = ['All'] + sorted([p for p in df['PERSON_TYPE'].dropna().unique() if str(p) != 'nan'])

# Injury types + "All"
injury_types = ['All'] + sorted([i for i in df['PERSON_INJURY'].dropna().unique() if str(i) != 'nan'])

# Gender options (M/F/U) + "All"
genders = ['All', 'M', 'F', 'U']

# Safety equipment options, filtered to avoid noisy/unhelpful labels and limited to top ~15
safety_equip = ['All'] + sorted(
    [s for s in df['SAFETY_EQUIPMENT'].dropna().unique()
     if str(s) not in ['nan', 'NOT APPLICABLE', 'NOT REPORTED', 'DOES NOT APPLY']][:15]
)

# -------------------------------------------------------
# Smart search parser: parse natural language into filters
# -------------------------------------------------------

def smart_search_parser(search_text):
    """Parse natural language search query into filter dictionary and human-readable summary.

    Returns:
        filters: dict of parsed filter values (borough, year, month, dow, hour_range, vehicle, etc.)
        applied_filters: list of strings describing what was detected (for feedback to user).
    """
    if not search_text:
        # No query → no filters
        return None

    search_lower = search_text.lower()
    filters = {}
    applied_filters = []

    # --- Borough detection ---
    boroughs_map = ['BROOKLYN', 'MANHATTAN', 'QUEENS', 'BRONX', 'STATEN ISLAND']
    for b in boroughs_map:
        if b.lower() in search_lower:
            filters['borough'] = b
            applied_filters.append(f"Borough: {b}")
            break

    # --- Year detection (any year 2010–2029 pattern like 2019, 2020, etc.) ---
    years_found = re.findall(r'\b(20[1-2][0-9])\b', search_text)
    if years_found:
        filters['year'] = int(years_found[0])
        applied_filters.append(f"Year: {years_found[0]}")

    # --- Month detection using month names/abbreviations ---
    months_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    for m_name, m_num in months_map.items():
        if m_name in search_lower:
            filters['month'] = m_num
            applied_filters.append(f"Month: {m_name.capitalize()}")
            break

    # --- Day-of-week detection ---
    # Map keywords (weekday, weekend, mon, tue, etc.) to underlying day indices (0=Mon..6=Sun)
    days_map = {
        'monday': [0], 'tuesday': [1], 'wednesday': [2], 'thursday': [3],
        'friday': [4], 'saturday': [5], 'sunday': [6],
        'mon': [0], 'tue': [1], 'wed': [2], 'thu': [3], 'fri': [4], 'sat': [5], 'sun': [6],
        'weekday': [0, 1, 2, 3, 4], 'weekend': [5, 6]
    }
    for day_name, day_nums in days_map.items():
        if day_name in search_lower:
            filters['dow'] = day_nums
            applied_filters.append(f"Day: {day_name.capitalize()}")
            break

    # --- Time-of-day detection based on common phrases ---
    if 'morning' in search_lower:
        filters['hour_range'] = (6, 10)
        applied_filters.append("Time: Morning (6-10)")
    elif 'afternoon' in search_lower:
        filters['hour_range'] = (12, 17)
        applied_filters.append("Time: Afternoon (12-17)")
    elif 'evening' in search_lower:
        filters['hour_range'] = (17, 20)
        applied_filters.append("Time: Evening (17-20)")
    elif 'night' in search_lower:
        filters['hour_range'] = (20, 23)
        applied_filters.append("Time: Night (20-23)")
    elif 'late night' in search_lower or 'midnight' in search_lower:
        filters['hour_range'] = (0, 5)
        applied_filters.append("Time: Late Night (0-5)")

    # --- Vehicle type detection: map keywords to normalized vehicle categories ---
    vehicle_keywords = {
        'sedan': 'SEDAN', 'suv': 'STATION WAGON/SPORT UTILITY VEHICLE',
        'taxi': 'TAXI', 'truck': 'PICK-UP TRUCK', 'bus': 'BUS',
        'motorcycle': 'MOTORCYCLE', 'bike': 'BICYCLE', 'scooter': 'SCOOTER',
        'van': 'VAN', 'ambulance': 'AMBULANCE', 'moped': 'MOPED'
    }
    for keyword, vehicle_type in vehicle_keywords.items():
        if keyword in search_lower:
            filters['vehicle'] = vehicle_type
            applied_filters.append(f"Vehicle: {keyword.capitalize()}")
            break

    # --- Person type detection: pedestrian, cyclist, occupant/driver ---
    if 'pedestrian' in search_lower:
        filters['person_type'] = 'PEDESTRIAN'
        applied_filters.append("Person: Pedestrian")
    elif 'cyclist' in search_lower:
        filters['person_type'] = 'CYCLIST'
        applied_filters.append("Person: Cyclist")
    elif 'occupant' in search_lower or 'driver' in search_lower:
        filters['person_type'] = 'OCCUPANT'
        applied_filters.append("Person: Occupant")

    # --- Injury type detection: fatal vs injured ---
    if 'fatal' in search_lower or 'death' in search_lower or 'killed' in search_lower:
        filters['injury'] = 'KILLED'
        applied_filters.append("Injury: Fatal")
    elif 'injured' in search_lower or 'injury' in search_lower:
        filters['injury'] = 'INJURED'
        applied_filters.append("Injury: Injured")

    # --- Gender detection: male/female ---
    if 'male' in search_lower and 'female' not in search_lower:
        filters['gender'] = 'M'
        applied_filters.append("Gender: Male")
    elif 'female' in search_lower:
        filters['gender'] = 'F'
        applied_filters.append("Gender: Female")

    return filters, applied_filters

# ---------------------------------------------------
# Core reporting function: filtering + all visualizations
# ---------------------------------------------------

def generate_report(
        borough, year, month, dow, hour_min, hour_max, vehicle, person_type,
        person_injury, gender, safety, c1_x, c1_y, c3_x, c3_y, c3_top,
        c4_x, c4_y, compare_cat
):
    """Generate summary stats + 9 charts + textual insights based on current filters and settings."""

    # --------------------------------
    # Apply all filters incrementally
    # --------------------------------
    filtered_df = df.copy()

    # Filter by borough, if specified
    if borough != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == borough]

    # Filter by year
    if year != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_YEAR'] == year]

    # Filter by month
    if month != 'All':
        filtered_df = filtered_df[filtered_df['CRASH_MONTH'] == month]

    # Filter by day-of-week (list of numeric codes)
    if dow:
        filtered_df = filtered_df[filtered_df['CRASH_DAYOFWEEK'].isin(dow)]

    # Filter by hour range (inclusive)
    filtered_df = filtered_df[
        (filtered_df['CRASH_HOUR'] >= hour_min) &
        (filtered_df['CRASH_HOUR'] <= hour_max)
        ]

    # Filter by vehicle type
    if vehicle != 'All':
        filtered_df = filtered_df[filtered_df['VEHICLE TYPE CODE 1'] == vehicle]

    # Filter by person type
    if person_type != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_TYPE'] == person_type]

    # Filter by injury type
    if person_injury != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_INJURY'] == person_injury]

    # Filter by gender
    if gender != 'All':
        filtered_df = filtered_df[filtered_df['PERSON_SEX'] == gender]

    # Filter by safety equipment
    if safety != 'All':
        filtered_df = filtered_df[filtered_df['SAFETY_EQUIPMENT'] == safety]

    # If all filters remove everything, return "empty" figures with a helpful message
    if len(filtered_df) == 0:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="No data found. Adjust filters.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        return (
            "No data found", empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, "",
            empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, "", empty_fig, ""
        )

    # -----------------------
    # Summary Statistics text
    # -----------------------

    total_records = len(filtered_df)
    total_injuries = int(filtered_df['NUMBER OF PERSONS INJURED'].sum())
    total_fatalities = int(filtered_df['NUMBER OF PERSONS KILLED'].sum())
    injury_rate = (total_injuries / total_records * 100) if total_records > 0 else 0
    fatality_rate = (total_fatalities / total_records * 100) if total_records > 0 else 0

    # Markdown table summarizing key metrics for this filtered subset
    summary_text = f"""
## 📊 Summary Statistics
| Metric | Value |
|--------|-------|
| **Total Records** | {total_records:,} |
| **Total Injuries** | {total_injuries:,} ({injury_rate:.2f}%) |
| **Total Fatalities** | {total_fatalities:,} ({fatality_rate:.2f}%) |
| **Pedestrian Injuries** | {int(filtered_df['NUMBER OF PEDESTRIANS INJURED'].sum()):,} |
| **Cyclist Injuries** | {int(filtered_df['NUMBER OF CYCLIST INJURED'].sum()):,} |
| **Motorist Injuries** | {int(filtered_df['NUMBER OF MOTORIST INJURED'].sum()):,} |
| **Unique Crashes** | {len(filtered_df['COLLISION_ID'].unique()):,} |
| **Avg Persons/Crash** | {(total_records / len(filtered_df['COLLISION_ID'].unique())):.1f} |
    """

    # -------------------------
    # Chart 1: Trend Analysis
    # -------------------------

    # If c1_y is 'count', use counts per temporal bucket; else sum numeric column
    if c1_y == 'count':
        chart1_data = filtered_df.groupby(c1_x).size().reset_index(name='count')
        y_label = 'Number of Records'
    else:
        chart1_data = filtered_df.groupby(c1_x)[c1_y].sum().reset_index()
        y_label = c1_y

    # Line chart over selected temporal dimension
    fig1 = px.line(
        chart1_data,
        x=c1_x,
        y=chart1_data.columns[1],
        labels={chart1_data.columns[1]: y_label, c1_x: c1_x},
        title='Trend Analysis'
    )
    fig1.update_traces(line_color='#3498db', line_width=3)
    fig1.update_layout(template='plotly_white', height=400)

    # Simple insight: where is the peak and the minimum
    max_val = chart1_data[chart1_data.columns[1]].max()
    min_val = chart1_data[chart1_data.columns[1]].min()
    max_cat = chart1_data.loc[chart1_data[chart1_data.columns[1]].idxmax(), c1_x]
    min_cat = chart1_data.loc[chart1_data[chart1_data.columns[1]].idxmin(), c1_x]
    insight1 = f"📈 **Insight:** Peak at {max_cat} ({max_val:,.0f}), lowest at {min_cat} ({min_val:,.0f})"

    # --------------------------------
    # Chart 2: Person Type Distribution
    # --------------------------------

    # Pie chart of person types (pedestrian, cyclist, occupant, etc.)
    person_type_data = filtered_df['PERSON_TYPE'].value_counts()
    fig2 = px.pie(
        values=person_type_data.values,
        names=person_type_data.index,
        title='Person Type Distribution',
        color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c', '#3498db']
    )
    fig2.update_layout(height=400)

    # Most common person type and its percentage share
    most_common = person_type_data.idxmax()
    pct = (person_type_data.max() / person_type_data.sum() * 100)
    insight2 = f"🥧 **Insight:** Most common person type: {most_common} ({pct:.1f}% of records)"

    # --------------------------------
    # Chart 3: Categorical Analysis
    # --------------------------------

    # Either count per category or sum of numeric metric per category (top N)
    if c3_y == 'count':
        chart3_data = filtered_df[c3_x].value_counts().head(int(c3_top))
        y_label = 'Number of Records'
    else:
        chart3_data = (
            filtered_df.groupby(c3_x)[c3_y]
            .sum()
            .sort_values(ascending=False)
            .head(int(c3_top))
        )
        y_label = c3_y

    fig3 = px.bar(
        x=chart3_data.index,
        y=chart3_data.values,
        labels={'x': c3_x, 'y': y_label},
        title=f'Categorical Analysis - Top {int(c3_top)}'
    )
    fig3.update_traces(marker_color='#3498db')
    fig3.update_layout(template='plotly_white', height=400)

    # Highlight the highest and lowest categories shown
    max_cat3 = chart3_data.idxmax()
    min_cat3 = chart3_data.idxmin()
    insight3 = (
        f"📊 **Insight:** Highest: {max_cat3} ({chart3_data.max():,.0f}), "
        f"Lowest: {min_cat3} ({chart3_data.min():,.0f})"
    )

    # ------------------------------
    # Chart 4: Time Distribution
    # ------------------------------

    # Similar to Chart 3 but specifically for temporal axis (e.g., hour, month)
    if c4_y == 'count':
        chart4_data = filtered_df[c4_x].value_counts().sort_index()
        y_label = 'Number of Records'
    else:
        chart4_data = filtered_df.groupby(c4_x)[c4_y].sum().sort_index()
        y_label = c4_y

    fig4 = px.bar(
        x=chart4_data.index,
        y=chart4_data.values,
        labels={'x': c4_x, 'y': y_label},
        title='Time Distribution'
    )
    fig4.update_traces(marker_color='#e67e22')
    fig4.update_layout(template='plotly_white', height=400)

    max_cat4 = chart4_data.idxmax()
    min_cat4 = chart4_data.idxmin()
    insight4 = (
        f"⏰ **Insight:** Peak time: {max_cat4} ({chart4_data.max():,.0f}), "
        f"Quietest: {min_cat4} ({chart4_data.min():,.0f})"
    )

    # ---------------------------------------
    # Chart 5: Top Contributing Factor Vehicle 1
    # ---------------------------------------

    # Frequency of primary contributing factors, excluding 'UNSPECIFIED'
    factor1_data = filtered_df['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(15)
    factor1_data = factor1_data[factor1_data.index != 'UNSPECIFIED']

    fig5 = px.bar(
        x=factor1_data.index,
        y=factor1_data.values,
        labels={'x': 'Contributing Factor', 'y': 'Number of Crashes'},
        title='Top Contributing Factors (Vehicle 1)'
    )
    fig5.update_traces(marker_color='#e74c3c')
    fig5.update_layout(template='plotly_white', height=400, xaxis={'tickangle': -45})

    top_factor1 = factor1_data.idxmax() if len(factor1_data) > 0 else "N/A"
    top_factor1_pct = (factor1_data.max() / len(filtered_df) * 100) if len(factor1_data) > 0 else 0
    insight5 = (
        f"🚨 **Insight:** Top cause: {top_factor1} "
        f"({factor1_data.max():,} crashes, {top_factor1_pct:.1f}%)"
    )

    # ---------------------------------------
    # Chart 6: Top Contributing Factor Vehicle 2
    # ---------------------------------------

    # Same idea as Chart 5 but for the second vehicle; exclude 'UNSPECIFIED' & 'NO SECOND VEHICLE'
    factor2_data = filtered_df['CONTRIBUTING FACTOR VEHICLE 2'].value_counts().head(15)
    factor2_data = factor2_data[~factor2_data.index.isin(['UNSPECIFIED', 'NO SECOND VEHICLE'])]

    if len(factor2_data) > 0:
        fig6 = px.bar(
            x=factor2_data.index,
            y=factor2_data.values,
            labels={'x': 'Secondary Contributing Factor', 'y': 'Number of Crashes'},
            title='Top Contributing Factors (Vehicle 2)'
        )
        fig6.update_traces(marker_color='#f39c12')
        fig6.update_layout(template='plotly_white', height=400, xaxis={'tickangle': -45})

        top_factor2 = factor2_data.idxmax()
        top_factor2_pct = (factor2_data.max() / len(filtered_df) * 100)
        insight6 = (
            f"🚨 **Insight:** Top secondary cause: {top_factor2} "
            f"({factor2_data.max():,} crashes, {top_factor2_pct:.1f}%)"
        )
    else:
        # If no secondary factors, show a placeholder figure and note
        fig6 = go.Figure()
        fig6.add_annotation(
            text="No secondary factors",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig6.update_layout(height=400, title='Top Contributing Factors (Vehicle 2)')
        insight6 = (
            "ℹ️ **Note:** Most crashes involve only one vehicle or have unspecified secondary factors"
        )

    # ---------------------------------
    # Chart 7: Injury & Fatality Rates
    # ---------------------------------

    # Group by the selected comparison category (e.g., BOROUGH, CRASH_HOUR)
    compare_data = filtered_df.groupby(compare_cat).agg({
        'COLLISION_ID': 'count',
        'NUMBER OF PERSONS INJURED': 'sum',
        'NUMBER OF PERSONS KILLED': 'sum'
    }).reset_index()
    compare_data.columns = [
        compare_cat, 'Total_Records', 'Total_Injuries', 'Total_Fatalities'
    ]
    compare_data['Injury_Rate'] = (
            compare_data['Total_Injuries'] / compare_data['Total_Records'] * 100
    )
    compare_data['Fatality_Rate'] = (
            compare_data['Total_Fatalities'] / compare_data['Total_Records'] * 100
    )

    # If comparing by day-of-week, convert numeric codes to names and keep natural order
    if compare_cat == 'CRASH_DAYOFWEEK':
        day_mapping = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
        }
        compare_data[compare_cat] = compare_data[compare_cat].map(day_mapping)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        compare_data[compare_cat] = pd.Categorical(
            compare_data[compare_cat], categories=day_order, ordered=True
        )
        compare_data = compare_data.sort_values(compare_cat)
    else:
        # Otherwise, sort by highest injury rate and limit to top 15 for readability
        compare_data = compare_data.sort_values('Injury_Rate', ascending=False).head(15)

    # Grouped bar chart for injury and fatality rates
    fig7 = go.Figure()
    fig7.add_trace(go.Bar(
        x=compare_data[compare_cat],
        y=compare_data['Injury_Rate'],
        name='Injury Rate (%)',
        marker_color='#f39c12'
    ))
    fig7.add_trace(go.Bar(
        x=compare_data[compare_cat],
        y=compare_data['Fatality_Rate'],
        name='Fatality Rate (%)',
        marker_color='#e74c3c'
    ))
    fig7.update_layout(
        barmode='group',
        template='plotly_white',
        height=400,
        title='Injury Rate Comparison',
        xaxis_title=compare_cat,
        yaxis_title='Rate (%)'
    )

    highest_injury = compare_data.loc[compare_data['Injury_Rate'].idxmax()]
    highest_fatal = compare_data.loc[compare_data['Fatality_Rate'].idxmax()]
    insight7 = (
        f"⚠️ **Insight:** Highest injury rate: {highest_injury[compare_cat]} "
        f"({highest_injury['Injury_Rate']:.2f}%), "
        f"Highest fatality rate: {highest_fatal[compare_cat]} "
        f"({highest_fatal['Fatality_Rate']:.2f}%)"
    )

    # --------------------------
    # Chart 8: Day × Hour Heatmap
    # --------------------------

    # Cross-tab of crashes by (day-of-week, hour)
    heatmap_data = (
        filtered_df.groupby(['CRASH_DAYOFWEEK', 'CRASH_HOUR'])
        .size()
        .reset_index(name='count')
    )
    if len(heatmap_data) > 0:
        heatmap_pivot = heatmap_data.pivot(
            index='CRASH_DAYOFWEEK', columns='CRASH_HOUR', values='count'
        )

        fig8 = go.Figure(
            data=go.Heatmap(
                z=heatmap_pivot.values,
                x=heatmap_pivot.columns,
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                colorscale='YlOrRd'
            )
        )
        fig8.update_layout(
            xaxis_title='Hour of Day',
            yaxis_title='Day of Week',
            title='Day × Hour Heatmap',
            template='plotly_white',
            height=500
        )

        # Find the busiest day overall and busiest hour overall
        max_day = heatmap_pivot.sum(axis=1).idxmax()
        max_hour = heatmap_pivot.sum(axis=0).idxmax()
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        insight8 = (
            f"🗓️ **Insight:** Busiest day: {day_names[max_day]}, "
            f"Busiest hour: {max_hour}:00"
        )
    else:
        # No data means an empty heatmap
        fig8 = go.Figure()
        fig8.update_layout(height=500, title='Day × Hour Heatmap')
        insight8 = ""

    # -----------------------------
    # Chart 9: Geographic Map (NYC)
    # -----------------------------

    # Basic spatial filter to remove invalid latitudes (NYC bounding box)
    map_sample = filtered_df[
        (filtered_df['LATITUDE'].notna()) &
        (filtered_df['LATITUDE'] != 0) &
        (filtered_df['LATITUDE'] > 40) &
        (filtered_df['LATITUDE'] < 41)
        ]

    if len(map_sample) > 0:
        # Sample up to 3000 points for performance and responsiveness
        map_sample = map_sample.sample(n=min(3000, len(map_sample)), random_state=42)

        # Helper: categorize crash severity for color-coding on map
        def categorize_severity(row):
            if row['NUMBER OF PERSONS KILLED'] > 0:
                return 'Fatal'
            elif row['NUMBER OF PERSONS INJURED'] > 0:
                return 'Injury'
            else:
                return 'Property Damage Only'

        map_sample['SEVERITY_CATEGORY'] = map_sample.apply(categorize_severity, axis=1)

        # Map severity categories to custom colors
        color_map = {
            'Fatal': '#e74c3c',
            'Injury': '#f39c12',
            'Property Damage Only': '#9d7aff'
        }

        # NOTE: This assumes a plotly scatter-map function (e.g., scatter_mapbox / scatter_geo).
        # The code uses px.scatter_map as written by you; keeping logic unchanged as requested.
        fig9 = px.scatter_map(
            map_sample,
            lat='LATITUDE',
            lon='LONGITUDE',
            color='SEVERITY_CATEGORY',
            color_discrete_map=color_map,
            title=f'Geographic Distribution (Sample of {len(map_sample):,} locations)',
            zoom=10,
            height=600,
            hover_data={
                'LATITUDE': False,
                'LONGITUDE': False,
                'SEVERITY_CATEGORY': True,
                'NUMBER OF PERSONS INJURED': True,
                'NUMBER OF PERSONS KILLED': True,
                'BOROUGH': True,
                'VEHICLE TYPE CODE 1': True
            }
        )
        fig9.update_layout(map_style="open-street-map")

        # Summarize what is most common severity in the sample
        severity_counts = map_sample['SEVERITY_CATEGORY'].value_counts()
        top_severity = severity_counts.idxmax() if len(severity_counts) > 0 else "N/A"
        insight9 = (
            f"🗺️ **Insight:** Showing {len(map_sample):,} locations, "
            f"most common severity: {top_severity}"
        )
    else:
        # If no location data, show a static message instead of map
        fig9 = go.Figure()
        fig9.add_annotation(
            text="No location data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig9.update_layout(height=600, title='Geographic Distribution')
        insight9 = ""

    # Return all text + figures in the order expected by the Gradio interface
    return (
        summary_text, fig1, insight1, fig2, insight2, fig3, insight3, fig4, insight4,
        fig5, insight5, fig6, insight6, fig7, insight7, fig8, insight8, fig9, insight9
    )

# ---------------------------------------------------
# Smart search wrapper: connects parser to UI fields
# ---------------------------------------------------

def apply_smart_search(search_text):
    """Apply smart search parser and map results to Gradio component values."""
    result = smart_search_parser(search_text)
    if result is None:
        # If no filters detected, keep all dropdowns at 'All' and show a helpful message
        return ['All'] * 11 + ["⚠️ No filters detected. Try: 'Brooklyn 2022 pedestrian crashes'"]

    filters, applied = result
    feedback = "✅ Filters Applied: " + ", ".join(applied) + "\n\nClick 'Generate Report' to see results."

    # Map parsed filters dict into ordered outputs that match the Gradio inputs
    return (
        filters.get('borough', 'All'),
        filters.get('year', 'All'),
        filters.get('month', 'All'),
        filters.get('dow', []),
        filters.get('hour_range', (0, 23))[0],
        filters.get('hour_range', (0, 23))[1],
        filters.get('vehicle', 'All'),
        filters.get('person_type', 'All'),
        filters.get('injury', 'All'),
        filters.get('gender', 'All'),
        filters.get('safety', 'All'),
        feedback
    )

# ---------------------------
# Gradio UI: layout + wiring
# ---------------------------

# Create Gradio Blocks app with a title
with gr.Blocks(title="NYC Motor Vehicle Crashes Dashboard") as demo:
    # Main title and short subtitle
    gr.Markdown("# 🚗 NYC Motor Vehicle Crashes Dashboard - Enhanced Analytics")
    gr.Markdown("### Comprehensive analysis with 5.7M+ crash records")

    # Smart Search accordion: natural language query → filter pre-fill
    with gr.Accordion("🔎 Smart Search", open=True):
        gr.Markdown(
            "**Type natural language queries** like: "
            "`Brooklyn 2022 pedestrian crashes` or `Manhattan weekend taxi injured`"
        )
        with gr.Row():
            # Text input for free-form search
            search_input = gr.Textbox(
                label="Search Query",
                placeholder="e.g., Queens Friday night motorcycle fatalities...",
                scale=3
            )
            # Button to parse query and apply filters
            search_btn = gr.Button("🔍 Apply Smart Search", variant="primary", scale=1)
            # Button to clear search text + feedback
            clear_search_btn = gr.Button("❌ Clear", variant="stop", scale=1)
        # Feedback area showing which filters were detected from the query
        search_feedback = gr.Markdown(visible=True)

    with gr.Row():
        # ------------------- Left column: filters -------------------
        with gr.Column(scale=1):
            gr.Markdown("### 🎛️ Filters")

            # Borough dropdown (All + 5 boroughs)
            borough = gr.Dropdown(choices=boroughs, value='All', label="Borough")

            # Year dropdown (All + year list)
            year = gr.Dropdown(choices=years, value='All', label="Year")

            # Month dropdown (All + 1–12)
            month = gr.Dropdown(choices=months, value='All', label="Month")

            # Day-of-week checkbox group (allows multiple selection)
            dow = gr.CheckboxGroup(
                choices=[('Mon', 0), ('Tue', 1), ('Wed', 2), ('Thu', 3),
                         ('Fri', 4), ('Sat', 5), ('Sun', 6)],
                label="Day of Week",
                type="value"
            )

            # Hour range sliders to define min/max hour window
            with gr.Row():
                hour_min = gr.Slider(
                    minimum=0, maximum=23, value=0, step=1, label="Hour Min"
                )
                hour_max = gr.Slider(
                    minimum=0, maximum=23, value=23, step=1, label="Hour Max"
                )

            # Vehicle type filter for VEHICLE TYPE CODE 1
            vehicle = gr.Dropdown(choices=vehicles, value='All', label="Vehicle Type 1")

            # Person type filter (pedestrian, cyclist, occupant, etc.)
            person_type = gr.Dropdown(choices=person_types, value='All', label="Person Type")

            # Injury type filter (INJURED/KILLED/None)
            person_injury = gr.Dropdown(choices=injury_types, value='All', label="Person Injury")

            # Gender filter (M/F/U)
            gender = gr.Dropdown(choices=genders, value='All', label="Gender")

            # Safety equipment filter (top N options only)
            safety = gr.Dropdown(choices=safety_equip, value='All', label="Safety Equipment")

        # ------------------- Right column: chart settings -------------------
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Chart Settings")

            # Chart 1 (Trend) X-axis: choose from temporal columns
            c1_x = gr.Dropdown(
                choices=TEMPORAL_COLS,
                value='CRASH_YEAR',
                label="Chart 1 X-axis (Trend)"
            )
            # Chart 1 Y-axis: either 'count' or one of numeric columns
            c1_y = gr.Dropdown(
                choices=['count'] + NUMERIC_COLS,
                value='count',
                label="Chart 1 Y-axis"
            )

            # Chart 3 category axis: choose from categorical columns
            c3_x = gr.Dropdown(
                choices=CATEGORICAL_COLS,
                value='BOROUGH',
                label="Chart 3 Category"
            )
            # Chart 3 measure: count or numeric column
            c3_y = gr.Dropdown(
                choices=['count'] + NUMERIC_COLS,
                value='count',
                label="Chart 3 Y-axis"
            )
            # Top N categories to show in Chart 3
            c3_top = gr.Slider(
                minimum=5, maximum=20, value=10, step=1,
                label="Chart 3 Top N"
            )

            # Chart 4 X-axis: temporal dimension again
            c4_x = gr.Dropdown(
                choices=TEMPORAL_COLS,
                value='CRASH_HOUR',
                label="Chart 4 X-axis (Time)"
            )
            # Chart 4 Y-axis: count or numeric column
            c4_y = gr.Dropdown(
                choices=['count'] + NUMERIC_COLS,
                value='count',
                label="Chart 4 Y-axis"
            )

            # Comparison category for Chart 7 (injury/fatality rate comparison)
            compare_cat = gr.Dropdown(
                choices=[
                    'BOROUGH', 'VEHICLE TYPE CODE 1', 'PERSON_TYPE',
                    'SAFETY_EQUIPMENT', 'CRASH_HOUR', 'CRASH_DAYOFWEEK',
                    'CRASH_MONTH', 'CRASH_YEAR', 'POSITION_IN_VEHICLE', 'PERSON_SEX'
                ],
                value='BOROUGH',
                label="Comparison Category"
            )

    # ------------------- Global action buttons -------------------
    with gr.Row():
        # Main button to trigger report generation (all charts + summary)
        generate_btn = gr.Button(
            "🔍 Generate Report", variant="primary", size="lg", scale=2
        )
        # Button to reset all filters to default values
        reset_btn = gr.Button(
            "🔄 Reset All Filters", variant="secondary", size="lg", scale=1
        )

    # ------------------- Outputs: Summary + Charts + Insights -------------------

    # Markdown area for summary statistics table
    summary_output = gr.Markdown(label="Summary Statistics")

    # Row 1: Trend & Person Type distribution
    with gr.Row():
        with gr.Column():
            chart1_output = gr.Plot(label="Chart 1: Trend Analysis")
            insight1_output = gr.Markdown(label="Insight")
        with gr.Column():
            chart2_output = gr.Plot(label="Chart 2: Person Type Distribution")
            insight2_output = gr.Markdown(label="Insight")

    # Row 2: Categorical Analysis & Time Distribution
    with gr.Row():
        with gr.Column():
            chart3_output = gr.Plot(label="Chart 3: Categorical Analysis")
            insight3_output = gr.Markdown(label="Insight")
        with gr.Column():
            chart4_output = gr.Plot(label="Chart 4: Time Distribution")
            insight4_output = gr.Markdown(label="Insight")

    # Row 3: Contributing factors 1 & 2
    with gr.Row():
        with gr.Column():
            chart5_output = gr.Plot(label="Chart 5: Contributing Factor 1")
            insight5_output = gr.Markdown(label="Insight")
        with gr.Column():
            chart6_output = gr.Plot(label="Chart 6: Contributing Factor 2")
            insight6_output = gr.Markdown(label="Insight")

    # Chart 7: Injury/Fatality rate comparison
    chart7_output = gr.Plot(label="Chart 7: Injury Rate Comparison")
    insight7_output = gr.Markdown(label="Insight")

    # Chart 8: Day × Hour heatmap
    chart8_output = gr.Plot(label="Chart 8: Day × Hour Heatmap")
    insight8_output = gr.Markdown(label="Insight")

    # Chart 9: Map of crash locations and severity
    chart9_output = gr.Plot(label="Chart 9: Geographic Distribution Map")
    insight9_output = gr.Markdown(label="Insight")

    # ------------------- Event handlers / callbacks -------------------

    # Wire "Generate Report" button to the generate_report function
    generate_btn.click(
        fn=generate_report,
        inputs=[
            borough, year, month, dow, hour_min, hour_max, vehicle, person_type,
            person_injury, gender, safety, c1_x, c1_y, c3_x, c3_y, c3_top,
            c4_x, c4_y, compare_cat
        ],
        outputs=[
            summary_output,
            chart1_output, insight1_output,
            chart2_output, insight2_output,
            chart3_output, insight3_output,
            chart4_output, insight4_output,
            chart5_output, insight5_output,
            chart6_output, insight6_output,
            chart7_output, insight7_output,
            chart8_output, insight8_output,
            chart9_output, insight9_output
        ]
    )

    # Helper to reset all filters to default values and clear smart-search feedback
    def reset_all():
        # Return values in the same order as reset_btn.click outputs
        return ('All', 'All', 'All', [], 0, 23, 'All', 'All', 'All', 'All', 'All', '')

    # Wire "Reset All Filters" button to reset_all helper
    reset_btn.click(
        fn=reset_all,
        outputs=[
            borough, year, month, dow, hour_min, hour_max, vehicle, person_type,
            person_injury, gender, safety, search_feedback
        ]
    )

    # Wire "Apply Smart Search" button to smart search function
    search_btn.click(
        fn=apply_smart_search,
        inputs=[search_input],
        outputs=[
            borough, year, month, dow, hour_min, hour_max, vehicle, person_type,
            person_injury, gender, safety, search_feedback
        ]
    )

    # Wire "Clear" button to reset search box and feedback only
    clear_search_btn.click(
        fn=lambda: ('', ''),
        outputs=[search_input, search_feedback]
    )

# -------------------
# App entry point
# -------------------
if __name__ == "__main__":
    # Launch Gradio app (no public sharing by default)
    demo.launch(share=False)
