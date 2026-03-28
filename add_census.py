import pymysql
import csv

# csv filepath here!!!
filepath = None

cnx = pymysql.connect(
    host='localhost',
    user='root',
    passwd='your_password',
    db='food_inspections'
)
c = cnx.cursor()

with open(filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute("""
            INSERT INTO census_tract (tract_id, census_year)
            VALUES (%s, %s)
        """, (row['CT_ID_10'], 2010))

cnx.commit()
cnx.close()
print("Done!")