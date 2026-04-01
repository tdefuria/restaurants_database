from shiny import reactive, req
from shiny import render as core_render
from shiny import ui as core_ui
import faicons as fa
import pymysql
import pandas as pd
import matplotlib.pyplot as plt

password = 'your_password'

def establish_connection():
    try:
        cnx = pymysql.connect(host='localhost', user='root', password=password, db='food_inspections',
                              charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        return cnx
    except pymysql.err.OperationalError:
        print("Username and password denied.  Please try again")
        user = input("Enter your username")
        pw = input("Enter valid password")
        return


def query_for_dict(query, cnx):
    conn = cnx
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute(query)
        result = cur.fetchall()
    return result

def close_connection_quit(cnx):
    cnx.close()
    print("Disconnected ...")
    print("Goodbye")
    quit()

def populate_search_options(cnx):
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

"""working = True
populate_search_options(cnx)
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
            continue"""

def concatenate_restaurant_results(result_list):
    if result_list == []:
        return None
    option_list = []
    for i in range(len(result_list)):
        result_dict = result_list[i]
        print(f'result_dict: {result_dict}')
        option = f"{result_dict.get('business_name', 'No business name')}"
        option += f" : {result_dict.get('street_num', 'No street')}"
        option += f" {result_dict.get('city', 'No city')}"
        option_list.append(option)
    return option_list

def main():
    print("Hello world")
    cnx = establish_connection()
    result_list = query_for_dict("CALL get_all_restaurants_search_options()", cnx)
    print(concatenate_restaurant_results(result_list))

    close_connection_quit(cnx)

if __name__ == "__main__":
    main()