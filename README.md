# Voter Contact Effectiveness Dashboard

An end-to-end election analytics pipeline built to analyze Democratic 
vote share shifts across U.S. states between the 2016 and 2020 
presidential elections.

## Project Overview

This project mirrors the analytical workflow of a progressive data 
organization — ingesting raw election data, transforming it through 
a dbt pipeline, and surfacing insights in an interactive dashboard.

## Tech Stack

- **DuckDB** — local data warehouse
- **dbt** — data transformation and modeling
- **Streamlit** — interactive dashboard
- **Plotly** — data visualization
- **Python** — pipeline orchestration
- **Data Source** — MIT Election Lab, County Presidential Election 
Returns 2000–2024

## Pipeline Architecture

## dbt Models

- `stg_election` — cleans raw CSV, handles nulls, calculates 
vote share percentage per candidate per county
- `mart_state_trends` — aggregates to state level, pivots by year, 
calculates Democratic and Republican vote share shift 2016→2020

## Key Findings

- Democrats gained vote share in all 41 states analyzed
- Largest gains: Vermont (+8.8%), Colorado (+7.2%), Oregon (+6.4%)
- Key flipped states clearly visible: Pennsylvania (+2.2%), 
Michigan (+3.4%), Wisconsin (+3.0%)
- Florida showed minimal shift (+0.04%) — a perennial battleground

## How to Run

1. Clone the repo
2. Install dependencies:
```bash
   pip install duckdb dbt-core dbt-duckdb streamlit plotly
```
3. Download election data from MIT Election Lab and place in `raw/`
4. Run the dbt pipeline:
```bash
   cd voter_analysis
   dbt run
```
5. Launch the dashboard:
```bash
   streamlit run dashboard/app.py
```

## Author

Built as a portfolio project demonstrating SQL, dbt, and data 
visualization skills for political analytics roles.

