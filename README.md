# Voter Analytics Dashboard

An end-to-end election analytics pipeline analyzing Democratic vote share shifts across all 50 U.S. states and every county between the 2016 and 2020 presidential elections.

**Live Dashboard:** [voter-analytics.streamlit.app](https://voter-analytics.streamlit.app)

---

## Project Overview

This project mirrors the analytical workflow of a progressive voter contact organization - ingesting raw election data, solving real data quality challenges, transforming it through a dbt pipeline, and surfacing actionable insights in an interactive deployed dashboard.

The analysis answers a core question voter contact organizations care about: **where did Democrats gain ground between 2016 and 2020, and what does that tell us about where to invest resources?**

---

## Tech Stack

- **DuckDB** - in-memory data warehouse
- **dbt** - data transformation and modeling (staging + mart layers)
- **Streamlit** - interactive dashboard, deployed on Streamlit Cloud
- **Plotly** - data visualization
- **Python** - pipeline orchestration
- **Data Source** - MIT Election Lab, County Presidential Election Returns 2000-2024

---

## Pipeline Architecture

---

## dbt Models

- `stg_election` - cleans raw CSV, handles nulls, calculates vote share percentage per candidate per county
- `mart_state_trends` - aggregates to state level using conditional logic to handle inconsistent vote reporting modes, pivots by year, calculates Democratic and Republican vote share shift and turnout change 2016 to 2020
- `mart_county_trends` - same conditional aggregation logic applied at the county level, enabling drill-down for all 50 states

---

## Key Data Challenge: Inconsistent Vote Reporting

A significant challenge in this dataset is that states report vote totals differently. Some states report a single unified TOTAL row per county. Others report breakdowns by voting mode (Election Day, Absentee, Early Vote, etc.) with no unified total.

Naively filtering to TOTAL rows excludes states like Georgia, Arizona, and Virginia. Naively summing all rows double-counts states that report both a TOTAL and breakdowns.

The solution uses conditional aggregation: states with clean TOTAL rows for both 2016 and 2020 use those directly. States missing TOTAL rows for either year have their breakdown modes summed across all parties to derive accurate totals. This ensures all 50 states are represented at both the state and county level.

---

## Dashboard Features

**State Overview Tab**
- KPI cards: states analyzed, average dem shift, states with gains, biggest gain
- Democratic vote share shift by state (2016 to 2020) - horizontal bar chart
- Voter turnout change by state - horizontal bar chart
- 2016 vs 2020 scatter plot with reference line, color coded by shift magnitude
- Turnout change vs dem shift correlation chart with OLS trendline
- Full state-level sortable data table
- Sidebar filters: All States, Swing States, Northeast, Midwest, South, West, or specific state selection

**County Deep Dive Tab**
- State selector with all 50 states
- Auto-generated analytical summary for each state
- Toggle between top 10 / bottom 10 counties and all counties
- County-level bar chart colored by dem shift
- County-level scatter plot (2016 vs 2020) with reference line
- Full county data table

---

## Key Findings

- Democrats gained vote share in all 50 states between 2016 and 2020, with an average shift of +3.71 percentage points
- Largest gains: Vermont (+8.80%), Colorado (+7.24%), Oregon (+6.38%)
- Key flipped states: Pennsylvania (+2.16%), Michigan (+3.35%), Wisconsin (+3.01%), Arizona (+4.80%), Georgia (+3.87%)
- Nationally, turnout growth shows a weak negative correlation with Democratic gains - persuasion drove more improvement than mobilization
- In swing states specifically, the correlation turns positive - mobilization in competitive states was more directly tied to Democratic gains
- Miami-Dade County, FL shifted Republican despite national trends, consistent with documented shifts among Latino voters

---

## How to Run Locally

1. Clone the repo
2. Install dependencies:
```bash
pip install duckdb dbt-core dbt-duckdb streamlit plotly pandas statsmodels
```
3. Download election data from [MIT Election Lab](https://electionlab.mit.edu/data) and place in `raw/election_data.csv`
4. Run the dbt pipeline:
```bash
cd voter_analysis
dbt run
```
5. Launch the dashboard:
```bash
streamlit run dashboard/app.py
```

---

## Author

Built by Sophie Marks as a portfolio project demonstrating SQL, dbt, data pipeline engineering, and data visualization skills for political analytics roles.

[voter-analytics.streamlit.app](https://voter-analytics.streamlit.app)