with clean_states as (
    select
        year,
        state,
        state_po,
        party,
        sum(candidatevotes) as total_candidate_votes,
        sum(totalvotes) as total_votes
    from {{ ref('stg_election') }}
    where year in (2016, 2020)
    and party in ('DEMOCRAT', 'REPUBLICAN')
    and mode = 'TOTAL'
    group by year, state, state_po, party
),

messy_states as (
    select
        year,
        state,
        state_po,
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
    group by year, state, state_po, party
),

messy_totals as (
    select
        year,
        state,
        sum(candidatevotes) as total_votes
    from {{ ref('stg_election') }}
    where year in (2016, 2020)
    and state in (select distinct state from messy_states)
    and mode != 'TOTAL'
    group by year, state
),

messy_combined as (
    select
        m.year,
        m.state,
        m.state_po,
        m.party,
        m.total_candidate_votes,
        t.total_votes
    from messy_states m
    join messy_totals t
        on m.state = t.state
        and m.year = t.year
),

combined as (
    select * from clean_states
    union all
    select * from messy_combined
),

vote_share as (
    select
        year,
        state,
        state_po,
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
        max(case when year = 2016 and party = 'DEMOCRAT' then vote_share_pct end) as dem_2016,
        max(case when year = 2020 and party = 'DEMOCRAT' then vote_share_pct end) as dem_2020,
        max(case when year = 2016 and party = 'REPUBLICAN' then vote_share_pct end) as rep_2016,
        max(case when year = 2020 and party = 'REPUBLICAN' then vote_share_pct end) as rep_2020,
        max(case when year = 2016 then total_votes end) as total_votes_2016,
        max(case when year = 2020 then total_votes end) as total_votes_2020
    from vote_share
    group by state, state_po
)

select
    state,
    state_po,
    dem_2016,
    dem_2020,
    rep_2016,
    rep_2020,
    round(dem_2020 - dem_2016, 2) as dem_shift,
    round(rep_2020 - rep_2016, 2) as rep_shift,
    total_votes_2020 - total_votes_2016 as turnout_change
from pivoted
where dem_2016 is not null
and dem_2020 is not null
order by dem_shift desc