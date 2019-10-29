import pickle
import copy
import pathlib
import flask
import dash
import math
import base64
import os
import datetime as dt
import pandas as pd
import authentication
import dash_core_components as dcc
import dash_html_components as html

from google.cloud import kms_v1
from dash.dependencies import Input, Output, State, ClientsideFunction

# Multi-dropdown options
from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
AZURE_OAUTH = os.getenv('AD_AUTH', False)

# Initiate flask server
server = flask.Flask(__name__)

# Create dash application
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    server=server
)

# Azure auth related stuff
if AZURE_OAUTH:
    authentication_config = {}
    encrypted_session_secret = base64.b64decode(authentication_config['encrypted_session_secret'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(
        authentication_config['kms_project'],
        authentication_config['kms_region'],
        authentication_config['kms_keyring'],
        'flask-session-secret')
    decrypt_response = kms_client.decrypt(crypto_key_name, encrypted_session_secret)
    authentication_config['session_secret'] = decrypt_response.plaintext.decode("utf-8")

    auth = authentication.AzureOAuth(
        app,
        authentication_config['client_id'],
        authentication_config['client_secret'],
        authentication_config['expected_issuer'],
        authentication_config['expected_audience'],
        authentication_config['jwks_url'],
        authentication_config['tenant'],
        authentication_config['session_secret'],
        authentication_config['required_scopes']
    )

# # Create controls
# county_options = [
#     {"label": str(COUNTIES[county]), "value": str(county)} for county in COUNTIES
# ]

# well_status_options = [
#     {"label": str(WELL_STATUSES[well_status]), "value": str(well_status)}
#     for well_status in WELL_STATUSES
# ]

# well_type_options = [
#     {"label": str(WELL_TYPES[well_type]), "value": str(well_type)}
#     for well_type in WELL_TYPES
# ]


# # Load data
# df = pd.read_csv(DATA_PATH.joinpath("wellspublic.csv"), low_memory=False)
# df["Date_Well_Completed"] = pd.to_datetime(df["Date_Well_Completed"])
# df = df[df["Date_Well_Completed"] > dt.datetime(1960, 1, 1)]

# trim = df[["API_WellNo", "Well_Type", "Well_Name"]]
# trim.index = trim["API_WellNo"]
# dataset = trim.to_dict(orient="index")

# points = pickle.load(open(DATA_PATH.joinpath("points.pkl"), "rb"))


# Create global chart template
mapbox_access_token = "pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w"

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(le=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data", data=['1', '1','1','1']),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("logoVQD.eps"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "Analysis OHW VWT Infratechniek",
                                    style={"margin-bottom": "0px"},
                                ),
                                html.H5(
                                    "Glasvezel nieuwbouw", style={"margin-top": "0px"}
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                # html.Div(
                #     [
                #         html.A(
                #             html.Button("Learn More", id="learn-more-button"),
                #             href="https://plot.ly/dash/pricing/",
                #         )
                #     ],
                #     className="one-third column",
                #     id="button",
                # ),
            ],
            id="header",
            className="row",
            style={"margin-bottom": "25px"},
        ),
        # html.Div(
            # [
                # html.Div(
                #     [
                #         html.P(
                #             "Filter by construction date (or select range in histogram):",
                #             className="control_label",
                #         ),
                #         dcc.RangeSlider(
                #             id="year_slider",
                #             min=1960,
                #             max=2017,
                #             value=[1990, 2010],
                #             className="dcc_control",
                #         ),
                #         html.P("Filter by type OHW:", className="control_label"),
                #         dcc.RadioItems(
                #             id="well_status_selector",
                #             options=[
                #                 {"label": "All ", "value": "all"},
                #             ],
                #             value="active",
                #             labelStyle={"display": "inline-block"},
                #             className="dcc_control",
                #         ),
                #         dcc.Dropdown(
                #             id="well_statuses",
                #             options=well_status_options,
                #             multi=True,
                #             value=list(WELL_STATUSES.keys()),
                #             className="dcc_control",
                #         ),
                #         dcc.Checklist(
                #             id="lock_selector",
                #             options=[{"label": "Lock camera", "value": "locked"}],
                #             className="dcc_control",
                #             value=[],
                #         ),
                #         html.P("Filter by well type:", className="control_label"),
                #         dcc.RadioItems(
                #             id="well_type_selector",
                #             options=[
                #                 {"label": "All ", "value": "all"},
                #                 {"label": "Productive only ", "value": "productive"},
                #                 {"label": "Customize ", "value": "custom"},
                #             ],
                #             value="productive",
                #             labelStyle={"display": "inline-block"},
                #             className="dcc_control",
                #         ),
                #         dcc.Dropdown(
                #             id="well_types",
                #             options=well_type_options,
                #             multi=True,
                #             value=list(WELL_TYPES.keys()),
                #             className="dcc_control",
                #         ),
                #     ],
                #     className="pretty_container four columns",
                #     id="cross-filter-options",
                # ),
        html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="wellText"), html.P("Totaal aantal projecten")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="gasText"), html.P("Aantal projecten met OHW")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="oilText"), html.P("Aantal projecten met overfacturatie")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="waterText"), html.P("Totaal aantal meter OHW")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                    ],
                    # id="right-column",
                    # className="row flex-display",
                # ),
            # ],
            # className="row flex-display",
        ),
        # html.Div(
        #     [
        #         html.Div(
        #             [dcc.Graph(id="main_graph")],
        #             className="pretty_container seven columns",
        #         ),
        #         html.Div(
        #             [dcc.Graph(id="individual_graph")],
        #             className="pretty_container five columns",
        #         ),
        #     ],
        #     className="row flex-display",
        # ),
        html.Div(
            [
                html.Div(
                        [dcc.Graph(id="count_graph")],
                        className="pretty_container 6 columns",
                ),
                html.Div(
                        [dcc.Graph(id="count_graph2")],
                        className="pretty_container 6 columns",
                ),
            ],
            className="row flex-display",
            # style={"margin-bottom": "50px"}, 
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container six columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            # className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)


# @app.callback(
#     Output("aggregate_data", "data"),
#     [
#         Input("aggregate_data", "data"),
#         # Input("well_types", "value"),
#         # Input("year_slider", "value"),
#     ],
# )
# def update_production_text(well_status_selector):

#     # dff = filter_dataframe(df, well_statuses, well_types, year_slider)
#     # selected = dff["API_WellNo"].values
#     # index, gas, oil, water = produce_aggregate(selected, year_slider)
#     return ['1', '1','1']


# # Radio -> multi
# @app.callback(
#     Output("well_statuses", "value"), [Input("well_status_selector", "value")]
# )
# def display_status(selector):
#     if selector == "all":
#         return list(WELL_STATUSES.keys())
#     elif selector == "active":
#         return ["AC"]
#     return []


# # Radio -> multi
# @app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
# def display_type(selector):
#     if selector == "all":
#         return list(WELL_TYPES.keys())
#     elif selector == "productive":
#         return ["GD", "GE", "GW", "IG", "IW", "OD", "OE", "OW"]
#     return []


# # Slider -> count graph
# @app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
# def update_year_slider(count_graph_selected):

#     if count_graph_selected is None:
#         return [1990, 2010]

#     nums = [int(point["pointNumber"]) for point in count_graph_selected["points"]]
#     return [min(nums) + 1960, max(nums) + 1961]


# # Selectors -> well text
# @app.callback(
#     Output("well_text", "children"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
# )
# def update_well_text(well_statuses, well_types, year_slider):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)
#     return dff.shape[0]


@app.callback(
    [
        Output("wellText", "children"),
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
    ],
    [Input("aggregate_data", "data")],
)
def update_text(data):
    return data[0] + " projecten", data[1] + " projecten", data[2] + " projecten", data[3] + " meters"


# # Selectors -> main graph
# @app.callback(
#     Output("main_graph", "figure"),
#     [
#         Input("well_statuses", "value"),
#         Input("well_types", "value"),
#         Input("year_slider", "value"),
#     ],
#     [State("lock_selector", "value"), State("main_graph", "relayoutData")],
# )
# def make_main_figure(
#     well_statuses, well_types, year_slider, selector, main_graph_layout
# ):

#     dff = filter_dataframe(df, well_statuses, well_types, year_slider)

#     traces = []
#     for well_type, dfff in dff.groupby("Well_Type"):
#         trace = dict(
#             type="scattermapbox",
#             lon=dfff["Surface_Longitude"],
#             lat=dfff["Surface_latitude"],
#             text=dfff["Well_Name"],
#             customdata=dfff["API_WellNo"],
#             name=WELL_TYPES[well_type],
#             marker=dict(size=4, opacity=0.6),
#         )
#         traces.append(trace)

#     # relayoutData is None by default, and {'autosize': True} without relayout action
#     if main_graph_layout is not None and selector is not None and "locked" in selector:
#         if "mapbox.center" in main_graph_layout.keys():
#             lon = float(main_graph_layout["mapbox.center"]["lon"])
#             lat = float(main_graph_layout["mapbox.center"]["lat"])
#             zoom = float(main_graph_layout["mapbox.zoom"])
#             layout["mapbox"]["center"]["lon"] = lon
#             layout["mapbox"]["center"]["lat"] = lat
#             layout["mapbox"]["zoom"] = zoom

#     figure = dict(data=traces, layout=layout)
#     return figure


# # Main graph -> individual graph
# @app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
# def make_individual_figure(main_graph_hover):

#     layout_individual = copy.deepcopy(layout)

#     if main_graph_hover is None:
#         main_graph_hover = {
#             "points": [
#                 {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
#             ]
#         }

#     chosen = [point["customdata"] for point in main_graph_hover["points"]]
#     index, gas, oil, water = produce_individual(chosen[0])

#     if index is None:
#         annotation = dict(
#             text="No data available",
#             x=0.5,
#             y=0.5,
#             align="center",
#             showarrow=False,
#             xref="paper",
#             yref="paper",
#         )
#         layout_individual["annotations"] = [annotation]
#         data = []
#     else:
#         data = [
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Gas Produced (mcf)",
#                 x=index,
#                 y=gas,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Oil Produced (bbl)",
#                 x=index,
#                 y=oil,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#a9bb95"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#             dict(
#                 type="scatter",
#                 mode="lines+markers",
#                 name="Water Produced (bbl)",
#                 x=index,
#                 y=water,
#                 line=dict(shape="spline", smoothing=2, width=1, color="#92d8d8"),
#                 marker=dict(symbol="diamond-open"),
#             ),
#         ]
#         layout_individual["title"] = dataset[chosen[0]]["Well_Name"]

#     figure = dict(data=data, layout=layout_individual)
#     return figure


# Selectors, main graph -> aggregate graph
@app.callback(
    Output("aggregate_graph", "figure"),
    [
        Input("pie_graph", 'clickData'),
        # Input("well_types", "value"),
        # Input("year_slider", "value"),
        # Input("main_graph", "hoverData"),
    ],
)
def make_aggregate_figure(selected_data):

    cat_lookup = {'b1':'Cat1','b2':'Cat2a','b3':'Cat2b','b4':'Cat3','b5':'Cat4a','b6':'Cat4b','b7':'Cat5'}
    if selected_data == None:
        cat = 'b1'
    else:
        cat = selected_data.get('points')[0].get('label')
    
    layout_aggregate = copy.deepcopy(layout)
    
    df_OHW = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/df_OHW.pkl')
    inkoop = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/inkoop.pkl')
    revisie = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/revisie.pkl')

    # Alle projecten met OHW
    projecten = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Project']
    # Alle inkoop orders 
    inkoop = inkoop[inkoop['PROJECT'].isin(projecten)]
    # Revisies
    projecten = set(projecten) - (set(projecten) - set(revisie.columns))
    revisie = revisie[list(projecten)]
    ingeschat = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Ingeschat'].sum()
    gefactureerd = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Gefactureerd totaal'].sum()

    # revisie = revisie[list(projecten)]

    inkoop = inkoop['Ontvangen'].cumsum()#.asfreq('D', 'ffill')
    revisie = revisie.sum(axis=1)#.asfreq('D', 'ffill')
    # delta_1_t = revisie[inkoop.index[0]:inkoop.index[-1]] - inkoop

    data = [
        dict(
            type="line",
            x=inkoop.index,
            y=inkoop,
            name="Ingekocht",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=revisie.index[3:],
            y=revisie,
            name="Gefactureerd (op basis van deelrevisies)",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            mode="line",
            x=[revisie.index[3], revisie.index[-1], ],
            y=[gefactureerd,gefactureerd],
            name="Gefactureerd Totaal",
        ),
        dict(
            type="line",
            x=[revisie.index[3], revisie.index[-1]],
            y=[ingeschat, ingeschat],
            name="Ingeschat",
        ),
    ]

    layout_aggregate["title"] = "Categorie " + cat
    layout_aggregate["dragmode"] = "select"
    layout_aggregate["showlegend"] = True
    layout_aggregate["autosize"] = True

    figure = dict(data=data, layout=layout_aggregate)
    return figure


# Selectors, main graph -> pie graph
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("pie_graph", 'clickData'),
        # Input("well_types", "value"),
        # Input("year_slider", "value"),
    ],
)
def make_pie_figure(dummy):

    layout_pie = copy.deepcopy(layout)

    df_OHW = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/df_OHW.pkl')
    m_b = df_OHW.groupby('Categorie').agg({'delta_1':'sum'})
    p_b = df_OHW.groupby(['Categorie','Project']).agg({'delta_1':'sum'})

    bakjes_info = ['Er is niks gefactureerd, en de laatste deelrevisie staat op 0; (mogelijk) doorvoer van TPG loopt achter, koppeling checken', 
                   'Er is niks gefactureerd, er is weel (deel)revisie aanwezig én er is al meer ingekocht dan ingeschat; mits invoer TPG klopt, moet hier (mogelijk) meerwerk worden aangevraagd',
                   'Er is niks gefactureerd, er is weel (deel)revisie aanwezig én er is al minder ingekocht dan ingeschat; mits de invoer TPG klot, kan dit gefactureerd worden', 
                   'Facturatie is gelijk aan de revisie; (mogelijk) doorvoer van TPG loopt achter, koppeling checken', 
                   'Er is minder gefactureerd dan de revisie én er is al meer ingekocht dan ingeschat; mits de invoer TPG klopt, moet hier (mogelijk) meerwerk worden aangevraagd', 
                   'Er is minder gefactureerd dan de revisie én er is minder ingekocht dan ingeschat; mits de invoer TPG klopt, kan dit gefactureerd worden', 
                   'Er is meer gefactureerd dan de revisie; Wat kan hier aan de hand zijn? Er is alsnog meer ingekocht'] 

    data = [
        dict(
            type="pie",
            labels=["b1", "b2", "b3", "b4", "b5", "b6", "b7"],
            values=[-m_b.loc['Cat1'][0], -m_b.loc['Cat2a'][0], -m_b.loc['Cat2b'][0], -m_b.loc['Cat3'][0], \
                    -m_b.loc['Cat4a'][0], -m_b.loc['Cat4b'][0], -m_b.loc['Cat5'][0]],
            name="Project Breakdown",
            text=bakjes_info,
            hoverinfo="text",
            textinfo="percent",
            # textinfo="label+percent+name",
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8", "#92d3d8", "#92d9d8", "#92d9d2", "#92d9d3"]),
            domain={"x": [0, 0.45], "y": [0.2, 0.8]},
            # selectedpoints=None,
        ),
        dict(
            type="pie",
            labels=["b1", "b2", "b3", "b4", "b5", "b6", "b7"],
            values=[len(p_b.loc['Cat1'][:]), len(p_b.loc['Cat2a'][:]), len(p_b.loc['Cat2b'][:]), len(p_b.loc['Cat3'][:]), \
                    len(p_b.loc['Cat4a'][:]), len(p_b.loc['Cat4b'][:]), len(p_b.loc['Cat5'][:])],
            name="OHW meters Breakdown",
            text=bakjes_info,
            hoverinfo="text",
            textinfo="percent",
            hole=0.5,
            marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8", "#92d3d8", "#92d9d8", "#92d9d2", "#92d9d3"]),
            domain={"x": [0.55, 1], "y": [0.2, 0.8]},
            # selectedpoints=None,
        ),
    ]
    layout_pie["title"] = "Categorieen OHW (links aantal projecten, rechts aantal meters):"
    layout_pie["clickmode"] = "event+select"
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
        font=dict(color="#CCCCCC", size="10"), orientation="h", bgcolor="rgba(0,0,0,0)"
    )
    layout_pie["showlegend"] = False
    figure = dict(data=data, layout=layout_pie)
    return figure


# Selectors -> count graph
@app.callback(
    [Output("count_graph", "figure"),
    Output("count_graph2", "figure"),
    Output("aggregate_data", "data")
    ],
    [
        Input("pie_graph", 'clickData'),
        # Input("well_types", "value"),
        # Input("year_slider", "value"),
    ],
)
def make_count_figure(dummy):

    layout_count = copy.deepcopy(layout)

    df_OHW = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/df_OHW.pkl')
    inkoop = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/inkoop.pkl')
    revisie = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/revisie.pkl')
    workflow = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/workflow.pkl')

    # Alle projecten met OHW
    projecten = df_OHW['Project'].unique()
    # Alle inkoop orders 
    inkoop = inkoop[inkoop['PROJECT'].isin(projecten)]
    # Revisies
    projecten = set(projecten) - (set(projecten) - set(revisie.columns))
    revisie = revisie[list(projecten)]
    ingeschat = df_OHW['Ingeschat'].sum()
    gefactureerd = df_OHW['Gefactureerd totaal'].sum()

    inkoop = inkoop.groupby('LEVERDATUM_ONTVANGST').agg({'Ontvangen':'sum'})
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')
    revisie = revisie.sum(axis=1).asfreq('D', 'ffill')
    delta_1_t = revisie[inkoop.index[0]:inkoop.index[-1]] - inkoop
    

    # Totaal aantal projecten:
    nproj = workflow['Project'].nunique()
    # Nr projecten met negatieve OHW:
    nOHW = df_OHW['Project'].nunique()
    # Nr projecten met positieve OHW:
    overfacturatie = workflow[workflow['delta_1'] > 0]['Project'].nunique()
    # totaal OHW meters:
    totOHW = -df_OHW['delta_1'].sum()

    data1 = [
        dict(
            type="line",
            x=inkoop.index,
            y=inkoop,
            name="Ingekocht",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=revisie.index[3:],
            y=revisie,
            name="Gefactureerd (op basis van deelrevisies)",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            mode="line",
            x=[revisie.index[3], revisie.index[-1], ],
            y=[gefactureerd,gefactureerd],
            name="Gefactureerd Totaal",
        ),
        dict(
            type="line",
            x=[revisie.index[3], revisie.index[-1]],
            y=[ingeschat, ingeschat],
            name="Ingeschat",
        ),
    ]

    data2 = [
        dict(
            type="line",
            x=delta_1_t.index,
            y=-delta_1_t,
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
    ]

    layout_count["title"] = ""
    layout_count["dragmode"] = "select"
    layout_count["showlegend"] = True
    layout_count["autosize"] = True

    figure1 = dict(data=data1, layout=layout_count)
    figure2 = dict(data=data2, layout=layout_count)
    return [figure1, figure2,[str(nproj), str(nOHW), str(overfacturatie), str(totOHW)]]


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
