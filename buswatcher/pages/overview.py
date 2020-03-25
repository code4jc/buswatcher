import pandas as pd
import pathlib

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from utils import Header, make_dash_table, make_dash_chart_data

import lib.Reports as reports
import lib.Maps as maps
# import lib.TransitSystem as system
# system_map = system.load_system_map()

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("../data").resolve()


route = 87 #todo set this from the callback

_df_route_summary = reports.get_route_summary(route)
# todo plug in live data source by making a call to wwwAPI here e.g. df_route_summary = wwwAPI.get_route_summary(route) where route is a callback from a dropdown



def create_layout(app,routes):
    # Page layouts
    return html.Div(
        [
            html.Div([Header(app,routes)]),
            # page 1
            html.Div(
                [
                    # Row 1
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H5("How Is the 87 Doing?"), # todo inject callback here
                                    html.H6("Journal Square — Hoboken"),
                                    html.Br([]),
                                    html.P(
                                        "\
                                        Residents and businesses depend on NJTransit buses every day. But its hard to\
                                        evaluate the quality of bus service.\
                                        That's why we built this site to provide a one-stop shop for bus performance\
                                        information. Here you can see data on past performance and view maps of current\
                                        service.",
                                        style={"color": "#ffffff"},
                                        className="row",
                                    ),


                                ],
                                className="product",
                            ),

                        ],
                        className="row",
                    ),
                    # Row 2
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        ["Route Overview"], className="subtitle padded"
                                    ),
                                    html.Table(make_dash_table(_df_route_summary)),
                                ],
                                className="six columns",
                            ),
                            html.Div(
                                [
                                    html.H6(
                                        "Overall Grade", className="subtitle padded"
                                    ),
                                    html.Table(make_dash_table(reports.get_grade(route))),
                                ],
                                className="six columns",
                            ),
                        ],
                        className="row ",
                    ),


                    # Row 3
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(
                                        "Frequency",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        id="graph-2",
                                        figure={
                                            "data": make_dash_chart_data(reports.get_frequency(route)),

                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                legend={
                                                    "x": -0.0277108433735,
                                                    "y": -0.142606516291,
                                                    "orientation": "h",
                                                },
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 20,
                                                    "l": 50,
                                                },
                                                showlegend=True,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "hour of day",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 60],
                                                    "showgrid": True,
                                                    "showline": True,
                                                    "ticklen": 10,
                                                    "ticks": "outside",
                                                    "title": "minutes",
                                                    "type": "linear",
                                                    "zeroline": False,
                                                    "zerolinewidth": 4,
                                                },
                                            ),
                                        },
                                        config={"displayModeBar": False},
                                    ),

                                    html.H6(
                                        "Reliability",
                                        className="subtitle padded",
                                    ),
                                    dcc.Graph(
                                        id="graph-2",
                                        figure={
                                            "data": [
                                                go.Scatter(
                                                    x=[
                                                        "6",
                                                        "7",
                                                        "8",
                                                        "9",
                                                        "10",
                                                        "11",
                                                        "12",
                                                        "13",
                                                        "14",
                                                        "15",
                                                        "16",
                                                    ],
                                                    y=[
                                                        "65",
                                                        "65",
                                                        "75",
                                                        "95",
                                                        "75",
                                                        "65",
                                                        "65",
                                                        "75",
                                                        "95",
                                                        "75",
                                                        "65",
                                                    ],
                                                    line={"color": "#e5bbed"},
                                                    mode="lines",
                                                    name="87 Weekdays",
                                                )
                                            ],
                                            "layout": go.Layout(
                                                autosize=True,
                                                title="",
                                                font={"family": "Raleway", "size": 10},
                                                height=200,
                                                width=340,
                                                hovermode="closest",
                                                legend={
                                                    "x": -0.0277108433735,
                                                    "y": -0.142606516291,
                                                    "orientation": "h",
                                                },
                                                margin={
                                                    "r": 20,
                                                    "t": 20,
                                                    "b": 20,
                                                    "l": 50,
                                                },
                                                showlegend=True,
                                                xaxis={
                                                    "autorange": True,
                                                    "linecolor": "rgb(0, 0, 0)",
                                                    "linewidth": 1,
                                                    "range": [6, 16],
                                                    "showgrid": False,
                                                    "showline": True,
                                                    "title": "",
                                                    "type": "linear",
                                                },
                                                yaxis={
                                                    "autorange": False,
                                                    "gridcolor": "rgba(127, 127, 127, 0.2)",
                                                    "mirror": False,
                                                    "nticks": 4,
                                                    "range": [0, 120],
                                                    "showgrid": True,
                                                    "showline": True,
                                                    "ticklen": 10,
                                                    "ticks": "outside",
                                                    "title": "minutes",
                                                    "type": "linear",
                                                    "zeroline": False,
                                                    "zerolinewidth": 4,
                                                },
                                            ),
                                        },
                                        config={"displayModeBar": False},
                                    ),







                                    # html.Div(
                                    #     [
                                    #         html.H6(
                                    #             "Reliability",
                                    #             className="subtitle padded",
                                    #         ),
                                    #         html.Table(make_dash_table(_87_reliability_overview)),
                                    #     ],
                                    #     className="twelve columns",
                                    # ),
                                ],
                                className="six columns",
                            ),
                            html.Div(
                                [
                            html.H6(
                                "Route Map",
                                className="subtitle padded",
                            ),
                            # good spot for the map
                            # todo how to add another layer to this?
                            dcc.Graph(id="map", config={"responsive": True},
                                      figure=maps.gen_map(route)
                                    ),


                        ],
                        className="six columns",
                    ),


                        ],
                        className="row ",
                    ),

                    # # Row 4
                    # html.Div(
                    #     [
                    #         html.Div(
                    #             [
                    #                 html.H6(
                    #                     "Reliability",
                    #                     className="subtitle padded",
                    #                 ),
                    #                 html.Table(make_dash_table(_df_reliability_overview)),
                    #             ],
                    #             className="six columns",
                    #         ),
                    #
                    #     ],
                    #     className="row ",
                    # ),
                ],

            className="sub_page",
            ),
        ],
        className="page",
    )