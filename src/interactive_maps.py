from src.feed import *
import folium
import warnings
warnings.filterwarnings('ignore')

def live_map(feed) -> folium.Map:

    """takes a feed and creates an interactive map, returning the html map
    to put into the dash app"""

    #initializing map
    m = folium.Map(location= feed.center_pt(), zoom_start=12, tiles="Cartodb Positron")

    #generating departure info (takes some time)
    departures = feed.departure_info()

    #ploting each route line
    for index,row in feed.trips_shapes_routes().iterrows():

        folium.PolyLine(row.shape_points.coords,
                        color= f'#{row.route_color}',
                        weight=2.5,
                        opacity=1,
                        popup = f'Route: {row.route_short_name} - {row.route_long_name}'
                       ).add_to(m)
        
    #selecting only the stop info we need, removing null stops and the simple stop types
    stop_sql = """ SELECT stop_id, location_type, stop_lat, stop_lon, stop_name
            FROM stops
            WHERE location_type IS NULL OR location_type == 0 OR location_type == 1
            AND stop_lat NOT NULL AND stop_lon NOT NULL;"""

    stops = pd.read_sql(stop_sql, feed.conn)

    #plot each stop
    for index, row in stops.iterrows():
        if row.stop_id in departures:
            popup = f"{row['stop_name']}<br>{departures[row['stop_id']]}"
        else:
            popup = f"{row['stop_name']}"
        folium.CircleMarker(
                location=[row['stop_lat'], row['stop_lon']],
                radius = 2,
                fill=True,
                fill_color = 'white',
                color = 'black',
                weight = 1,
                tooltip= popup

            ).add_to(m)
        

    return m

