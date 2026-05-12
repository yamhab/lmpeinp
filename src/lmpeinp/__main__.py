import csv
import pathlib
import sqlite3


CSV_FILENAME = "Elk_Island_NP_Grassland_Forest_Ungulate_Population_1906-2017_data_reg.csv"
DB_FILENAME = "populations.db"


def main() -> None:
    con = sqlite3.connect(DB_FILENAME)
    cur = con.cursor()
    import_csv(con, cur)


def import_csv(con, cur):
    with pathlib.Path(CSV_FILENAME).open() as file:
        reader = csv.DictReader(file)
        cur.execute(
            "CREATE TABLE IF NOT EXISTS populations(park_area, population_year, survey_year, survey_month, survey_day, species_name, unknown_age_count, male_count, female_count, unknown_sex_count, yearling_count, calf_count, survey_total, correction_factor, captive_factor, removed_prior, fall_estimate, survey_comment, estimation_method)",
        )
        data = [
            (
                row["Area of park"],
                int(row["Population year"]),
                None if row["Survey Year"] == "NA" else int(row["Survey Year"]),
                None if row["Survey Month"] == "NA" else int(row["Survey Month"]),
                None if row["Survey Day"] == "NA" else int(row["Survey Day"]),
                row["Species name"],
                None
                if row["Unknown age and sex count"] == "NA"
                else int(row["Unknown age and sex count"]),
                None if row["Adult male count"] == "NA" else int(row["Adult male count"]),
                None if row["Adult female count"] == "NA" else int(row["Adult female count"]),
                None
                if row["Adult unknown count"] == "NA" or row["Adult unknown count"] == ""
                else int(row["Adult unknown count"]),
                None if row["Yearling count"] == "NA" else int(row["Yearling count"]),
                None if row["Calf count"] == "NA" else int(row["Calf count"]),
                None if row["Survey total"] == "NA" else int(row["Survey total"]),
                None
                if row["Sightability correction factor"] == "NA"
                else float(row["Sightability correction factor"]),
                None
                if row["Additional captive count"] == "NA"
                else int(row["Additional captive count"]),
                None
                if row["Animals removed prior to survey"] == "NA"
                else int(row["Animals removed prior to survey"]),
                None
                if row["Fall population estimate"] == "NA"
                else int(row["Fall population estimate"]),
                None if row["Survey comment"] == "" else row["Survey comment"],
                None if row["Estimate method"] == "NA" else row["Estimate method"],
            )
            for row in reader
        ]
        cur.executemany(
            "INSERT INTO populations VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            data,
        )
        con.commit()


if __name__ == "__main__":
    main()
