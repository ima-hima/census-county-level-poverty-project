# County-level poverty data
#### Analyze census data income by county and state

1. Determine the top ten zipcodes most afflicted by poverty by grouping them by rate (expressed as a %) below poverty level.

    1. As an example, one dataset should be the top ten most impoverished zip codes in the United States based on the total percentage impacted. This might mean that low-income and low-population cities show up first, or that low-income high-population urban clusters show up—that is up to you to determine and prove your logic.

    1. Classify the poverty percentages into discrete buckets (e.g. 20–40% below poverty level, 40–60% below poverty level, etc.) and provide some analysis on the distribution of zipcodes in each bucket.

    1. Conduct a more detailed geographic analysis—determine which states have the highest proportions of impoverished zipcodes.

1. Create several tables in PostgreSQL to store this information in a simple and relational manner.

1. Conduct the analyses either directly in Python (and load the results to PostgreSQL), or load the raw data into PostgreSQL and write queries to analyze the data—determine and justfy the better choice.

#### Implementation

As the project was short it was implemented as a single Python module which can be run directly from the terminal, as such `python import.py`.

#### Results

1. The ten zipcodes with the highest levels of poverty are (n.b. several zip codes were listed as having either 100% or 0% poverty rates. I did not remove those zip codes.). The query and results are below.

```sql
SELECT
      zip_stats.zipcode, 
      poverty_level_rank, 
      name 
FROM zip_stats 
     JOIN zip_raw_data ON zip_stats.zipcode = zip_raw_data.zipcode 
     JOIN states ON zip_raw_data.state_id = states.id
LIMIT 10;
```


|zipcode | rank | state | 
|--------|:----:|-------|
|38630   | 1    | Mississippi |
|71659   | 1    | Arkansas |
|95443   | 1    | California |
|22548   | 1    | Virginia |
|44503   | 1    | Ohio |
|01009   | 1    | Massachusetts |
|26348   | 1    | West Virginia |
|41845   | 2    | Kentucky |
|40997   | 3    | Kentucky |
|62523   | 4    | Illinois |

#### Choices and justifications

1. Extra data was collected from the census in order for more complex analysis. Specifically, for each zipcode: 
    1. The total population
    1. Gross rent as a percentage of household income
    1. Median household income (dollars)
    1. Margin of error in poverty level: not currently collecting  

    For instance, by comparing the median household income against the current poverty rate ($26,500 for a family of four in 2020) or against the gross rent as a percentage of household, the relative strength of zip code-level poverty might be better indicated.

1. Rather than do any of the analyses in Python, I chose to do all the computation in the database. This was for two reasons: first, my expectation is that a data scientist, data analyst, or BI would be the final consumer of the data and they would interact directly with the database; second, as the world moves more and more to data warehouses and databases grow in size, doing intensive computation locally will not scale as well as doing the computation directly in the warehouse.


