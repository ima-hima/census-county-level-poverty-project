from census import Census
import csv
from us import states
import psycopg
from dotenv import load_dotenv
from os import getenv

load_dotenv(override=True)

API_KEY = getenv("CENSUS_API_KEY")
PSQL_PW = getenv("PSQL_PASSWORD")
PSQL_DATABASE_NAME = getenv("PSQL_DATABASE_NAME")

c = Census(API_KEY, year=2019)  # 2020 returns nulls for the state.

# Collecting info on these variables
# DP05_0001PE Total population
# DP04_0136PE Gross rent as a percentage of household income
# DP03_0062E Median household income (dollars)
# DP03_0119PE Percentage of families and people whose income in the past 12
#             months is below the poverty level
# DP03_0119PM -- Margin of error in poverty level: not currently collecting

# Note that for data profile tables we must use Census.acs5db() and not Census.acs5().
# table = c.acs5dp.get(
#     ("DP05_0001PE", "DP04_0136PE", "DP03_0062E", "DP03_0119PE"),
#     {"for": "zip code tabulation area:*"},
# )
# print(table)
# for i, row in enumerate(table):
#     print(i, row["DP03_0119PE"], row["state"], row["zip code tabulation area"])

# The following imports data to translate numeric state identifiers into
# state names (or, if needed postal abbreviations). The data came from here:
# https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
with open(
    (
        "/Users/eric/Documents/workspace_git/census-county-level-poverty-project/"
        "state_codes.csv"
    ),
    "r",
) as states_in:
    states = csv.DictReader(states_in, delimiter=",", quotechar='"')
    states_to_insert = [(s["value"], s["name"], s["abbreviation"]) for s in states]


# with open(
#     "/Users/eric/Documents/workspace_git/census-county-level-poverty-project/zips.csv",
#     "w",
# ) as zips:
#     zip_writer = csv.writer(
#         zips, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
#     )
#     zip_writer.writerow(
#         [
#             "Total population",
#             "Gross rent as a percentage of household income",
#             "Median household income (dollars)",
#             "Percent below poverty line",
#             "STATE",
#             "zipcode",
#         ]
#     )
#     for row in table:
#         if (
#             row["DP05_0001PE"] != "0.0"
#             and row["DP03_0119PE"] >= 0
#             and row["DP03_0062E"] >= 0
#         ):
#             # Throwing out bad data, which comes back as negative numbers.
#             # Consider margin of error here? Some zips return 0% or 100%
#             # poverty levels. Including those for now.
#             zip_writer.writerow(
#                 [
#                     row["DP05_0001PE"],
#                     row["DP04_0136PE"],
#                     row["DP03_0062E"],
#                     row["DP03_0119PE"],
#                     row["state"],
#                     row["zip code tabulation area"],
#                 ]
#             )

with open(
    (
        "/Users/eric/Documents/workspace_git/census-county-level-poverty-project/"
        "zips.csv"
    ),
    "r",
) as zips_in:
    zips = csv.DictReader(zips_in, delimiter=",", quotechar='"')
    zips_to_insert = [
        (
            z["zipcode"],
            int(float(z["Total population"])),
            z["Gross rent as a percentage of household income"],
            int(float(z["Median household income (dollars)"])),
            z["Percent below poverty line"],
            z["STATE"],
        )
        for z in zips
    ]


with psycopg.connect(
    f"dbname={PSQL_DATABASE_NAME} user=postgres password={PSQL_PW}"
) as conn:
    # Open a cursor to perform database operations
    with conn.cursor() as cur:
        # Create state_ids table to translate from numeric IDs returned from
        # census to text. Both state name and postal code are stored.
        cur.execute("DROP TABLE IF EXISTS states CASCADE")
        cur.execute(
            """
            CREATE TABLE states (
                id INT PRIMARY KEY,
                name varchar(50),
                abbreviation varchar(2)
            )
            """
        )
        insert_sql = "INSERT INTO states (id, name, abbreviation)" "VALUES (%s, %s, %s)"
        cur.executemany(insert_sql, states_to_insert)

        # Now create table of raw data.
        cur.execute("DROP TABLE IF EXISTS zip_raw_data CASCADE")
        cur.execute(
            """
            CREATE TABLE zip_raw_data (
                zipcode varchar(5) PRIMARY KEY,
                population INT,
                rent_as_pctg float,
                median_income INT,
                poverty_level float,
                state_id INT REFERENCES states (id)
            )
            """
        )
        insert_sql = (
            "INSERT INTO zip_raw_data (zipcode, population, "
            "rent_as_pctg, median_income, poverty_level, state_id)"
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        cur.executemany(insert_sql, zips_to_insert)

        # Finally, create table with various stats.
        # Currently, this breaks
        cur.execute("DROP TABLE IF EXISTS zip_stats")
        cur.execute(
            """
            CREATE TABLE zip_stats
            AS
            SELECT
                zipcode,
                NTILE(5) OVER (ORDER BY poverty_level DESC) AS quintiles,
                DENSE_RANK() OVER (
                    ORDER BY poverty_level DESC
                ) poverty_level_rank
            FROM zip_raw_data
            """
        )

# poverty level family of four: 26500


# by state: proportion per state
# by zip: percent < poverty, median household income, rent as percent of income
#         total population
