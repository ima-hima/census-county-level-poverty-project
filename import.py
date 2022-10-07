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


# API_CALL = (
#     "https://api.census.gov/data/2020/acs/acs5/profile?get=NAME,DP03_0119PE"
#     f"&for=zip%20code%20tabulation%20area:*&key={API_KEY}"
# )

# Collecting info on these variables
# DP05_0001PE Total population
# DP04_0136PE Gross rent as a percentage of household income
# DP03_0062E Median household income (dollars)
# DP03_0119PE Percentage of families and people whose income in the past 12
#             months is below the poverty level

# Note that for data
# # profile tables must use Census.acs5db() and not Census.acs5().
table = c.acs5dp.get(
    ("DP05_0001PE", "DP04_0136PE", "DP03_0062E", "DP03_0119PE"),
    {"for": "zip code tabulation area:*"},
)
# print(table)
# for i, row in enumerate(table):
#     print(i, row["DP03_0119PE"], row["state"], row["zip code tabulation area"])

# The following imports data to translate numeric state identifiers into
# state names (or, if needed postal abbreviations). The data came from here:
# https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
with open(
    (
        "/Users/eric/Documents/workspace_git/census-county-level-poverty-project/"
        "state codes.csv"
    ),
    "r",
) as states_in:
    states = csv.DictReader(states_in, delimiter=",", quotechar='"')
    state_lookup = {s["value"]: s["name"] for s in states}
# print(state_lookup)

with open(
    "/Users/eric/Documents/workspace_git/census-county-level-poverty-project/zips.csv",
    "w",
) as zips:
    zip_writer = csv.writer(
        zips, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
    )
    zip_writer.writerow(
        [
            "Total population",
            "Gross rent as a percentage of household income",
            "Median household income (dollars)",
            "Percent below poverty line",
            "STATE",
            "zipcode",
        ]
    )
    for row in table:
        if (
            row["DP05_0001PE"] != "0.0"
            and row["DP03_0119PE"] != -666666666.0
            and row["DP03_0062E"] != -666666666.0
        ):
            zip_writer.writerow(
                [
                    row["DP05_0001PE"],
                    row["DP04_0136PE"],
                    row["DP03_0062E"],
                    row["DP03_0119PE"],
                    state_lookup[row["state"]],
                    row["zip code tabulation area"],
                ]
            )

# with psycopg.connect(f"dbname={PSQL_DATABASE_NAME} user=postgres password={PSQL_PW}") as conn:
#     # Open a cursor to perform database operations
#     with conn.cursor() as cur:
#         # Execute a command: this creates a new table
#         cur.execute(
#             "DROP TABLE IF EXISTS poverty_zips"
#         )
#         cur.execute(
#             """
#             CREATE TABLE poverty_zips (
#                 id serial PRIMARY KEY,
#                 poverty_level float,
#                 zipcode integer UNIQUE,
#                 decile integer,
#                 state varchar(15)
#             )
#             PARTITION BY RANGE (decile)
#             """
#         )
#         # cur.execute("CREATE INDEX zip_idx ON poverty_zips (zipcode)")


# by state: proportion per state
# by zip: percent < poverty, median household income, rent as percent of income
#         total population
