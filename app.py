from src.gui import *


app = Dash(__name__, 
            external_stylesheets=[dbc.themes.DARKLY])

app.title = 'Mapping Your Transit'

server = app.server

create_layout(app)
register_callbacks(app)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # Render sets the PORT env variable
    app.run_server(host='0.0.0.0', port=port, debug=False)