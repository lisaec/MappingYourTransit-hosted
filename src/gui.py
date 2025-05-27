
from dash import Dash, html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc
import base64
import zipfile
import importlib
import os

from src import feed
from src import interactive_maps
from src import posters
from src import heatmap
importlib.reload(feed)
importlib.reload(posters)


import warnings
warnings.filterwarnings('ignore')

def run_app() -> None:

    """Runs the Dash App when called in main python file"""

    app = Dash(__name__, 
                external_stylesheets=[dbc.themes.DARKLY])
    app.title = 'Mapping Your Transit'

    create_layout(app)
    register_callbacks(app)

    app.run(debug=False) 

def create_layout(app: Dash) -> None:
    """Sets up the layout of the App"""

    #Main Layout (contains all main features)
    layout = html.Div(
        id='main-div',
        style={'padding': '40px'},
        children=[
            html.H1('Mapping Your Transit'), #title
            html.Hr(), #horizontal Line
            html.H4("Create an interactive transit map by uploading your General Transit Feed Specification (GTFS) Folder below or select from the example transit systems"),

            # side-by-side container for dropdown and upload
            html.Div(
                style={'display': 'flex', 'gap': '50px', 'alignItems': 'center'},
                children=[
                        dcc.Dropdown(
                            id='demo-dropdown',
                            options=[
                                {'label': 'Williamsburg', 'value': 'Williamsburg'},
                                {'label': 'New York City Subway', 'value': 'New York'},
                                {'label': 'San Luis Obispo', 'value': 'San Luis Obispo'},
                                {'label': 'Charlottesville', 'value': 'Charlottesville'}
                            ],
                            value = None,
                            placeholder="Select a sample feed",
                                style={
                                    'width': '100%',
                                    'color': 'black',
                                    'backgroundColor': 'white'
                                }
                        ),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div(
                                ['Drag and Drop Compressed GTFS Folder or ',
                                    html.A('Select File')
                                ]
                            ),
                            style={
                                'width': '100%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'padding': '0 px',
                                'lineHeight': '1.5' 
                            },
                            multiple=False
                        )
                    ]
            ),

            # Empty Map display panel

            html.Div(
                style={'display': 'flex', 'gap': '50px', 'alignItems': 'center'},
                children=[

                    html.Div(
                                id='map-container',
                                children= html.Div(
                                    "No map loaded yet.",
                                    style={
                                        "height": "600px",
                                        "backgroundColor": "#f9f9f9",
                                        "textAlign": "center",
                                        "lineHeight": "600px",
                                        "color": "#666",
                                        "fontStyle": "italic"
                                    }
                                ),
                                style={
                                    'marginTop': '20px',
                                    'width': '70%',
                                    'marginLeft': 'auto',
                                    'marginRight': 'auto'
                                }
                            ),
                    
                ]
            ),

            # Active Feed storage
            dcc.Store(id='active-feed-string')
        ]
    )

    app.layout = layout
    return None



def register_callbacks(app):
    """Tells Dash what to do when user interacts with app"""
    @app.callback(
        Output('map-container', 'children'),
        Output('active-feed-string', 'data'),
        Input('upload-data', 'contents'),
        Input('demo-dropdown', 'value'),
        State('upload-data', 'filename')
    )
    def update_map(contents, demo_choice, filename):
        """Puts map in interactive window"""
        placeholder = html.Div(
            "Select a Transit Feed",
            style={
                "height": "600px",
                "backgroundColor": "#f9f9f9",
                "textAlign": "center",
                "lineHeight": "600px",
                "color": "#666",
            })
        def label_box(feed):
            """adds label box"""
            return html.Div(
                feed.agency_name(),
                style={
                    "marginTop": "18px",
                    "marginBottom": "18px",
                    "textAlign": "center",
                    "padding": "10px",
                    "border": "1px solid black",
                    "borderRadius": "0px",
                    "color": "black",
                    "fontWeight": "bold",
                    "backgroundColor": 'white',
                    "width": "100%",
                    "marginLeft": "auto",
                    "marginRight": "auto"
                }
            )
        def website_box(feed):
                """adds website link"""
                return html.Div(children=html.A(f"Agency Website", href=feed.agency_url(), target="_blank"),
                style={
                    "marginTop": "15px",
                    "textAlign": "center",
                    "padding": "10px",
                    "border": "1px solid black",
                    "borderRadius": "0px",
                    "color": "black",
                    "textDecoration": "none",
                    "fontWeight": "bold",
                    "backgroundColor": 'white',
                    "width": "40%",
                    "marginLeft": "auto",
                    "marginRight": "auto"
                }
            )
        def insert_heatmap(feed):
            return [html.H4("Frequency of Top 10 Routes",
                            style={"color": "white",
                                   "textAlign": "center"
                                   }),
            dcc.Graph(
                id="heatmap-graph",
                figure=heatmap.heatmap(feed),
                config={"displayModeBar": False},  # optional
                style={"height": "300px",
                       "width": "500px",
                        "marginBottom": "15px"}
            )]

        #If user uploads a file: read the feed and add in the label boxes
        if contents is not None:
            # User uploaded a file
            map_frame, feed_path = read_feed(contents, filename)

            return html.Div(style={
                            'display': 'flex',
                            'flexDirection': 'column',  # Stack vertically
                            'alignItems': 'center',     
                            'width': '100%',
                            'margin': 'auto',
                            'marginTop': '20px',
                        }, children = [
                label_box(feed.Feed(feed_path)),
                # Horizontal layout with map on left and heatmap + poster tools on right
                html.Div(
                    style={
                            'display': 'flex',
                            'justifyContent': 'space-between',
                            'alignItems': 'flex-start',
                            'gap': '40px',
                            'padding': '0 00px',   # smaller side padding
                            'width': '100%',       # full width
                            'boxSizing': 'border-box'  # include padding in width calculation
                        },
                    children=[

                        # Left side: the map
                        html.Div(
                            [map_frame, website_box(feed.Feed(feed_path))],
                            style={
                                'marginTop': '20px',
                                'width': '70%',
                                'marginLeft': 'auto',
                                'marginRight': 'auto'
                            }
                        ),

                        # Right side: heatmap and poster tools stacked
                        html.Div(
                            style={"width": "30%"},
                            children=[
                                html.Div(
                                    children=insert_heatmap(feed.Feed(feed_path)),
                                    style={"marginBottom": "40px"}
                                ),
                                html.H3("Create a Poster Map"),
                                html.Label("Include Frequency Summary?"),
                                dcc.RadioItems(
                                    id='include-summary-input',
                                    options=[
                                        {'label': 'Yes', 'value': True},
                                        {'label': 'No', 'value': False}
                                    ],
                                    value=True,
                                    labelStyle={'display': 'inline-block', 'margin-right': '30px'}
                                ),
                                html.Br(),
                                dbc.Button("Download Poster", id="btn_txt", color="secondary", className="me-1"),
                                dcc.Download(id="download_text_index")
                            ]
                        )
                    ]
                )
            ]), feed_path

        #If user selects a sample feed: load the sample feed
        elif demo_choice:
            # User picked a sample dataset
            map_frame, feed_path = load_sample_feed(demo_choice)
            # Horizontal layout with map on left and heatmap + poster tools on right
            return html.Div(style={
                            'display': 'flex',
                            'flexDirection': 'column',  # Stack vertically
                            'alignItems': 'center',     # Center all horizontally
                            'width': '100%',
                            'margin': 'auto',
                            'marginTop': '20px',
                        }, children = [
                        label_box(feed.Feed(feed_path)),
                        html.Div(
                        style={
                            'display': 'flex',
                            'justifyContent': 'space-between',
                            'alignItems': 'flex-start',
                            'gap': '40px',
                            'padding': '0 00px',   # smaller side padding
                            'width': '100%',       # full width
                            'boxSizing': 'border-box'  # include padding in width calculation
                        },
                        children=[

                            # Left side: the map
                            html.Div(
                                [map_frame, website_box(feed.Feed(feed_path))],
                                style={
                                    'marginTop': '20px',
                                    'width': '70%',
                                    'marginLeft': 'auto',
                                    'marginRight': 'auto'
                                }
                            ),

                            # Right side: heatmap and poster tools stacked
                            html.Div(
                                style={"width": "30%"},
                                children=[
                                    html.Div(
                                        children=insert_heatmap(feed.Feed(feed_path)),
                                        style={"marginBottom": "40px"}
                                    ),
                                    html.H3("Create a Poster Map"),
                                    html.Label("Include Frequency Summary?"),
                                    dcc.RadioItems(
                                        id='include-summary-input',
                                        options=[
                                            {'label': 'Yes', 'value': True},
                                            {'label': 'No', 'value': False}
                                        ],
                                        value=True,
                                        labelStyle={'display': 'inline-block', 'margin-right': '30px'}
                                    ),
                                    html.Br(),
                                    dbc.Button("Download Poster", id="btn_txt", color="secondary", className="me-1"),
                                    dcc.Download(id="download_text_index")
                                ]
                            )       
                        ]
                    )]
            
                ), feed_path
        
        #Before user does anything use the placeholder
        else:
            # Neither uploaded nor selected
            return placeholder, None
        
#callback for poster download
    @app.callback(
    Output("download_text_index", "data"),
    Input("btn_txt", "n_clicks"),
    State('active-feed-string', 'data'),  
    State('include-summary-input', 'value'),
    prevent_initial_call=True
    )
    def throw_poster(n_clicks, filename, heatmap_choice):
        "generates poster and sends it to the button"
        if not filename:
            return None  # no feed selected, nothing to generate
        
        if 'user_data' in filename.split(os.sep):
            user_data = True
        else: 
            user_data = False

        poster_file = posters.map(feed.Feed(filename), Heatmap = heatmap_choice, user_data = user_data)
        return dcc.send_file(poster_file) 
    

def read_feed(contents, filename):
    """reads feed from drag and drop box, decoding the uploaded zip file,
    saves the zip and the extracted file, creates the feed object, and returns 
    html iframe of map"""

    # Interpreting contents: upload -> filename for unzipped folder of gtfs data
    #decoding contents
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    # Save uploaded zip
    zip_path = os.path.join('data/user_data/gtfs_files/zipped_files', filename)
    with open(zip_path, 'wb') as f:
        f.write(decoded)

    #unzipping into a folder in gtfs_files folder
    gtfs_folder_name = filename.replace('.zip', '') #folder name
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('data/user_data/gtfs_files') #extract to that folder

    # Create the Feed and map
    feed_filename = os.path.join('data/user_data/gtfs_files', gtfs_folder_name)
    gtfs_feed = feed.Feed(feed_filename)
    folium_map = interactive_maps.live_map(gtfs_feed)
    map_html = folium_map.get_root().render()

    return html.Iframe(srcDoc=map_html,
                       width='100%',
                       height='600',
                       style={"border": "none"}), feed_filename 


def load_sample_feed(demo_choice):
    """creates instance of feed object from sample data and returns 
    html iframe of map"""

    sample_feed_path = "data/samples/gtfs_files"
    sample_paths = {
        'New York': 'gtfs_nyc',
        'Williamsburg': 'gtfs_wata',
        'San Luis Obispo' : 'gtfs_slo',
        'Charlottesville' : 'gtfs_charlottesville'

    }
    
    gtfs_folder_path = os.path.join(sample_feed_path, sample_paths.get(demo_choice))

    # Create the Feed and map
    gtfs_feed = feed.Feed(gtfs_folder_path)
    folium_map = interactive_maps.live_map(gtfs_feed)
    map_html = folium_map.get_root().render()

    return html.Iframe(srcDoc=map_html,
                       width='100%',
                       height='600',
                       style={"border": "none"}), gtfs_folder_path
