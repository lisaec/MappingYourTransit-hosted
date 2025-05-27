from src.grc import *

import importlib
importlib.reload(gui)


app = Dash(__name__, 
            external_stylesheets=[dbc.themes.DARKLY])

app.title = 'Mapping Your Transit'

server = app.server

create_layout(app)
register_callbacks(app)

app.run(debug=False) 
