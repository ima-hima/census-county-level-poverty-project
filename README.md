# County-level poverty data
#### Task: Analyze census data income by county and state

1. Determine the top ten zipcodes most afflicted by poverty by grouping them by rate (expressed as a %) below poverty level.

    1. As an example, one dataset should be the top ten most impoverished zip codes in the United States based on the total percentage impacted. This might mean that low-income and low-population cities show up first, or that low-income high-population urban clusters show up—that is up to you to determine and prove your logic.

    1. Classify the poverty percentages into discrete buckets (e.g. 20–40% below poverty level, 40–60% below poverty level, etc.) and provide some analysis on the distribution of zipcodes in each bucket.

    1. Conduct a more detailed geographic analysis—determine which states have the highest proportions of impoverished zipcodes.

1. Create several tables in PostgreSQL to store this information in a simple and relational manner.

1. Conduct the analyses either directly in Python (and load the results to PostgreSQL), or load the raw data into PostgreSQL and write queries to analyze the data—determine and justify the better choice.

#### Implementation

As the project was short it was implemented as a single Python module which can be run directly from the terminal, as such `python import.py`. Information on state ANSI codes, which are returned from the census data is saved into an external csv file and imported separately. Link is [here](https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html). Please see the code for implementation-specific documentation/comments.

The project relies on the [census](https://github.com/datamade/census) library to access the census API.

The database consists of three tables, `states`, `zip_raw_data`, and `zip_stats`. 

As noted, `states` is available to be able to convert between ANSI state enumeration, state postal codes, and state names.

`zip_raw_data` hold the various data fields pulled from the census:

```sql
CREATE TABLE zip_raw_data (
    zipcode varchar(5) PRIMARY KEY,
    population INT,
    rent_as_pctg float,
    median_income INT,
    poverty_level float,
    state_id INT REFERENCES states (id)
)
```

`zip_stats` is provided as proof of concept and thus only has two example fields, one of which splits the zip codes into quintiles and one of which orders zips by descending level of poverty.

```sql
CREATE TABLE zip_stats
    AS
    SELECT
        zipcode,
        NTILE(5) OVER (ORDER BY poverty_level DESC) AS quintiles,
        DENSE_RANK() OVER (
            ORDER BY poverty_level DESC
        ) poverty_level_rank
    FROM zip_raw_data
```



#### Results

1. The query and results to find the ten zipcodes with the highest poverty are below. (n.b. Several zip codes were listed as having either 100% or 0% poverty rates. I did not remove those zip codes.)  

```sql
SELECT
      zip_stats.zipcode, 
      poverty_level_rank, 
      state_name 
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


1. The query and results to find the ten states with the highest proportion of zipcodes with high poverty—which I designated as having poverty rates >= 30—are below. (n.b. As above, several zip codes were listed as having either 100% or 0% poverty rates. I did not remove those zip codes.)  

```sql
SELECT state_name, high_poverty_count / count_all AS "percent high"
FROM
    (SELECT 
        state_id, 
        COUNT(zipcode)::float AS count_all
    FROM zip_raw_data
    GROUP BY state_id) AS zrd
    JOIN (SELECT 
              COUNT(zipcode)::float AS high_poverty_count, 
              state_id
          FROM zip_raw_data 
          WHERE poverty_level >= 25
          GROUP BY state_id) AS high_poverty
    ON high_poverty.state_id = zrd.state_id
    JOIN states ON states.id = zrd.state_id
ORDER BY "percent high" DESC
LIMIT 10;
```

|     state_name      |    percent high    |
|---------------------|--------------------|
|Puerto Rico          |               0.912|
|Alaska               | 0.29439252336448596|
|Mississippi          | 0.23237597911227154|
|New Mexico           |  0.2041522491349481|
|Kentucky             | 0.18664643399089528|
|Arizona              | 0.17819148936170212|
|West Virginia        | 0.16404886561954624|
|District of Columbia | 0.13636363636363635|
|Louisiana            | 0.12578616352201258|
|Alabama              |  0.1097972972972973|

#### Choices and justifications

1. Extra data was collected from the census in order for more complex analysis. Specifically, for each zipcode: 
    1. The total population
    1. Gross rent as a percentage of household income
    1. Median household income (dollars)
    1. Margin of error in poverty level: not currently collecting  

    For instance, by comparing the median household income against the current poverty rate ($26,500 for a family of four in 2020) or against the gross rent as a percentage of household, the relative strength of zip code-level poverty might be better indicated.

1. Rather than do any of the analyses in Python, I chose to do all the computation in the database. This was for two reasons: first, my expectation is that a data scientist, data analyst, or BI would be the final consumer of the data and they would interact directly with the database; second, as the world moves more and more to data warehouses and databases grow in size, doing intensive computation locally will not scale as well as doing the computation directly in the warehouse.


