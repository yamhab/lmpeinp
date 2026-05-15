import csv
import pathlib
import sqlite3
import sys


CSV_FILENAME = "Elk_Island_NP_Grassland_Forest_Ungulate_Population_1906-2017_data_reg.csv"
DB_FILENAME = "populations.db"


def main() -> None:
    con = sqlite3.connect(DB_FILENAME)
    cur = con.cursor()
    import_csv(con, cur)
    menu(con, cur)
    con.close()


def import_csv(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
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
    if data in {"NA", ""}:
        return None
    if data.isdigit():
        return int(data)
    return data


def menu(con: sqlite3.Connection, cur: sqlite3.Cursor) -> None:
    prompt = ""
    while len(prompt) == 0 or prompt[0].lower() != "q":
        prompt = input(
            "Would you like to (d)etermine population growth or (q)uit the program? ",
        )
        if len(prompt) == 0:
            continue
        match prompt[0].lower():
            case "d":
                print()
                growth(cur)


def growth(cur: sqlite3.Cursor) -> None:
    try:
        start_year = int(input("Starting year of period? "))
        end_year = int(input("Ending year of period? "))
        if start_year >= end_year:
            raise ValueError

        species = int(
            input("Mammal population to analyze (1: Bison, 2: Deer, 3: Elk, 4: Moose, 5: All)? ")
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
            "Not enough data available to calculate rate of population change over given period!\n"
        )


def show_year(cur: sqlite3.Cursor, year: int, species: str) -> int | None:
    if species == "All":
        cur.execute(
            "SELECT park_area, fall_estimate, survey_comment, estimation_method FROM populations WHERE population_year = ? AND species_name IN ('Bison', 'Deer', 'Elk', 'Moose')",
            (year,),
        )
    else:
        cur.execute(
            "SELECT park_area, fall_estimate, survey_comment, estimation_method FROM populations WHERE population_year = ? AND species_name = ?",
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
            print(f"Survey comment for {year} in the {row[0]}: {row[2]}")

    if population != 0:
        print(f"Total population of {species} during {year}: {population} ({method})")
        return population
    return None


if __name__ == "__main__":
    main()
