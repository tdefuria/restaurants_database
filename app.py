import plotly.graph_objects as go
from shiny import reactive, req
from shiny.express import input, render, session, ui
from shinywidgets import render_plotly
import faicons as fa
import pymysql as sql
import pandas as pd
import copy
import matplotlib.pyplot as plt
from pymysql import err
import json

# save value for database connection (session-specific)
cnx = reactive.value(None)

# restaurant_options_dict =
# {'123 Apple Blvd Dorchester':
# {'1234567':
# {{'latitude': 32.2341235, 'longitude': 132.4132523}}
# }}
# license_num values available (session-specific)
restaurant_options_dict = reactive.Value({})
# {'1234567': 81}
# {'license_num: vio_count}
restaurant_vio_count_lookup = reactive.Value({})

# reactive value for reviews data - keyed by option string, value is full row dict
my_reviews_dict = reactive.Value({})

# this reactive value and the function below control updates to relevant value cards after CRUD operations
review_update_trigger = reactive.Value(0)

# whenever this function is called, other reactive values are re-loaded
def trigger_review_update():
    review_update_trigger.set(review_update_trigger() + 1)

# this reactive value controls updates to the reviews selectizer
refresh_reviews_trigger = reactive.Value(0)

def trigger_refresh_reviews():
    refresh_reviews_trigger.set(refresh_reviews_trigger() + 1)

# helper function for calling processes in value cards
def call_proc(proc_name):
    conn = cnx()
    if conn is None:
        return ""
    c = conn.cursor()
    c.callproc(f'food_inspections.{proc_name}')
    return str(c.fetchone()[0])

# helper to display search result count
def search_result_count():
    if not restaurant_options_dict.get():
        return
    return len(restaurant_options_dict.get())

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

# never append to the default param list as that will cause a bug.
# assumes the call already added parenthesis in the param_list if needed
def query_for_dict(query, param_list=[]):
    conn = cnx()
    if conn is None:
        return
    query_string = query + '( ' + ', '.join(param_list) + ' )'
    with conn.cursor(sql.cursors.DictCursor) as cur:
        try:
            cur.execute(query_string)
            results = cur.fetchall()
        except err.OperationalError as e:
            # open error modal
            m = ui.modal(title=str(e).split("\'")[-2], easy_close=True, footer=None)
            ui.modal_show(m)
            return
    return results

# This is for when there are multiple return sets from a procedure
# it handles the while loop for cur.fetchall()
def query_line_by_line_to_dict(conn, query, key_col, value_col, param_list=[]):
    if conn is None:
        return
    query_string = query + '( ' + ', '.join(param_list) + ' )'
    with conn.cursor(sql.cursors.DictCursor) as cur:
        census_tract_densities_dict = {}
        try:
            cur.execute(query_string)
            line_remaining = True
            while line_remaining:
                row = cur.fetchone()
                if row:
                    census_tract_densities_dict[row.get(key_col)] = row.get(value_col)
                    cur.nextset()
                else:
                    line_remaining = False
        except err.OperationalError as e:
            m = ui.modal(title=str(e).split("\'")[-2], easy_close=True, footer=None)
            ui.modal_show(m)
            return
    return census_tract_densities_dict

# Title banner - top of screen
ui.page_opts(
    title="Boston Restaurants: Inspections and Reviews", fillable=False)

# Import Census Tract Shapes
def census_shapes():
    with open("shapes/Census_2010_Tracts.json", 'r') as f:
        geojson_data = json.load(f)
    return geojson_data

# Action button - database log-in
ui.input_action_button("login", "Login to database")

# Action button - database log-out
ui.input_action_button("logout", "Logout")

@reactive.effect
@reactive.event(input.logout)
def close_connection_reactive():
    conn = cnx()
    if conn is None:
        m = ui.modal(title="Must be logged in to logout.", easy_close=True, footer=None)
        ui.modal_show(m)
        return ""
    conn.close() # ignore warning, the boolean logic controls for conn is None
    with reactive.isolate():
        cnx.set(None)
    # open error modal
    m = ui.modal(title="Disconnected... You can now safely close the window.", easy_close=True, footer=None)
    ui.modal_show(m)
    return

# modal pop-up for database login
# input is the action that triggers the event
# login is the id for the input action button
@reactive.effect
@reactive.event(input.login)
def show_login_modal():
    login_modal = ui.modal(
        ui.input_text("name", "Username:"),
        ui.input_password("password", "Password:"),
        ui.input_action_button("connect", "Connect"),
        title="Database Credentials",
        easy_close=True,
        footer=None,
    )
    ui.modal_show(login_modal)

all_tables_fig = reactive.Value(go.Figure())
restaurant_search_fig = reactive.Value(go.Figure())
# used to ensure the plot_basis only develops once not repeatedly
plot_basis_once = reactive.Value(False)

@reactive.effect
@reactive.event(lambda: cnx() is None)
def plot_basis():
    if plot_basis_once.get():
        return
    fig = go.Figure()
    ids = []
    ids = [] # empty list for census tracts
    shapes = census_shapes()
    for f in shapes['features']:
        # Grab the ID from inside the properties of this specific feature
        tract_id = f['properties']['GEOID10']
        # Add it to our list
        ids.append(tract_id)
    # update z values for actual data (total up violations / restaurant for that area)
    z_c = [0] * len(ids)
    fig.add_trace(go.Choroplethmap(
        geojson=shapes,
        featureidkey='properties.GEOID10',  # This is how to reference the tract names (11 digits)
        z=z_c,  # update with any data to differentiate the tracts. Default 1 keeps colors constant.
        locations=ids,  # these correspond to the 11 digit tract_ids in our database
        showscale=False,
        colorscale='Blues',
        marker_opacity=0.2,
        marker_line_width=2,
        marker_line_color="darkblue",
        name='Basemap'
    ))
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style='open_street_map',
        map=dict(
            center=dict(lat=42.3560, lon=-71.0724),  # Boston decimal center coordinates
            zoom=12  # Zoom to a reasonable scope (User can scroll in/out once the map is up)
        )
    )
    all_tables_fig.unset()
    all_tables_fig.set(fig)
    restaurant_search_fig.set(fig)
    plot_basis_once.set(True)


@reactive.effect
@reactive.event(lambda: cnx())
def plot_density():
    shapes = census_shapes()
    with reactive.isolate():
        conn = cnx()
    if not conn:
        return
    ids = {}  # empty list for census tracts
    with reactive.isolate():
        densities_dict = query_line_by_line_to_dict(
            conn,
            'CALL get_each_tract_violations_count',
            'tract_id', 'density', [])
        fig = copy.deepcopy(all_tables_fig.get())
    for f in shapes['features']:
        # Grab the ID from inside the properties of this specific feature
        tract_id = f['properties']['GEOID10']
        # Add it to our list
        ids[tract_id] = densities_dict.get(tract_id, 0)
    # update z values for actual data (total up violations / restaurant for that area)
    fig.add_trace(go.Choroplethmap(
        geojson=shapes,
        featureidkey='properties.GEOID10',  # This is how to reference the tract names (11 digits)
        z=list(ids.values()),  # update with any data to differentiate the tracts. Default 1 keeps colors constant.
        locations=list(ids.keys()),  # these correspond to the 11 digit tract_ids in our database
        colorscale='Blues',
        showscale=False,
        marker_opacity=0.8,
        marker_line_width=2,
        marker_line_color="darkblue",
        name='Density Census Tracts'
    ))
    fig.update_traces(
        hovertemplate="<b>Census Tract:</b> %{location}<br><b>Density of Violations/Restaurant:</b> %{z}<extra></extra>"
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style='open_street_map',
        map=dict(
            center=dict(lat=42.3560, lon=-71.0724),  # Boston decimal center coordinates
            zoom=12  # Zoom to a reasonable scope (User can scroll in/out once the map is up)
        )
    )
    all_tables_fig.unset()
    all_tables_fig.set(fig)
    restaurant_search_fig.set(fig)

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
        successful_connect = ui.modal(title="Connection successful!", easy_close=True, footer=None)
        ui.modal_show(successful_connect)

    except sql.err.OperationalError:
        connection_error = ui.modal(title="Connection failed", easy_close=True, footer=None)
        ui.modal_show(connection_error)

# ENTERING MAIN NESTED STRUCTURE OF UI COMPONENTS
# two tabs: Overview and Restaurant Search
with ui.navset_pill(id="selected_navset_pill"):
    # Overview dashboard tab
    with ui.nav_panel("Overview"):

        ICONS = {"utensils": fa.icon_svg("utensils"),
                 "clipboard": fa.icon_svg("clipboard"),
                 "yelp": fa.icon_svg("yelp"),
                 "star": fa.icon_svg("star"),
                 "triangle-exclamation": fa.icon_svg("triangle-exclamation"),
                 "ranking": fa.icon_svg("ranking-star")
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
                    review_update_trigger() # create dependency: value is watched in case of updates
                    return call_proc('get_review_count')

            # value box: average rating
            with ui.value_box(showcase=ICONS["star"]):
                "Average rating per restaurant"

                @render.text
                def avg_rating():
                    review_update_trigger() # create dependency: value is watched in case of updates
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
                        "Level 1: Most severe\n"
                        "Level 2: Moderate\n"
                        "Level 3: Least severe"
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
        with ui.layout_columns(fill=False):

            @render_plotly
            def census_map_home():
                fig = copy.deepcopy(all_tables_fig.get())
                # This updates the basemap background including census shapes and streetmap
                # by adding the current restaurant search results.
                req(fig.data or fig.layout.map)
                conn = cnx()
                if conn is None:
                    return fig
                df = query_for_df('CALL get_restaurant_locations()')
                columns_dict = {col: i for i, col in enumerate(df.columns)}
                business_idx = columns_dict['business_name']
                city_idx = columns_dict['city']
                street_idx = columns_dict['street_num']
                vio_idx = columns_dict['vio_count']
                # adds a trace to the figure, or overlays these restaurant locations
                # with these custom tooltip (HTML / plotly format)
                fig.add_trace(go.Scattermap(
                    lat=df['latitude'],
                    lon=df['longitude'],
                    customdata=df,
                    mode='markers',
                    hovertemplate="<b> %{customdata[" + str(business_idx) + "]} <br>"
                                                                            " %{customdata[" + str(street_idx) + "]} " +
                                  " %{customdata[" + str(city_idx) + "]}</b><br></br>" +
                                  "<b>%{customdata[" +str(vio_idx)+ "]} violations in this time frame.</b><extra></extra>",
                    name='all_restaurants'
                ))
                return fig

    # Restaurant Search panel
    with ui.nav_panel("Search Restaurants"):
        # panel sidebar -
        with ui.layout_sidebar():
            with ui.sidebar(title="Restaurant Search"):
                with ui.layout_columns(fill=False):
                    ui.input_text("keyword_search", '')
                    ui.input_action_button("send_search", "Enter")

                @render.text
                def search_result_count_display():
                    count = search_result_count()
                    if count:
                        return str(count)+ ' results'
                    else: return "\n"
                ui.input_selectize(id="restaurant_selected",
                                   label="Select or search below...",
                                   choices=[],
                                   width='100%')

            with ui.layout_columns(fill=False):

                with ui.value_box(showcase=ICONS["star"]):
                    "Ratings"


                    @render.text
                    def selected_avg_rating():
                        review_update_trigger()
                        conn = cnx()
                        if conn is None or not input.restaurant_selected():
                            return ""
                        license_num = list(restaurant_options_dict.get().get(
                            input.restaurant_selected(), {}).keys())
                        if not license_num:
                            return ""
                        c = conn.cursor()
                        c.callproc('food_inspections.get_restaurant_rating_and_count', (license_num[0],))
                        row = c.fetchone()
                        if row is None or row[0] is None:
                            return "No ratings yet"
                        avg = round(float(row[0]), 2)
                        # get review count
                        c.callproc('food_inspections.get_restaurant_rating_and_count', (license_num[0],))
                        row = c.fetchone()
                        if row is None or row[0] is None:
                            return "No ratings yet"
                        return f"Total reviews: {row[1]} \n Average rating: {row[0]} stars"


                with ui.value_box(showcase=ICONS["triangle-exclamation"]):
                    "Avg Violations per Inspection"

                    @render.text
                    def selected_avg_violations():
                        conn = cnx()
                        if conn is None or not input.restaurant_selected():
                            return ""
                        license_num = list(restaurant_options_dict.get().get(
                            input.restaurant_selected(), {}).keys())
                        if not license_num:
                            return ""
                        c = conn.cursor()
                        c.callproc('food_inspections.get_restaurant_avg_violations', (license_num[0],))
                        row = c.fetchone()
                        if row is None or row[0] is None:
                            return "No inspections found"
                        return str(row[0])

                with ui.value_box(showcase=ICONS["ranking"]):
                    "Review Ranking"

                    @render.text
                    def selected_review_rank():
                        review_update_trigger()
                        conn = cnx()
                        if conn is None or not input.restaurant_selected():
                            return ""
                        license_num = list(restaurant_options_dict.get().get(
                            input.restaurant_selected(), {}).keys())
                        if not license_num:
                            return ""
                        c = conn.cursor()
                        c.callproc('food_inspections.get_restaurant_review_rank', (license_num[0],))
                        row = c.fetchone()
                        if row is None or row[0] is None:
                            return "Unranked - no reviews"
                        return f"#{row[0]} most reviewed"

            with ui.layout_columns(fill=False):

                @render.text
                @reactive.event(input.send_search)
                def search_result_title():
                    with reactive.isolate():
                        if not input.keyword_search():
                            return ""
                        else:
                            search_title = input.keyword_search() if (cnx() and input.keyword_search()) else "No"
                            search_title = f'\"{search_title}\" '
                    return f'{search_title}Search Results'


            with ui.layout_columns(fill=False):

                @render_plotly
                def census_map_search():
                    search_fig = restaurant_search_fig.get()
                    req(search_fig is not None and (search_fig.data or search_fig.layout.map))
                    return search_fig

            with ui.layout_columns(fill=False):
                # review survey box
                with ui.card():
                    ui.card_header("Review this restaurant!")
                    ui.input_text("email", 'Email Address')
                    ui.input_text("city", 'City')
                    ui.input_text("state", "State (e.g. MA)")
                    # shiny doesn't limit input size, found this through google/stackoverflow:
                    ui.tags.script("""
                        document.getElementById('state').setAttribute('maxlength', '2');
                    """)
                    ui.input_radio_buttons(id="rating", label="Rating:",
                                            choices=["0", "1", "2", "3", "4", "5"],
                                           inline=True)
                    ui.input_text_area(id="comment", label="Comment:",
                                        value='I ate here!')
                    ui.input_action_button("send_comment", "Submit")

                @reactive.effect
                @reactive.event(input.send_comment)
                def submit_review():
                    # check all fields are filled
                    if not all([input.email(), input.city(), input.state(), input.comment(),
                                input.restaurant_selected()]):
                        incomplete_survey = ui.modal(title="Please fill in all fields!", easy_close=True, footer=None)
                        ui.modal_show(incomplete_survey)
                        return
                    # error handling - input for state must be two characters
                    if len(input.state()) > 2:
                        state_abbr = ui.modal(title="Please enter a 2-letter state abbreviation (e.g. MA)!",
                                     easy_close=True, footer=None)
                        ui.modal_show(state_abbr)
                        return
                    if len(input.comment()) > 255:
                        comment_length = ui.modal(title="Please limit comments to 255 characters or less",
                                     easy_close=True, footer=None)
                        ui.modal_show(comment_length)
                        return
                    conn = cnx()
                    if conn is None:
                        return

                    # extract license_num from the selected restaurant option
                    license_num_match = list(restaurant_options_dict.get().get(input.restaurant_selected()).keys())
                    license_num = license_num_match[0] # there is only 1 match
                    username = input.email()
                    try:
                        c = conn.cursor()

                        # insert user if they don't already exist
                        c.callproc('food_inspections.insert_user_if_not_exists',
                                   (username, input.city(), input.state()))

                        # insert the review (should also trigger updates to restaurant table)
                        c.callproc('food_inspections.insert_review',
                                   (license_num, username, input.comment(), input.rating()))

                        conn.commit()
                        trigger_review_update()  # update value boxes

                        # refresh selectize if the review was submitted by the same user currently viewing their reviews
                        if input.email() == input.my_email():
                            trigger_refresh_reviews()

                        # clear review form
                        ui.update_text('email', value='')
                        ui.update_text('city', value='')
                        ui.update_text('state', value='')
                        ui.update_text('comment', value='')
                        trigger_review_update()  # update value boxes
                        successful_submit = ui.modal(title="Review submitted!", easy_close=True, footer=None)
                        ui.modal_show(successful_submit)

                    except sql.err.IntegrityError:
                        m = ui.modal(title="You have already reviewed this restaurant!", easy_close=True, footer=None)
                        ui.modal_show(m)


                with ui.card():
                    ui.card_header("Health Code Violations")

                    # table for health code violations
                    @render.data_frame
                    def violations_table():
                        conn = cnx()
                        if conn is None or not input.restaurant_selected():
                            return pd.DataFrame()

                        # extract license number form selection
                        license_num = list(restaurant_options_dict.get().get(
                            input.restaurant_selected(), {}).keys())
                        if not license_num:
                            return pd.DataFrame()

                        # find all violations for the selected restaurant
                        with conn.cursor(sql.cursors.DictCursor) as cur:
                            cur.callproc('food_inspections.get_restaurant_violations', (license_num[0],))
                            results = cur.fetchall()

                        if not results:
                            return pd.DataFrame()

                        # dataframe of violations
                        df = pd.DataFrame(results)
                        df = df[['status_date', 'type_code', 'type_description',
                                 'violation_level', 'violation_status', 'violation_comment']]
                        df.columns = ['Date', 'Code', 'Description', 'Level', 'Status', 'Comment']
                        return render.DataGrid(df)

    # my reviews panel
    with ui.nav_panel("My Reviews"):
        with ui.layout_sidebar():
            # search for your reviews using your email address
            with ui.sidebar(title="Find My Reviews"):
                # search email
                ui.input_text("my_email", "Enter your email address:")
                # action button for search
                ui.input_action_button("find_reviews", "Find Reviews")
                # all reviews associated with your email will populate selectizer
                ui.input_selectize(id="review_selected",
                                   label="Select a review to edit:",
                                   choices=[],
                                   width='100%')

            with ui.card():
                ui.card_header("Edit Review")

                # using render.ui so that the below only appear if a review is selected
                @render.ui
                def edit_review_form():
                    if not input.review_selected() or input.review_selected() == '':
                        return ui.p("Select a review from the sidebar to edit it.")

                    # find the selected review in the "get reviews" query
                    row = my_reviews_dict().get(input.review_selected())
                    if row is None:
                        return ui.p("No review data found.")

                    # using html tools for "prettier" html formatting: p = paragraph, em = emphasis
                    return ui.TagList(
                        ui.p(ui.strong(row['business_name'])),
                        ui.input_radio_buttons(
                            id="edit_rating",
                            label="Rating:",
                            choices=["0", "1", "2", "3", "4", "5"],
                            selected=str(row['rating']),
                            inline=True
                        ),
                        ui.input_text_area(
                            id="edit_comment",
                            label="Comment:",
                            value=row['review_comment']
                        ),
                        ui.p(ui.em(f"Originally reviewed: {row['review_date']}")),
                        ui.input_action_button("update_review_btn", "Update Review",
                                               class_="btn-primary"),
                        ui.input_action_button("delete_review_btn", "Delete Review",
                                               class_="btn-danger"), #btn-danger -> red!
                    )

@reactive.effect
@reactive.event(input.find_reviews, refresh_reviews_trigger)
def load_my_reviews():
    if not cnx():
        if input.find_reviews() > 0:  # only show modal if user clicked the button
            m = ui.modal(title="Please login to database first!", easy_close=True, footer=None)
            ui.modal_show(m)
        return
    if not input.my_email():
        if input.find_reviews() > 0:
            m = ui.modal(title="Please enter an email address!", easy_close=True, footer=None)
            ui.modal_show(m)
        return
    conn = cnx()
    if conn is None:
        return
    # find all reviews from user's email
    with conn.cursor(sql.cursors.DictCursor) as cur:
        cur.callproc("food_inspections.get_reviews_by_user", (input.my_email(),))
        results = cur.fetchall()
    if not results:
        m = ui.modal(title="No reviews found for this email.", easy_close=True, footer=None)
        ui.modal_show(m)
        return
    # put results in dictionary
    d = {}
    for row in results:
        option = f"{row['business_name']} : {row['review_date']} : {row['rating']}★"
        d[option] = row

    # update selectizer with query results
    my_reviews_dict.set(d)
    options = list(d.keys())
    ui.update_selectize('review_selected', choices=options, selected=options[0])

@reactive.effect
@reactive.event(input.update_review_btn)
def update_review():
    selected = input.review_selected()
    if not selected:
        return
    row = my_reviews_dict().get(selected)
    if row is None:
        return
    conn = cnx()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.callproc('food_inspections.update_review', (
            row['license_num'],
            input.my_email(),
            input.edit_comment(),
            input.edit_rating()
        ))
        conn.commit()
        trigger_review_update()  # update value boxes
        trigger_refresh_reviews()  # refresh selectize
        m = ui.modal(title="Review updated!", easy_close=True, footer=None)
        ui.modal_show(m)

    except Exception as e:
        m = ui.modal(title=f"Error: {str(e)}", easy_close=True, footer=None)
        ui.modal_show(m)

@reactive.effect
@reactive.event(input.delete_review_btn)
def delete_review():
    selected = input.review_selected()
    if not selected:
        return
    row = my_reviews_dict().get(selected)
    if row is None:
        return
    conn = cnx()
    if conn is None:
        return
    try:
        c = conn.cursor()
        c.callproc('food_inspections.delete_review', (
            row['license_num'],
            input.my_email()
        ))
        conn.commit()
        trigger_review_update()
        d = dict(my_reviews_dict())
        d.pop(selected, None)
        my_reviews_dict.set(d)
        options = list(d.keys())
        ui.update_selectize('review_selected', choices={}, selected=None)
        ui.update_selectize('review_selected',
                            choices=options if options else {},
                            selected=options[0] if options else None)
        m = ui.modal(title="Review deleted!", easy_close=True, footer=None)
        ui.modal_show(m)
    except Exception as e:
        m = ui.modal(title=f"Error: {str(e)}", easy_close=True, footer=None)
        ui.modal_show(m)
        trigger_refresh_reviews()
        d = dict(my_reviews_dict())
        d.pop(selected, None)
        my_reviews_dict.set(d)
        options = list(d.keys())
        ui.update_selectize('review_selected', choices={}, selected=None)
        ui.update_selectize('review_selected',
                            choices=options if options else {},
                            selected=options[0] if options else None)
        m = ui.modal(title="Review deleted!", easy_close=True, footer=None)
        ui.modal_show(m)
    except Exception as e:
        m = ui.modal(title=f"Error: {str(e)}", easy_close=True, footer=None)
        ui.modal_show(m)

# organize the results from restaurant search query from database
def concatenate_restaurant_results(result_list):
    if not result_list:
        return None, None
    rows = [] # rows will become a dataframe for the mapping component
    new_restaurant_options_dict = {} # build the options for restaurants
    new_restaurant_vio_counts = {} # dictionary for violation counts
    for i in range(len(result_list)):
        result_dict = result_list[i]
        option = f"{result_dict.get('business_name', 'No business name')}"
        # <br> goes here if js formatting works, otherwise ',' (comma)
        option += f", {result_dict.get('street_num', 'No street')}"
        option += f", {result_dict.get('city', 'No city')}"
        #all elements for the map option is the tooltip text. vio_count is, too.
        rows.append({'options': option,
                     'latitude': result_dict.get('latitude'),
                     'longitude': result_dict.get('longitude'),
                     'vio_count': result_dict.get('vio_count')})
        new_restaurant_options_dict[option] = \
            {result_dict.get('license_num'):
                 {'latitude': result_dict.get('latitude'),
                  'longitude': result_dict.get('longitude')}
             }
        new_restaurant_vio_counts[result_dict.get('license_num')] = result_dict.get('vio_count')
    restaurant_vio_count_lookup.set(new_restaurant_vio_counts) # set to the client reactive value
    results_df = pd.DataFrame(rows) # dataframe goes to map later
    return results_df, new_restaurant_options_dict

@reactive.calc
@reactive.event(input.send_search) # enter sends the search
def populate_search_options():
    # check for invalid states first:
    with reactive.isolate():
        prev = restaurant_options_dict.get() # prev options_dict
    if not cnx(): # check connection and issue reminder to login if not.
        search_modal = ui.modal(title="Please login to database first!", easy_close=True, footer=None)
        ui.modal_show(search_modal)
        return pd.DataFrame(), prev # empty df, prev options_dict
    elif not input.keyword_search(): # keyword_search contains no search terms
        m = ui.modal(title="Please enter an keyword search!", easy_close=True, footer=None)
        ui.modal_show(m)
        return pd.DataFrame(), prev # empty df, prev options_dict, for valid blank UI no errors
    else: # all invalid states ruled out, proceed with standard logic:
        with reactive.isolate(): # prevent infinite loop dependent on keyword_search
            keywords = input.keyword_search()
        try:
            result_list = query_for_dict("CALL search_by_name_restaurant", ["\'"+keywords+"\'"])
        except err.Error as e:
            invalid_char_modal = ui.modal(
                title="Please ensure you only enter valid alphabetical characters. Do not include punctuation",
                easy_close=True, footer=None)
            ui.modal_show(invalid_char_modal)
            return pd.DataFrame(), prev
        results_df, new_restaurant_options_dict = concatenate_restaurant_results(result_list)
        """with reactive.isolate():
            ui.update_text('keyword_search', value='')"""
    return results_df, new_restaurant_options_dict

@reactive.effect
@reactive.event(input.restaurant_selected)
def zoom_to_restaurant_selection():
    # get the restaurant_options_dict license_num matching that option
    rest_options = restaurant_options_dict.get()
    if not rest_options:
        return
    # the restaurant_selected() input may not be user input. Must match the options available.
    selected = input.restaurant_selected()
    if selected not in rest_options:
        return
    license_num = list(rest_options.get(selected).keys())[0]
    coords = rest_options.get(selected).get(license_num)
    with reactive.isolate():
        current_fig = copy.deepcopy(restaurant_search_fig.get())
    current_fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style='open_street_map',
        map=dict(
            center=dict(lat=coords.get('latitude'),
                lon=coords.get('longitude')),  # Selected option coordinates
            zoom=15  # Zoom to a reasonable scope (User can scroll in/out once the map is up)
        )
    )
    restaurant_search_fig.set(current_fig)

@reactive.effect
@reactive.event(input.send_search)
def update_choices():
    #new_choices_list,
    results_df, new_restaurant_options_dict = populate_search_options()
    ui.update_selectize(
        'restaurant_selected',
        choices=[],
        selected=None
    )
    with reactive.isolate():
        base_fig = copy.deepcopy(all_tables_fig.get())
    restaurant_search_fig.unset()
    with reactive.isolate():
        if isinstance(results_df, pd.DataFrame) and results_df.empty == False: # only if there are results
            # update selectize options with js_eval rich text
            # shinywidgets
            ui.update_selectize(
                'restaurant_selected',
                choices=results_df['options'].tolist(),
                selected=[],
                # attempt at js formatting the options to include line breaks between place name and address
                # didn't work, so current version has commas instead.  Room for improvement.
                options={
                    "render": ui.js_eval(
                        """{
                        option: function(item, escape) {
                                return '<div>' + item.label + '</div>';
                        },
                        item: function(item, escape) {
                                return '<div>' + item.label + '</div>';
                        }
                    }""")
                }
            )
            restaurant_options_dict.unset()
            restaurant_options_dict.set(new_restaurant_options_dict)
            # add the new search results to the base map copy
            base_fig.add_trace(go.Scattermap(
                lat=results_df['latitude'],
                lon=results_df['longitude'],
                customdata=results_df,
                mode='markers',
                hovertemplate="<b>%{customdata["+str(0)+"]}</b><br>" +
                              "<b>%{customdata[" +str(3)+ "]} violations in this time frame.</b><extra></extra>",
                name='all_restaurants'
            ))
        else:
            # update selectize with empty list
            ui.update_selectize(
                'restaurant_selected',
                choices=[],
                selected=None,
            )
            restaurant_options_dict.unset()
            restaurant_options_dict.set({})
    # store the improved/populated basemap as the new restaurant search
    restaurant_search_fig.set(base_fig)
