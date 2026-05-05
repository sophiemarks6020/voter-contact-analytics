with clean_counties as (
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

messy_counties as (
    select
        year,
        state,
        state_po,
        county_name,
        party,
        sum(candidatevotes) as total_candidate_votes
    from {{ ref('stg_election') }}
    where year in (2016, 2020)
    and party in ('DEMOCRAT', 'REPUBLICAN')
    and state in (
        select state from (
            select state, year
            from {{ ref('stg_election') }}
            where mode = 'TOTAL'
            and year in (2016, 2020)
            group by state, year
        ) t
        group by state
        having count(distinct year) < 2
    )
    and mode != 'TOTAL'
    group by year, state, state_po, county_name, party
),

messy_county_totals as (
    select
        year,
        state,
        county_name,
        sum(candidatevotes) as total_votes
    from {{ ref('stg_election') }}
    where year in (2016, 2020)
    and state in (select distinct state from messy_counties)
    and mode != 'TOTAL'
    group by year, state, county_name
),

messy_combined as (
    select
        m.year,
        m.state,
        m.state_po,
        m.county_name,
        m.party,
        m.total_candidate_votes,
        t.total_votes
    from messy_counties m
    join messy_county_totals t
        on m.state = t.state
        and m.year = t.year
        and m.county_name = t.county_name
),

combined as (
    select * from clean_counties
    union all
    select * from messy_combined
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
    from combined
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