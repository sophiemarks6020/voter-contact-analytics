with base as (
    select
        year,
        state,
        state_po,
        county_name,
        party,
        sum(candidatevotes) as total_candidate_votes,
        max(totalvotes) as total_votes
    from {{ ref('stg_election') }}
    where year in (2016, 2020)
    and party in ('DEMOCRAT', 'REPUBLICAN')
    and mode = 'TOTAL'
    group by year, state, state_po, county_name, party
),

vote_share as (
    select
        year,
        state,
        state_po,
        county_name,
        party,
        total_votes,
        round(total_candidate_votes * 100.0 / total_votes, 2) as vote_share_pct
    from base
    where total_votes > 0
),

pivoted as (
    select
        state,
        state_po,
        county_name,
        max(case when year = 2016 and party = 'DEMOCRAT' then vote_share_pct end) as dem_2016,
        max(case when year = 2020 and party = 'DEMOCRAT' then vote_share_pct end) as dem_2020,
        max(case when year = 2016 and party = 'REPUBLICAN' then vote_share_pct end) as rep_2016,
        max(case when year = 2020 and party = 'REPUBLICAN' then vote_share_pct end) as rep_2020
    from vote_share
    group by state, state_po, county_name
)

select
    state,
    state_po,
    county_name,
    dem_2016,
    dem_2020,
    rep_2016,
    rep_2020,
    round(dem_2020 - dem_2016, 2) as dem_shift,
    round(rep_2020 - rep_2016, 2) as rep_shift
from pivoted
where dem_2016 is not null
and dem_2020 is not null
order by state, dem_shift desc