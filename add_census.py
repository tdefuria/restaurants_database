import pymysql
import csv

# csv filepaths here!!!
tracts_filepath = None
bgs_filepath = None
blocks_filepath = None
parcels_filepath = None

cnx = pymysql.connect(
    host='localhost',
    user='root',
    passwd='password',
    db='food_inspections'
)
c = cnx.cursor()

with open(tracts_filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute("""
            INSERT INTO census_tract (tract_id, census_year)
            VALUES (%s, %s)
        """, (row['CT_ID_10'], 2010))

print("Processed census tracts")

with open(bgs_filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute("""
            INSERT INTO census_block_group (block_group_id, census_year, tract_id)
            VALUES (%s, %s, %s)
        """, (row['BG_ID_10'], 2010, row['CT_ID_10']))
        
print("Processed census block groups")

with open(blocks_filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute("""
            INSERT INTO census_block (block_id, block_group_id, census_year)
            VALUES (%s, %s, %s)
        """, (row['Blk_ID_10'], row['BG_ID_10'], 2010))

print("Processed census blocks")


with open(parcels_filepath, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute("""
            INSERT IGNORE INTO land_parcel (land_parcel_id, gis_id, block_id)
            VALUES (%s, %s, %s)
        """, (row['Land_Parcel_ID'], row['GIS_ID'], row['Blk_ID_10']))

print("Processed land parcels")
print("Done!")
cnx.commit()
cnx.close()
