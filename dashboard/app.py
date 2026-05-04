import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Connect to DuckDB
conn = duckdb.connect('C:/Users/13609/voter_contact_analysis/data/election.duckdb')

# Page config
st.set_page_config(
    page_title="Voter Contact Analytics",
    page_icon="🗳️",
    layout="wide"
)

# Title
st.title("🗳️ Voter Contact Effectiveness Dashboard")
st.markdown("**America Votes | 2016–2020 Presidential Election Analysis**")
st.markdown("---")

# Load data
df = conn.execute("SELECT * FROM mart_state_trends").df()

# KPI Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("States Analyzed", len(df))
with col2:
    st.metric("Avg Dem Shift", f"+{df['dem_shift'].mean():.2f}%")
with col3:
    st.metric("States with Dem Vote Share Increase", f"{len(df[df['dem_shift'] > 0])} of {len(df)}")
with col4:
    st.metric("Biggest Gain", f"{df.loc[df['dem_shift'].idxmax(), 'state_po']} +{df['dem_shift'].max():.2f}%")

st.markdown("---")

# Bar chart - dem shift by state
st.subheader("Democratic Vote Share Shift by State (2016 → 2020)")
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
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# Scatter - 2016 vs 2020
st.subheader("2016 vs 2020 Democratic Vote Share by State")
fig2 = px.scatter(
    df,
    x='dem_2016',
    y='dem_2020',
    text='state_po',
    labels={'dem_2016': 'Dem Vote Share 2016 (%)', 'dem_2020': 'Dem Vote Share 2020 (%)'},
    height=500
)
fig2.add_shape(type='line', x0=20, y0=20, x1=70, y1=70,
               line=dict(color='gray', dash='dash'))
fig2.update_traces(textposition='top center')
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Data table
st.subheader("Full State-Level Data")
st.dataframe(df.sort_values('dem_shift', ascending=False), use_container_width=True)