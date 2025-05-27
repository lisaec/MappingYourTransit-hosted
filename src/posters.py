from src import feed
import importlib
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
from src.feed import *
importlib.reload(feed)
import numpy as np
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt



import warnings
warnings.filterwarnings('ignore')


def map(feed, Heatmap = True, user_data = False)-> str:
    
    """Makes 11x17 poster with map, route legend, and an optional heatmap. 
    saves poster in outputs folder and returns the name of the file"""

    # Set up the plot
    fig = plt.figure(figsize=(11, 17))
    gs = GridSpec(nrows=1, ncols=2, width_ratios=[3, 1.5], figure=fig)
    
    #Axes
    ax = fig.add_subplot(gs[0])   #Map
    # ax2 = fig.add_subplot(gs[1]) #Heat Map
    
    #setting extent of axis
    minx, miny, maxx, maxy = unary_union(feed.trips_shapes_routes()['shape_points']).bounds
    extent = [minx - 0.001, maxx + 0.001, miny - 0.001, maxy + 0.001]
    ax.axis(extent)
    
    #Background Colors
    fig.patch.set_facecolor('#f0f0f0')  
    ax.set_facecolor('#fafafa') 
    
    # Turn off ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    #Keep Frame around Map
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor("black")
        spine.set_linewidth(1.5)
    
    #map position relative to figure (adding margin)
    ax.set_position([0.01, 0.01, .99, .99])  # Left, bottom, width, height
    
    #set linewidth and stop size based on number of routes
    n_routes = len(feed.routes())

    if  n_routes <= 20:
        linewidth = 2.5
        stop_size = 4
        edge = 1.5
    elif 21 <= n_routes <= 50:
        linewidth = 2
        stop_size = 3
        edge = 1
    else:
        linewidth = 1.2
        stop_size = 2.5
        edge = 1


    for index, row in feed.trips_shapes_routes().iterrows():
        line = row['shape_points']
        x, y = line.xy  
        ax.plot(x, y,
                linewidth=linewidth,
                color=f"#{row['route_color']}")

    #plot each stop 
    
    #selecting only the stop info we need and the simple stop types
    stop_sql = """ SELECT stop_id, location_type, stop_lat, stop_lon
            FROM stops
            WHERE location_type IS NULL OR location_type == 0 OR location_type == 1;"""

    stops = pd.read_sql(stop_sql, feed.conn)

    for index,row in stops.iterrows():
        x, y = row.stop_lat, row.stop_lon
        ax.plot(x, y, marker="o", color="black", 
            markerfacecolor="white",
            markeredgecolor="black",
            markeredgewidth = edge,
            markersize = stop_size)

    #Creating Legend
    
    # Starting y position for the legend
    y_position = 0.97  

    # Legend Title
    ax.text(
        0.985, y_position + 0.017,
        "ROUTES", 
        transform=ax.transAxes, 
        fontsize = 15,
        verticalalignment='top',
        horizontalalignment='right',
        fontname='Helvetica',
        backgroundcolor = '#fafafa'
        )
   
    #Making Legend Entries
        #Route Names that are not duplicated and have color
    route_sql = """ SELECT route_long_name, 
                            MIN(route_short_name) AS route_short_name, 
                            MIN(
                                CASE 
                                    WHEN LOWER(route_color) = 'ffffff' THEN '000000'
                                    ELSE route_color
                                END
                            ) AS route_color
                        FROM routes 
                        WHERE route_color IS NOT NULL
                        GROUP BY route_long_name;"""
    
    legend_entries = pd.read_sql(route_sql, feed.conn)

    #limiting the number of entries in the legend 
    if len(legend_entries) > 25:
        #if there are too many legend entries then limit it to 25 Randomly Selected ones
        legend_entries = legend_entries.sample(25, ignore_index = True)
    
    # Text: "short name - long name legend entry"
    legend_entries['full_label'] = legend_entries['route_short_name'] + " - " + legend_entries['route_long_name'] + " "
    
    
    #Adding Frame: Text box with the body in transparent text
    ax.text(
        .98, y_position,
        "\n".join([i for i in legend_entries['full_label'].astype(str)]),  
        transform=ax.transAxes,
        bbox = dict(facecolor="white", 
                            alpha = 1,
                            edgecolor="black", linewidth=1), #alpha box is not transparent
        fontsize=13.5,
        verticalalignment='top',
        horizontalalignment='right',
        alpha = 0 #alpha text is transparent
        )
    
    #Adding Text with each route colored in its map color
    for _, row in legend_entries.iterrows():
        route_name = f"{row['route_short_name']} - {row['route_long_name']} "
        route_color = f"#{row['route_color']}"
        # Place each route in the legend with colored text in individual text elements
        ax.text(
            0.98, y_position, route_name, color=route_color,
            transform=ax.transAxes,
            fontsize=12, 
            verticalalignment='top',
            horizontalalignment='right', 
            fontweight='bold',
            fontname='Helvetica'
        )

        # Adjust the y_position down to space out the text
        #Used later in Heatmap positioning too
        y_position -= 0.0125 


    # Agency Name Main Title
    ax.set_title(feed.agency_name(),
                 fontsize=32, 
                 weight='black', 
                 pad=10,
                 loc = "right",
                fontname='Helvetica')
    
    #adding byline
    fig.text(0.99, -0.001, 'Lisa Coleman | Mapping Your Transit', 
         ha='right', fontsize=10, color='gray')

    #filename
    poster_file = f'data/outputs/posters/{feed.name}.png'

    #user uploaded kept separate
    if user_data:
        poster_file = f'data/outputs/posters/user_uploaded/{feed.name}.png'

    #HEATMAP
    if Heatmap:
        #Heatmap shows the top ten most frequent routes and their trip frequency from 8 to 8

        #labeling the files differently
        poster_file = f'data/outputs/posters/{feed.name}_Frequency.png'
        
        if user_data:
            poster_file = f'data/outputs/posters/user_uploaded/{feed.name}_Frequency.png'

        ax2 = fig.add_subplot(gs[1])
        
        cax = ax2.imshow(feed.route_freq().values,  cmap='Reds')
        ax2.set_aspect(.8) 

        hours = list(range(8, 21))

        # Set axis ticks
        ax2.set_xticks(np.arange(len(hours)))
        ax2.set_xticklabels(hours)
        ax2.set_yticks(np.arange(len(feed.route_freq().index)))
        ax2.set_yticklabels(feed.route_freq().index)

        # axis labels
        ax2.set_xlabel("Hour (8am - 8pm)", fontsize=12, fontname='Helvetica')


        # Remove gridlines
        ax2.set_xticks(np.arange(len(hours) + 1) - 0.5, minor=True)
        ax2.set_yticks(np.arange(len(feed.route_freq().index) + 1) - 0.5, minor=True)

        # Whitespace between cells
        ax2.grid(which='minor', color= '#f0f0f0', linestyle='-', linewidth=1)


        # Remove the actual tick marks but keep the labels
        ax2.tick_params(axis='x', which='both', length=0)  # Hide x-axis ticks
        ax2.tick_params(axis='y', which='both', length=0)  # Hide y-axis ticks


        #Setting Position of heatmap beneath legend
        ax2.set_position([.705, y_position - 0.21, .26, .24]) #[left, bottom, width, height]


        #Frequency Table bounding box
        ax.add_patch(Rectangle(
                        (.66, y_position- 0.17),  # Bottom left 
                        .33,  # Width 
                        .14,  # Height 
                        transform=ax.transAxes, 
                        edgecolor='black',
                        facecolor = 'white',
                        zorder=10)
                        )

        #Title of heatmap
        ax.text(
            .985, y_position - 0.017,
            "FREQUENCY BY ROUTE", 
            transform=ax.transAxes, 
            fontsize = 15,
            verticalalignment='top',
            horizontalalignment='right',
            fontname='Helvetica',
            backgroundcolor = '#fafafa'
            )
        
        

    plt.savefig(poster_file, dpi = 500, bbox_inches='tight', pad_inches=0.25)
    
    return poster_file