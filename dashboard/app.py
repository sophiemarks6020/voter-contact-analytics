import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

import os

DB_PATH = ':memory:'
CSV_PATH = 'raw/election_data.csv'

@st.cache_resource
def get_connection():
    conn = duckdb.connect(DB_PATH)
    conn.execute("""
        CREATE VIEW IF NOT EXISTS stg_election AS
        SELECT
            year, state, state_po, county_name, candidate, party, mode,
            candidatevotes, totalvotes,
            round(candidatevotes * 100.0 / totalvotes, 2) as vote_share_pct
        FROM read_csv_auto('""" + CSV_PATH + """', nullstr='NA', sample_size=-1)
        WHERE totalvotes > 0 AND candidatevotes IS NOT NULL
    """)
    conn.execute("""
        CREATE VIEW IF NOT EXISTS mart_state_trends AS
        WITH clean_states AS (
            SELECT year, state, state_po, party,
                sum(candidatevotes) as total_candidate_votes,
                sum(totalvotes) as total_votes
            FROM stg_election
            WHERE year IN (2016, 2020)
            AND party IN ('DEMOCRAT', 'REPUBLICAN')
            AND mode = 'TOTAL'
            GROUP BY year, state, state_po, party
        ),
        messy_states AS (
            SELECT year, state, state_po, party,
                sum(candidatevotes) as total_candidate_votes
            FROM stg_election
            WHERE year IN (2016, 2020)
            AND party IN ('DEMOCRAT', 'REPUBLICAN')
            AND state IN (
                SELECT state FROM (
                    SELECT state, year
                    FROM stg_election
                    WHERE mode = 'TOTAL' AND year IN (2016, 2020)
                    GROUP BY state, year
                ) t
                GROUP BY state
                HAVING count(DISTINCT year) < 2
            )
            AND mode != 'TOTAL'
            GROUP BY year, state, state_po, party
        ),
        messy_totals AS (
            SELECT year, state, sum(candidatevotes) as total_votes
            FROM stg_election
            WHERE year IN (2016, 2020)
            AND state IN (SELECT DISTINCT state FROM messy_states)
            AND mode != 'TOTAL'
            GROUP BY year, state
        ),
        messy_combined AS (
            SELECT m.year, m.state, m.state_po, m.party,
                m.total_candidate_votes, t.total_votes
            FROM messy_states m
            JOIN messy_totals t ON m.state = t.state AND m.year = t.year
        ),
        combined AS (
            SELECT * FROM clean_states
            UNION ALL
            SELECT * FROM messy_combined
        ),
        vote_share AS (
            SELECT year, state, state_po, party, total_votes,
                round(total_candidate_votes * 100.0 / total_votes, 2) as vote_share_pct
            FROM combined WHERE total_votes > 0
        ),
        pivoted AS (
            SELECT state, state_po,
                max(CASE WHEN year = 2016 AND party = 'DEMOCRAT' THEN vote_share_pct END) as dem_2016,
                max(CASE WHEN year = 2020 AND party = 'DEMOCRAT' THEN vote_share_pct END) as dem_2020,
                max(CASE WHEN year = 2016 AND party = 'REPUBLICAN' THEN vote_share_pct END) as rep_2016,
                max(CASE WHEN year = 2020 AND party = 'REPUBLICAN' THEN vote_share_pct END) as rep_2020,
                max(CASE WHEN year = 2016 THEN total_votes END) as total_votes_2016,
                max(CASE WHEN year = 2020 THEN total_votes END) as total_votes_2020
            FROM vote_share GROUP BY state, state_po
        )
        SELECT state, state_po, dem_2016, dem_2020, rep_2016, rep_2020,
            round(dem_2020 - dem_2016, 2) as dem_shift,
            round(rep_2020 - rep_2016, 2) as rep_shift,
            total_votes_2020 - total_votes_2016 as turnout_change
        FROM pivoted
        WHERE dem_2016 IS NOT NULL AND dem_2020 IS NOT NULL
        ORDER BY dem_shift DESC
    """)
    return conn

conn = get_connection()

st.set_page_config(
    page_title="Voter Contact Analytics",
    page_icon="",
    layout="wide"
)

st.title(" U.S. Presidential Election Shift Analysis (2016-2020)")
st.markdown("**Built for America Votes | Analyzing Democratic Vote Share Trends by State**")

st.markdown("---")

st.markdown("""
### About This Dashboard
This dashboard analyzes shifts in Democratic presidential vote share between
the 2016 and 2020 U.S. presidential elections using county-level returns
aggregated to the state level.

**Data Source:** MIT Election Lab - County Presidential Election Returns 2000-2024

**Methodology:** Vote share is calculated as each party's total votes divided
by total votes cast per state. Shift is the difference in Democratic vote share
between 2016 and 2020.

**Purpose:** To identify which states showed the most movement toward Democratic
candidates - informing where progressive voter contact programs may have had
the greatest impact and where future investment could be most effective.
""")

st.markdown("---")

df = conn.execute("""
    SELECT * FROM mart_state_trends
    WHERE state != 'DISTRICT OF COLUMBIA'
""").df()

st.sidebar.title("Filters")
regions = {
    "All States": list(df['state']),
    "Swing States": ["PENNSYLVANIA", "MICHIGAN", "WISCONSIN", "ARIZONA", "GEORGIA", "NEVADA", "NORTH CAROLINA"],
    "Northeast": ["CONNECTICUT", "MAINE", "MASSACHUSETTS", "NEW HAMPSHIRE", "NEW JERSEY", "NEW YORK", "PENNSYLVANIA", "RHODE ISLAND", "VERMONT"],
    "Midwest": ["ILLINOIS", "INDIANA", "IOWA", "KANSAS", "MICHIGAN", "MINNESOTA", "MISSOURI", "NEBRASKA", "NORTH DAKOTA", "OHIO", "SOUTH DAKOTA", "WISCONSIN"],
    "South": ["ALABAMA", "ARKANSAS", "FLORIDA", "GEORGIA", "KENTUCKY", "LOUISIANA", "MARYLAND", "MISSISSIPPI", "NORTH CAROLINA", "OKLAHOMA", "SOUTH CAROLINA", "TENNESSEE", "TEXAS", "VIRGINIA", "WEST VIRGINIA"],
    "West": ["ALASKA", "ARIZONA", "CALIFORNIA", "COLORADO", "HAWAII", "IDAHO", "MONTANA", "NEVADA", "NEW MEXICO", "OREGON", "UTAH", "WASHINGTON", "WYOMING"]
}

selected_region = st.sidebar.selectbox("Filter by Region", list(regions.keys()))
selected_states = st.sidebar.multiselect("Or select specific states", sorted(df['state'].tolist()), default=[])

if selected_states:
    df = df[df['state'].isin(selected_states)]
elif selected_region != "All States":
    df = df[df['state'].isin(regions[selected_region])]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("States Analyzed", len(df))
with col2:
    st.metric("Avg Dem Shift", f"+{df['dem_shift'].mean():.2f}%" if len(df) > 0 else "N/A")
with col3:
    st.metric("States w/ Dem Vote Share Increase", f"{len(df[df['dem_shift'] > 0])} of {len(df)}")
with col4:
    if len(df) > 0:
        st.metric("Biggest Gain", f"{df.loc[df['dem_shift'].idxmax(), 'state_po']} +{df['dem_shift'].max():.2f}%")
    else:
        st.metric("Biggest Gain", "N/A")

st.markdown("---")

st.subheader("Democratic Vote Share Shift by State (2016 to 2020)")
fig1 = px.bar(
    df.sort_values('dem_shift'),
    x='dem_shift',
    y='state_po',
    orientation='h',
    color='dem_shift',
    color_continuous_scale='RdBu',
    labels={'dem_shift': 'Shift in Vote Share (%)', 'state_po': 'State'},
    height=800
)
fig1.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig1, use_container_width=Tst.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})rue)

st.markdown("---")

st.subheader("Voter Turnout Change by State (2016 to 2020)")
st.caption("How many more total votes were cast in 2020 vs 2016.")
fig3 = px.bar(
    df.sort_values('turnout_change'),
    x='turnout_change',
    y='state_po',
    orientation='h',
    color='turnout_change',
    color_continuous_scale='Blues',
    labels={'turnout_change': 'Change in Total Votes', 'state_po': 'State'},
    height=800
)
fig3.update_layout(
    coloraxis_showscale=False,
    xaxis=dict(tickformat=',')
)
st.plotly_chart(fig3, use_container_width=True, config={'staticPlot': True})

st.markdown("---")

st.subheader("2016 vs 2020 Democratic Vote Share by State")
st.markdown("""
Each dot represents a state. The horizontal axis shows Democratic vote share in 2016,
and the vertical axis shows Democratic vote share in 2020. The dashed diagonal line
is a reference line representing zero change - states whose dots fall above it improved
their Democratic vote share from 2016 to 2020, while states below it lost ground.

Dot color reflects the magnitude of the shift: blue dots indicate larger Democratic
gains, while red dots indicate smaller gains. The further a dot sits above the line,
the more significant the improvement. Hover over any dot to see the state name, both
vote share figures, and the net shift.

The reference line is mathematically derived from the actual data range - it spans
from the minimum to maximum vote share values observed across both years, ensuring
the line accurately reflects the scale of the data.
""")

min_val = int(df[['dem_2016', 'dem_2020']].min().min()) - 2
max_val = int(df[['dem_2016', 'dem_2020']].max().max()) + 2

fig2 = px.scatter(
    df,
    x='dem_2016',
    y='dem_2020',
    hover_name='state',
    color='dem_shift',
    color_continuous_scale='RdBu',
    hover_data={'state_po': True, 'dem_2016': True, 'dem_2020': True, 'dem_shift': True},
    labels={'dem_2016': 'Dem Vote Share 2016 (%)', 'dem_2020': 'Dem Vote Share 2020 (%)', 'dem_shift': 'Dem Shift (%)'},
    height=550
)
fig2.add_shape(type='line', x0=min_val, y0=min_val, x1=max_val, y1=max_val,
               line=dict(color='gray', dash='dash'))
fig2.update_traces(marker=dict(size=10))
fig2.update_layout(
    dragmode='pan',
    xaxis=dict(fixedrange=False),
    yaxis=dict(fixedrange=False),
    modebar_remove=['zoom', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
)
st.plotly_chart(fig2, use_container_width=True, config={
    'scrollZoom': True,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
    'dragmode': 'pan'
})

st.markdown("---")

st.subheader("Turnout Change vs Democratic Vote Share Shift")
st.markdown("""
This chart explores whether states with higher voter turnout increases also saw
larger Democratic vote share gains. A positive correlation would suggest that
progressive voter mobilization efforts drove Democratic performance improvements.

Nationally, the correlation is weakly negative - suggesting persuasion of existing
voters drove Democratic gains more than raw turnout increases. However, when filtered
to swing states specifically, the correlation turns positive - indicating that in
competitive states, voter mobilization efforts were more directly tied to Democratic
vote share improvements. Use the sidebar filter to explore this pattern.
""")

fig4 = px.scatter(
    df,
    x='turnout_change',
    y='dem_shift',
    hover_name='state',
    hover_data={'state_po': True, 'turnout_change': True, 'dem_shift': True},
    labels={'turnout_change': 'Change in Total Votes', 'dem_shift': 'Dem Vote Share Shift (%)'},
    trendline='ols',
    height=500
)
fig4.update_traces(marker=dict(size=10, color='steelblue'),
                   selector=dict(mode='markers'))
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

st.subheader("Full State-Level Data")
display_df = df.sort_values('dem_shift', ascending=False).copy()
display_df = display_df[['state', 'state_po', 'dem_shift', 'rep_shift', 'dem_2016', 'dem_2020', 'rep_2016', 'rep_2020', 'turnout_change']]
display_df.index = range(1, len(display_df) + 1)
display_df['dem_2016'] = display_df['dem_2016'].map(lambda x: f"{x}%")
display_df['dem_2020'] = display_df['dem_2020'].map(lambda x: f"{x}%")
display_df['rep_2016'] = display_df['rep_2016'].map(lambda x: f"{x}%")
display_df['rep_2020'] = display_df['rep_2020'].map(lambda x: f"{x}%")
display_df['dem_shift'] = display_df['dem_shift'].map(lambda x: f"{x}%")
display_df['rep_shift'] = display_df['rep_shift'].map(lambda x: f"{x}%")
st.dataframe(display_df, use_container_width=True)

st.markdown("---")

st.markdown("""
### Methodology Note
**Data Source:** MIT Election Lab - County Presidential Election Returns 2000-2024

**Coverage:** All 50 U.S. states (Washington D.C. excluded as it has no Electoral College votes).

**Vote Reporting:** States report election results differently - some report a single unified
total, others report by voting mode (Election Day, Absentee, Early Vote, etc.).
This analysis handles both cases: unified totals are used where available,
and breakdown modes are summed where they are not, ensuring all 50 states are represented accurately.
""")