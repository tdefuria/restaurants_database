from shiny import reactive, req
from shiny import render as core_render
from shiny import ui as core_ui
import faicons as fa
import pymysql
import pandas as pd
import matplotlib.pyplot as plt


login=True
while login:
    try:
        cnx = pymysql.connect(host='localhost', user='root', password='TandemBicycle78!', db='food_inspections', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    except pymysql.err.OperationalError:
        print("Username and password denied.  Please try again")
        user=input("Enter your username")
        pw=input("Enter valid password")
        continue
    login = False

def close_connection_quit():
    cnx.close()
    print("Disconnected ...")
    print("Goodbye")
    quit()

def populate_search_options():
    conn = cnx
    query ="CALL get_all_restaurants_search_options()"
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
    df = pd.DataFrame(results)
    cols = df.columns
    df['option'] = df[cols].astype(str).apply(lambda row: str(row.iloc[0]) + ' : ' + ', '.join(row.iloc[1:]), axis=1)
    option_list = df['option'].tolist()
    print(option_list)
    return option_list

working = True
populate_search_options()
while working:
    menu_opt = input("Did it work? Take a second to decide 0 for no, 1 for yes, q for quit.")
    match menu_opt:
        case '0':
            print("Ok, lets try again.")
            print(populate_search_options())
        case '1':
            print("Hooray!")
            close_connection_quit()
            working = False
        case 'q':
            close_connection_quit()
            working = False
        case _:
            print('You must choose')
            continue
