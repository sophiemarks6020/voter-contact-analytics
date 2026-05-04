with source as (
    select * from read_csv_auto(
        'C:/Users/13609/voter_contact_analysis/raw/election_data.csv',
        nullstr='NA',
        sample_size=-1
    )
),

staged as (
    select
        year,
        state,
        state_po,
        county_name,
        candidate,
        party,
        mode,
        candidatevotes,
        totalvotes,
        round(candidatevotes * 100.0 / totalvotes, 2) as vote_share_pct
    from source
    where totalvotes > 0
    and candidatevotes is not null
)

select * from staged