
from shiny import reactive, req
from shiny.express import input, render, ui
import faicons as fa
import pymysql as sql

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

# title banner - top of screen
ui.page_opts(
    title="Boston Restaurants: Inspections and Reviews", fillable=False)


# Action button - database log-in
ui.input_action_button("login", "Login to database")

# modal pop-up for database login
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

    # Restaurant Search panel
    with ui.nav_panel("Search Restaurants"):
        # panel sidebar -
        with ui.layout_sidebar():
            with ui.sidebar(title="Restaurant Search"):
                ui.input_selectize(id="searchbar",
                                   label="Search Restaurants",
                                   choices=['cat', 'car', 'cow', 'cow2', 'cow3'],
                                   width='100%')







