"""Large Mammal Populations Elk Island National Park."""

import csv
import pathlib
import sqlite3
import sys


CSV_FILENAME = "Elk_Island_NP_Grassland_Forest_Ungulate_Population_1906-2017_data_reg.csv"
DB_FILENAME = "populations.db"


def main() -> None:
    """Program's Entry point."""
    con = sqlite3.connect(DB_FILENAME)
    cur = con.cursor()
    import_csv(con, cur)
    menu(con, cur)
    con.close()


def import_csv(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """Look for the population data CSV file, and create an appropriate SQL database using it."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='populations'")
    if cur.fetchone() is not None:
        print("Using existing database's population data...")
        return

    print("Importing population data from CSV file into database...")
    path = pathlib.Path(CSV_FILENAME)
    if not path.exists():
        sys.exit(f"CSV file ({CSV_FILENAME}) cannot be found!")

    with path.open() as file:
        reader = csv.reader(file)
        cur.execute(
            """CREATE TABLE populations(
                park_area,
                population_year,
                survey_year,
                survey_month,
                survey_day,
                species_name,
                unknown_age_count,
                male_count,
                female_count,
                unknown_sex_count,
                yearling_count,
                calf_count,
                survey_total,
                correction_factor,
                captive_count,
                removed_prior,
                fall_estimate,
                survey_comment,
                estimation_method
            )""",
        )
        data = [tuple(nullify(cell) for cell in row) for row in reader]
        placeholders = ", ".join(["?"] * len(data[0]))
        cur.executemany(f"INSERT INTO populations VALUES({placeholders})", data)
        con.commit()


def nullify(data: str) -> str | int | None:
    """Convert a Python value into its SQL counterpart."""
    if data in {"NA", ""}:
        return None
    if data.isdigit():
        return int(data)
    return data


def menu(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """Go through the program's main menu."""
    prompt = ""
    while len(prompt) == 0 or prompt[0].lower() != "q":
        prompt = input(
            "Would you like to (s)how population growth, (a)dd new data to the database, (d)elete \
a year's population data, or (q)uit the program? ",
        )
        if len(prompt) == 0:
            continue
        match prompt[0].lower():
            case "s":
                print()
                growth(cur)
            case "a":
                print()
                add(con, cur)
            case "d":
                print()
                delete(con, cur)


def growth(cur: sqlite3.Cursor) -> None:
    """Ask the user for what years and species to look for and analyze the data."""
    try:
        start_year = int(input("Starting year of period? "))
        end_year = int(input("Ending year of period? "))
        if start_year >= end_year:
            raise ValueError

        species = int(
            input("Mammal population to analyze (1: Bison, 2: Deer, 3: Elk, 4: Moose, 5: All)? "),
        )
        match species:
            case 1:
                species = "Bison"
            case 2:
                species = "Deer"
            case 3:
                species = "Elk"
            case 4:
                species = "Moose"
            case 5:
                species = "All"
            case _:
                raise ValueError
    except ValueError:
        print("Error detected in provided inputs!")
        return
    print()

    start_population = show_year(cur, start_year, species)
    end_population = show_year(cur, end_year, species)
    if start_population is not None and end_population is not None:
        rate = int(round((end_population - start_population) / (end_year - start_year), 0))
        print(f"Approximate rate of change ({start_year}-{end_year}): {rate} {species}/year\n")
    else:
        print(
            "Not enough data available to calculate rate of population change over given period!\n",
        )


def show_year(cur: sqlite3.Cursor, year: int, species: str) -> int | None:
    """Search the database for the provided data and interpret it."""
    if species == "All":
        cur.execute(
            "SELECT park_area, fall_estimate, survey_comment, estimation_method FROM populations \
WHERE population_year = ? AND species_name IN ('Bison', 'Deer', 'Elk', 'Moose')",
            (year,),
        )
    else:
        cur.execute(
            "SELECT park_area, fall_estimate, survey_comment, estimation_method FROM populations \
WHERE population_year = ? AND species_name = ?",
            (year, species),
        )

    rows = cur.fetchall()
    if len(rows) == 0:
        print(f"{species} population data not present during {year}")

    population = 0
    for row in rows:
        if row[1] is None:
            print(f"{species} population data not present during {year} in the {row[0]}")
        else:
            population += row[1]
            method = row[3]

        if row[2] is not None:
            print(f"Survey comment for {year} in the {row[0]}: '{row[2]}'")

    if population != 0:
        print(f"Total population of {species} during {year}: {population} ({method})")
        return population
    return None


def add(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """Add a new population data entry to the database using user-provided input."""
    try:
        population_year = int(input("Population year? "))

        species_name = int(input("Species of mammal (1: Bison, 2: Deer, 3: Elk, 4: Moose)? "))
        match species_name:
            case 1:
                species_name = "Bison"
            case 2:
                species_name = "Deer"
            case 3:
                species_name = "Elk"
            case 4:
                species_name = "Moose"
            case _:
                raise ValueError

        fall_estimate = int(input("Population estimate? "))
        if fall_estimate < 0:
            raise ValueError

        print("For the following optional values, leave empty to skip.")

        park_area = input("Area of park (1: North, 2: South? ")
        match park_area:
            case "1":
                park_area = "North"
            case "2":
                park_area = "South"
            case _:
                park_area = None

        survey_year = input("Survey year? ")
        survey_year = int(survey_year) if survey_year != "" else None

        survey_month = input("Survey month? ")
        survey_month = int(survey_month) if survey_month != "" else None
        if survey_month is not None and 1 > survey_month > 12:
            raise ValueError

        survey_day = input("Survey day? ")
        survey_day = int(survey_day) if survey_day != "" else None
        if survey_day is not None and 1 > survey_day > 31:
            raise ValueError

        unknown_age_count = input("Unknown age count? ")
        unknown_age_count = int(unknown_age_count) if unknown_age_count != "" else None
        if unknown_age_count is not None and unknown_age_count < 0:
            raise ValueError

        male_count = input("Adult male count? ")
        male_count = int(male_count) if male_count != "" else None
        if male_count is not None and male_count < 0:
            raise ValueError

        female_count = input("Adult female count? ")
        female_count = int(female_count) if female_count != "" else None
        if female_count is not None and female_count < 0:
            raise ValueError

        unknown_sex_count = input("Adult unknown sex count? ")
        unknown_sex_count = int(unknown_sex_count) if unknown_sex_count != "" else None
        if unknown_sex_count is not None and unknown_sex_count < 0:
            raise ValueError

        yearling_count = input("Yearling count? ")
        yearling_count = int(yearling_count) if yearling_count != "" else None
        if yearling_count is not None and yearling_count < 0:
            raise ValueError

        calf_count = input("Calf count? ")
        calf_count = int(calf_count) if calf_count != "" else None
        if calf_count is not None and calf_count < 0:
            raise ValueError

        survey_total = input("Survey total? ")
        survey_total = int(survey_total) if survey_total != "" else None
        if survey_total is not None and survey_total < 0:
            raise ValueError

        correction_factor = input("Sightability correction factor? ")
        correction_factor = float(correction_factor) if correction_factor != "" else None
        if correction_factor is not None and correction_factor < 1:
            raise ValueError

        captive_count = input("Captive count? ")
        captive_count = int(captive_count) if captive_count != "" else None
        if captive_count is not None and captive_count < 0:
            raise ValueError

        removed_prior = input("Animals removed prior to survey? ")
        removed_prior = int(removed_prior) if removed_prior != "" else None
        if removed_prior is not None and removed_prior < 0:
            raise ValueError

        survey_comment = input("Survey Comment? ")
        if survey_comment == "":
            survey_comment = None

        estimation_method = input("Estimation method? ")
        if estimation_method == "":
            estimation_method = None
    except ValueError:
        print("Error detected in provided inputs!")
        return

    row = (
        park_area,
        population_year,
        survey_year,
        survey_month,
        survey_day,
        species_name,
        unknown_age_count,
        male_count,
        female_count,
        unknown_sex_count,
        yearling_count,
        calf_count,
        survey_total,
        correction_factor,
        captive_count,
        removed_prior,
        fall_estimate,
        survey_comment,
        estimation_method,
    )
    cur.execute(f"INSERT INTO populations VALUES({', '.join(['?'] * 19)})", row)
    con.commit()
    print()


def delete(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    """Delete a year's worth of populations from the database of the user's choice."""
    try:
        year = int(
            input(
                "Which year's worth of populations data would you like to have deleted from the \
database? ",
            ),
        )
    except ValueError:
        print("Error detected in provided inputs!")
        return
    print()

    cur.execute("DELETE FROM populations WHERE population_year = ?", (year,))
    print(
        f"Deleted {cur.rowcount} sets of populations matching population year {year} from the \
database",
    )
    con.commit()
    print()


if __name__ == "__main__":
    main()
