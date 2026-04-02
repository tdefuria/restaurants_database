import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import json

from fn_testing import establish_connection, close_connection_quit, password
import matplotlib.pyplot as plt

def query_for_df(query, conn):
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

def main():
    cnx = establish_connection()
    df = query_for_df('CALL get_restaurant_locations()', cnx)
    columns_dict = {col: i for i, col in enumerate(df.columns)}
    business_idx = columns_dict['business_name']
    city_idx = columns_dict['city']
    street_idx = columns_dict['street_num']
    map_df = gpd.read_file("shapes/Census_2010_Tracts.shp")
    if map_df.crs is None:
        map_df.set_crs(epsg=3857, inplace=True)
    map_df_4326 = map_df.to_crs(epsg=4326)
    map_df_4326.to_file("shapes/Census_2010_Tracts.json", driver="GeoJSON")
    with open("shapes/Census_2010_Tracts.json", 'r') as f:
        geojson_data = json.load(f)
    print(geojson_data['features'][0])
    flag = 1
    while flag:
        user_in = input("0 to quit, 1 to continue")
        match user_in:
            case '0':
                close_connection_quit(cnx)
            case '1':
                flag = 0
                continue
            case _:
                print("Invalid input")
    fig = go.Figure()
    ids = []
    for f in geojson_data['features']:
        # Grab the ID from inside the properties of this specific feature
        tract_id = f['properties']['GEOID10']
        # Add it to our list
        ids.append(tract_id)
    # update z values for actual data (total up violations / restaurant for that area)
    z_c = [1] * len(ids)
    fig.add_trace(go.Choroplethmap(
        geojson=geojson_data,
        featureidkey='properties.GEOID10', # This is how to reference the tract names (11 digits)
        z=z_c, # update with any data to differentiate the tracts. Default 1 keeps colors constant.
        locations=ids, # these correspond to the 11 digit tract_ids in our database
        marker_opacity=0.2,
        marker_line_width=2,
        marker_line_color="blue"
    ))
    '''
    Add the second trace.  This is the scatter map that actually has the city tiles.
    It also plots the lat lon data queries from our database for the restaurants
    '''
    fig.add_trace(go.Scattermap(
        lat = df['latitude'],
        lon = df['longitude'],
        customdata = df,
        mode='markers',
        hovertemplate="<b> %{customdata["+str(business_idx)+"]} <br>"
                      " %{customdata["+str(street_idx)+"]} " +
                      " %{customdata["+str(city_idx)+"]}</b><br></br>" +
                      "<b>violations in this time frame.</b><extra></extra>",
    ))
    fig.update_layout(
        mapbox_style='open_street_map',
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        map=dict(
            center=dict(lat=42.3560, lon=-71.0724),  # Boston decimal center coordinates
            zoom=12  # Zoom to a reasonable scope (User can scroll in/out once the map is up)
        )
    )
    fig.show()
    wait = 1
    while wait:
        user_in = input("press 0 to quit")
        if user_in not in ['0', '1']:
            print("not a valid input")
        wait = int(user_in)
    """# Load a built-in map for background (e.g., world)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    # Plot background and points together
    fig, ax = plt.subplots(figsize=(10, 6))
    world.plot(ax=ax, color='lightgrey')
    gdf.plot(ax=ax, color='red', markersize=50)"""
    plt.show()
    close_connection_quit(cnx)

if __name__ == '__main__':
    main()
