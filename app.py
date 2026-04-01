
from shiny import reactive, req
from shiny.express import input, render, ui
import faicons as fa
import pymysql as sql
import pandas as pd
import matplotlib.pyplot as plt

# save value for database connection
cnx = reactive.Value(None)

# helper function for calling processes in value cards
def call_proc(proc_name):
    conn = cnx()
    if conn is None:
        return ""
    c = conn.cursor()
    c.callproc(f'food_inspections.{proc_name}')
    return str(c.fetchone()[0])


# helper function for calling procedures that would return dataframes
def query_for_df(query):
    conn = cnx()
    if conn is None:
        return
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall() # to get every line returned
        # because the columns are included in the description.
        # although I can't find documentation in pymysql cursor objects for cur.description,
        # this stack overflow post has it and I tested that
        # 1 it causes error from column not found without this line
        # 2 it contains the columns with their appropriate names with this
        # https://stackoverflow.com/questions/12704305/return-column-names-from-pyodbc-execute-statement#:~:text=4%20Answers,3%20Comments
        columns = [description[0] for description in cur.description]
    return pd.DataFrame(results, columns=columns)

# title banner - top of screen
ui.page_opts(
    title="Boston Restaurants: Inspections and Reviews", fillable=False)


# Action button - database log-in
ui.input_action_button("login", "Login to database")

# modal pop-up for database login
# input is the action that triggers the event
# login is the id for the input action button
@reactive.effect
@reactive.event(input.login)
def show_login_modal():
    m = ui.modal(
        ui.input_text("name", "Username:"),
        ui.input_password("password", "Password:"),
        ui.input_action_button("connect", "Connect"),
        title="Database Credentials",
        easy_close=True,
        footer=None,
    )
    ui.modal_show(m)

# mysql connection attempt
@reactive.effect
@reactive.event(input.connect)
def connect_to_database():
    try:
        connection = sql.connect(
            host='localhost', user=input.name(), passwd=input.password(),
            db='food_inspections', charset='utf8mb4'
        )
        cnx.set(connection)  # store it globally
        ui.modal_remove()
        m = ui.modal(title="Connection successful!", easy_close=True, footer=None)
        ui.modal_show(m)

    except sql.err.OperationalError:
        m = ui.modal(title="Connection failed", easy_close=True, footer=None)
        ui.modal_show(m)

# two tabs: Overview and Restaurant Search
with ui.navset_pill(id="selected_navset_pill"):
    # Overview dashboard tab
    with ui.nav_panel("Overview"):

        ICONS = {"utensils": fa.icon_svg("utensils"),
                 "clipboard": fa.icon_svg("clipboard"),
                 "yelp": fa.icon_svg("yelp"),
                 "star": fa.icon_svg("star"),
                 "triangle-exclamation": fa.icon_svg("triangle-exclamation")
                 }

        with ui.layout_columns(fill=False):

            # summary value boxes: total restaurants
            with ui.value_box(showcase=ICONS["utensils"]):
                "Total restaurants"

                @render.text
                def total_restaurants():
                    return call_proc('get_restaurant_count')

            # value box: total inspections
            with ui.value_box(showcase=ICONS["clipboard"]):
                "Total health inspections"

                @render.text
                def total_health_inspections():
                    return call_proc('get_inspection_count')

            # value box: total reviews
            with ui.value_box(showcase=ICONS["yelp"]):
                "Total reviews"

                @render.text
                def total_reviews():
                    return call_proc('get_review_count')

            # value box: average rating
            with ui.value_box(showcase=ICONS["star"]):
                "Average rating per restaurant"

                @render.text
                def avg_rating():
                    return call_proc('get_avg_rating')

            # value box: average violations per inspection
            with ui.value_box(showcase=ICONS["triangle-exclamation"]):
                "Average violations per inspection"

                @render.text
                def avg_violations():
                    return call_proc('get_avg_violations_per_inspection')

        with ui.layout_columns(fill=False):

            # plot of violations per level
            with ui.card():
                ui.card_header("Violations by Level")

                @render.plot
                def violations_by_level():
                    conn = cnx()
                    if conn is None:
                        return
                    df = query_for_df("CALL food_inspections.get_violations_by_level()")
                    fig, ax = plt.subplots()
                    ax.bar(df['violation_level'], df['count'])
                    ax.set_title('Health and Safety Violations by Level')
                    ax.set_xlabel('Violation Level')
                    ax.set_ylabel('Count')
                    description = (
                        "Level 1: Least severe\n"
                        "Level 2: Moderate\n"
                        "Level 3: Most severe"
                    )
                    ax.text(0.98, 0.98, description,
                            transform=ax.transAxes,
                            fontsize=8,
                            verticalalignment='top',
                            horizontalalignment='right',
                            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
                    return fig

            # plot of violations per year
            with ui.card():
                ui.card_header("Total Violations per Year")

                @render.plot
                def violations_per_year():
                    conn = cnx()
                    if conn is None:
                        return
                    df = query_for_df("CALL food_inspections.get_violations_per_year()")
                    fig, ax = plt.subplots()
                    ax.plot(df['year'], df['count'], marker='o')
                    ax.set_title('Total Violations per Year')
                    ax.set_xlabel('Year')
                    ax.set_ylabel('Count')
                    return fig

    # Restaurant Search panel
    with ui.nav_panel("Search Restaurants"):
        # panel sidebar -
        with ui.layout_sidebar():
            with ui.sidebar(title="Restaurant Search"):
                with ui.layout_columns(fill=False):
                    ui.input_text("keyword_search", '')
                    ui.input_action_button("send_search", "Enter")
                ui.input_selectize(id="searchbar",
                                   label="Select Restaurant",
                                   choices=["Click to search"],
                                   width='100%')

@reactive.calc
@reactive.event(input.send_search) # enter sends the search
def populate_search_options():
    if input.keyword_search() == '': # keyword_search contains the search terms
        df = query_for_df("CALL get_all_restaurants_search_options()")
        if df is None or df.empty:
            return None
        df = df.head(10)
        cols = df.columns
        df['option'] = df[cols].astype(str).apply(lambda row: str(row.iloc[0]) + ' : ' + ', '.join(row.values[1:]),
                                                  axis=1)
        option_list = df['option'].tolist()
        return option_list
    else:
        with reactive.isolate():
            keywords = input.keyword_search()
        df = query_for_df("CALL search_by_name_restaurant(\'" +keywords+ "\')")
        if df is None or df.empty:
            return None
        df = df.head(10)
        cols = df.columns
        df['option'] = df[cols].astype(str).apply(lambda row: str(row.iloc[0]) + ' : ' + ', '.join(row.values[1:]),
                                                  axis=1)
        option_list = df['option'].tolist()
        with reactive.isolate():
            ui.update_text('keyword_search', value='')
        return option_list

@reactive.effect
def update_choices():
    new_choices = populate_search_options()
    ui.update_selectize(
        'searchbar',
        choices=[],
        selected=None
    )

    if new_choices: # only if there are results
        ui.update_selectize(
            'searchbar',
            choices=new_choices,
            selected=new_choices[0]
        )
    else:
        ui.update_selectize(
            'searchbar',
            choices=[],
            selected=None
        )