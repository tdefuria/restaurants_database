
from shiny import reactive
from shiny.express import input, render, ui
import faicons as fa
import pymysql as sql

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
        cnx = sql.connect(host='localhost', user=input.name(), passwd=input.password(),
                                  db='gamedb_cainh', charset='utf8mb4')
        ui.modal_remove()

    # modal for connection failure
    except sql.err.OperationalError:
        @reactive.effect
        def show_failure_modal():
            m = ui.modal(title="Connection failed",
                easy_close=True,
                footer=None,
            )
            ui.modal_show(m)

# two tabs: Overview and Restaurant Search
with ui.navset_pill(id="selected_navset_pill"):
    # Overview dashboard tab
    with ui.nav_panel("Overview"):
        "Boston Overview Dashboard"

        ICONS = {"utensils": fa.icon_svg("utensils"),
                 "clipboard": fa.icon_svg("clipboard"),
                 "yelp": fa.icon_svg("yelp")}

        with ui.layout_columns(fill=False):
            with ui.value_box(showcase=ICONS["utensils"]):
                "Total restaurants"

                @render.express
                def total_restaurants():
                    pass # SQL FUNCTION: SELECT * FROM restaurant

            with ui.value_box(showcase=ICONS["clipboard"]):
                "Total health inspections"

                @ render.express
                def total_health_inspections():
                    pass # SQl FUNCTION: SELECT * FROM restaurant

            with ui.value_box(showcase=ICONS["yelp"]):
                "Total reviews"

                @render.express
                def total_reviews():
                    pass #SQL FUNCTION: SELECT * FROM reviews

    # Restaurant Search panel
    with ui.nav_panel("Search Restaurants"):
        # panel sidebar -
        with ui.layout_sidebar():
            with ui.sidebar(title="Restaurant Search"):
                ui.input_selectize(id="searchbar",
                                   label="Search Restaurants",
                                   choices=['cat', 'car', 'cow', 'cow2', 'cow3'],
                                   width='100%')







