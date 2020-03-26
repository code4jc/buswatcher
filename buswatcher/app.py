# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pages import (
    overview,
    speed,
    frequency,
    reliability,
    bunching,
    newsReviews,
)

# get system map
from lib.TransitSystem import load_system_map
system_map=load_system_map()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)
server = app.server

# Describe the layout/ UI of the app
app.layout = html.Div(
    [dcc.Location(id="url", refresh=False), html.Div(id="page-content")]
)

# suppress callback warnings
app.config['suppress_callback_exceptions'] = True

# get routes defined in config/collection_descriptions.json
routes = dict()
for k, v in system_map.collection_descriptions.items():
    for r in v['routelist']:
        for rr in system_map.route_descriptions['routedata']:
                if rr['route'] == r:
                    routes[r]=rr['prettyname'] #bug dies here if this isnt defined in route_desrptions.json


# Update page
@app.callback(
        Output("page-content", "children"),
        [Input("url", "pathname")])
def display_page(pathname):

    if pathname == "/speed":
        return speed.create_layout(app,routes)
    elif pathname == "/frequency":
        return frequency.create_layout(app,routes)
    elif pathname == "/reliability":
        return reliability.create_layout(app,routes)
    elif pathname == "/bunching":
        return bunching.create_layout(app,routes)
    elif pathname == "/news-and-reviews":
        return newsReviews.create_layout(app,routes)
    elif pathname == "/full-view":
        return (
            overview.create_layout(app,routes),
            speed.create_layout(app,routes),
            frequency.create_layout(app,routes),
            reliability.create_layout(app,routes),
            bunching.create_layout(app,routes),
            newsReviews.create_layout(app,routes),
        )
    else:
        return overview.create_layout(app,routes)



# todo pass active_route back into the other callback to load the data, or do it here
@app.callback(Output('active_route', 'children'), [Input('route_choice', 'value')])
def output_active_route(route):
    return u'{}'.format(route)

if __name__ == "__main__":
    app.run_server(debug=True)
