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

# Download button 
import io
from flask import send_file


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
        dcc.Store(id="aggregate_data2", data=['1', '1','1','1']),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("vqd.png"),
                            id="vqd-image",
                            style={
                                "height": "100px",
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
                                    "Analyse OHW VWT Infratechniek",
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
            ],
            id="header",
            className="row",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [html.H6(id="wellText0"), html.P("Eerst analyseren we de totale set van projecten in workflow t.o.v. geulen graven:")],
                            id="wells0",
                            className="pretty_container 1 columns",
                        ),
                    ],
                    id="info-container0",
                    className="row container-display",
                ),
            ],
        ),
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
                                    [html.H6(id="waterText"), html.P("Totaal aantal meter OHW (op basis van deelrevisies)")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                    ],
        ),
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
                    [
                        html.Div(
                            [html.H6(id="wellText01"), html.P("Vervolgens kan deze set van projecten onderzocht worden op basis van verschillende categorieen, oorzaak OHW:")],
                            id="wells01",
                            className="pretty_container 1 columns",
                        ),
                    ],
                    id="info-container01",
                    className="row container-display",
                ),
            ],
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [html.H6(id="wellText2"), html.P("Aantal meters meerwerk in de geselecteerde categorie")],
                            id="wells2",
                            # className="mini_container",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="gasText2"), html.P("Aantal projecten in deze categorie")],
                            id="gas2",
                            # className="mini_container",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="oilText2"), html.P("Totaal aantal meters in deze categorie")],
                            id="oil2",
                            # className="mini_container",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="waterText2"), html.P("Totaal aantal meters OHW  (op basis van deelrevisies)")],
                            id="water2",
                            # className="mini_container",
                            className="pretty_container 3 columns",
                        ),
                    ],
                    id="info-container2",
                    className="row container-display",
                ),
            ],
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container 4 columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container 4 columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph2")],
                    className="pretty_container 4 columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Button(
                    html.A('download excel', id='my-link', href='/download_excel'),
                    style={
                    'background-color': '#f9f9f9',  
                    # # 'color': "#339fcd",
                    # 'border-radius': '8px',
                    # 'display': 'inline-block',
                    # 'padding': '7px',
                    # 'text-align': 'center',
                    # 'margin-top': '10px',
                    # 'margin-bottom': '10px',
                    # 'margin-left': '10px',
                    # 'margin-right': '10px',
                    },
                ),
                html.Button(
                    'Uitleg categorieën',
                    id = 'uitleg_cat',
                    style={
                    'background-color': '#f9f9f9',  
                    # # 'color': "#339fcd",
                    # 'border-radius': '8px',
                    # 'display': 'inline-block',
                    # 'padding': '7px',
                    # 'text-align': 'center',
                    # 'margin-top': '10px',
                    # 'margin-bottom': '10px',
                    # 'margin-left': '10px',
                    # 'margin-right': '10px',
                    },
                )
            ],
            style={
                'margin-left': '13px'
            },
            # className= "pretty_container"
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Download function
@app.callback(
    Output('my-link','href'),
    [
        Input('pie_graph', 'clickData')
    ],
)
def update_link(clickData):

    if clickData == None:
        cat = 'b1'
    else:
        cat = clickData.get('points')[0].get('label')
    return '/download_excel?categorie={}'.format(cat)

@app.server.route('/download_excel')
def download_excel():
    #Create DF
    cat = flask.request.args.get('categorie')
    cat_lookup = {'b1':'Cat1','b2':'Cat2a','b3':'Cat2b','b4':'Cat3','b5':'Cat4a','b6':'Cat4b','b7':'Cat5'}
    df_OHW = pd.read_pickle('C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/pickles_dashboard/df_OHW.pkl')
    # Alle projecten met OHW
    projecten = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]
    df = projecten[['Project','Gefactureerd totaal', 'Ingeschat', 'Ingekocht','Revisie totaal','Meerwerk', 'Categorie']]

    #Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1")
    excel_writer.save()
    excel_data = strIO.getvalue()
    strIO.seek(0)

    return send_file(strIO,
                     attachment_filename='test.xlsx',
                     as_attachment=True)


# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("count_graph", "figure")],
)

@app.callback(
    [
        Output("wellText", "children"),
        Output("gasText", "children"),
        Output("oilText", "children"),
        Output("waterText", "children"),
        Output("wellText2", "children"),
        Output("gasText2", "children"),
        Output("oilText2", "children"),
        Output("waterText2", "children"),
    ],
    [Input("aggregate_data", "data"),
    Input("aggregate_data2", "data")],
)
def update_text(data1, data2):
    return data1[0] + " projecten", data1[1] + " projecten", data1[2] + " projecten", data1[3] + " meters", \
           data2[0] + " meters", data2[1] + " projecten", data2[2] + " meters", data2[3] + " meters" 

# Selectors, main graph -> aggregate graph
@app.callback(
    [Output("aggregate_graph", "figure"),
     Output("aggregate_graph2", "figure"),
     Output("aggregate_data2", "data"),
    ],
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
    layout_aggregate2 = copy.deepcopy(layout)
    
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

    inkoop = inkoop.groupby('LEVERDATUM_ONTVANGST').agg({'Ontvangen':'sum'})
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')
    revisie = revisie.sum(axis=1).asfreq('D', 'ffill')
    delta_1_t = revisie[inkoop.index[0]:inkoop.index[-1]] - inkoop

    # Totaal aantal projecten:
    nproj = len(projecten)
    # Nr projecten met negatieve OHW:
    nOHW = -delta_1_t[-1]
    # Nr projecten met positieve OHW:
    ntotmi = inkoop[-1]
    # totaal OHW meters:
    totOHW = -df_OHW['delta_1'].sum()
    meerw = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Meerwerk'].sum()

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
            name="Deelrevisies Totaal",
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

    bakjes_info = [
        'gefactureerd=0, deelrevisie=0', 
        'gefactureerd=0, revisie>0, ingekocht > ingeschat',
        'gefactureerd=0, revisie>0, ingekocht < ingeschat', 
        'gefactureerd = revisie', 
        'gefactureerd < revisie, ingekocht > ingeschat', 
        'gefactureerd > revisie, ingekocht < ingeschat', 
        'gefactureerd > revisie'
    ]

    layout_aggregate["title"] = "Categorie " + cat + ':<br>' + ' (' + bakjes_info[int(cat[1])-1] + ')'
    layout_aggregate["dragmode"] = "select"
    layout_aggregate["showlegend"] = True
    layout_aggregate["autosize"] = True
    layout_aggregate["yaxis"] = dict(title='[m]')

    layout_aggregate2["title"] = "OHW (op basis van deelrevisies)"
    layout_aggregate2["dragmode"] = "select"
    layout_aggregate2["showlegend"] = True
    layout_aggregate2["autosize"] = True
    layout_aggregate2["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_aggregate)
    figure2 = dict(data=data2, layout=layout_aggregate2)
    return [figure1, figure2, [str(meerw), str(nproj), str(ntotmi), str(nOHW)]]


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

    bakjes_info = [
        'gefactureerd=0, deelrevisie=0', 
        'gefactureerd=0, revisie>0, ingekocht > ingeschat',
        'gefactureerd=0, revisie>0, ingekocht < ingeschat', 
        'gefactureerd = revisie', 
        'gefactureerd < revisie, ingekocht > ingeschat', 
        'gefactureerd > revisie, ingekocht < ingeschat', 
        'gefactureerd > revisie,'
    ] 

    data = [
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
            # marker=dict(colors=["#fac1b7", "#a9bb95", "#92d8d8", "#92d3d8", "#92d9d8", "#92d9d2", "#92d9d3"]),
            marker=dict(colors=["#30304b", "#3b496c", "#3f648d", "#3d81ae", "#339fcd", "#20bfe8", "#00dfff"]),
            # domain={"x": [0.55, 1], "y": [0.2, 0.8]},
            # selectedpoints=None,
        ),
    ]
    layout_pie["title"] = "Categorieen OHW (aantal meters):"
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
    layout_count2 = copy.deepcopy(layout)

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
            name="Deelrevisies Totaal",
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

    layout_count["title"] = "Projecten met OHW"
    layout_count["dragmode"] = "select"
    layout_count["showlegend"] = True
    layout_count["autosize"] = True
    layout_count["yaxis"] = dict(title='[m]')

    layout_count2["title"] = "OHW (op basis van deelrevisies)"
    layout_count2["dragmode"] = "select"
    layout_count2["showlegend"] = True
    layout_count2["autosize"] = True
    layout_count2["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_count)
    figure2 = dict(data=data2, layout=layout_count2)
    return [figure1, figure2,[str(nproj), str(nOHW), str(overfacturatie), str(totOHW)]]


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
