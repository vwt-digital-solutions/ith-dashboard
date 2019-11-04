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

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(le=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
)

# path to files
pickle_path = 'C:/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/Data/Aanlevering Arend/transfer-aschonewille-REF53789/191104_pickles_dashboard/'

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data", data=['1', '1','1','1']),
        dcc.Store(id="aggregate_data2", data=['1', '1','1','1']),
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
                dcc.Checklist(
                                options=[
                                            {'label': 'Vanaf nul punt', 'value': 'NL'},
                                            {'label': "Niet meenemen, afgehecht: 'Administratief Afhechting'", 'value': 'AF_1'},
                                            {'label': "Niet meenemen, afgehecht: 'Berekening restwerkzaamheden'", 'value': 'AF_2'},
                                            {'label': "Niet meenemen, afgehecht: 'Bis Gereed'", 'value': 'AF_3'},
                                        ],
                                        id='checklist_filters',
                                        value=[],
                                        className="one-third column",
                                        style={"margin-bottom": "25px"},
                ),
            ],
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5("Eerst analyseren we de totale set van projecten in workflow t.o.v. geulen graven:",
                                    style={"margin-top": "0px"}
                                ),
                            ]
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
                                    [html.H6(id="info_globaal_0"), html.P("Totaal aantal projecten")],
                                    id="info_globaal_container0",
                                    # className="mini_container",
                                    className="pretty_container 3 columns",
                                ),
                                html.Div(
                                    [html.H6(id="info_globaal_1"), html.P("Aantal projecten met OHW")],
                                    id="info_globaal_container1",
                                    className="pretty_container 3 columns",
                                ),
                                html.Div(
                                    [html.H6(id="info_globaal_2"), html.P("Aantal projecten met overfacturatie")],
                                    id="info_globaal_container2",
                                    className="pretty_container 3 columns",
                                ),
                                html.Div(
                                    [html.H6(id="info_globaal_3"), html.P("Totaal aantal meter OHW (op basis van deeldf_revisies)")],
                                    id="info_globaal_container3",
                                    className="pretty_container 3 columns",
                                ),
                            ],
                            id="info-container1",
                            className="row container-display",
                        ),
                    ],
        ),
        html.Div(
            [
                html.Div(
                        [dcc.Graph(id="Projecten_globaal_graph")],
                        className="pretty_container 6 columns",
                ),
                html.Div(
                        [dcc.Graph(id="OHW_globaal_graph")],
                        className="pretty_container 6 columns",
                ),
            ],
            id="info-container01",
            className="row flex-display",
            # style={"margin-bottom": "50px"}, 
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H5("Vervolgens kan deze set van projecten onderzocht worden op basis van verschillende categorieen, oorzaak OHW:",
                                    style={"margin-top": "40px"}
                                ),
                            ]
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
                    [
                        html.Div(
                            [html.H6(id="info_bakje_0"), html.P("Aantal meters meerwerk in de geselecteerde categorie")],
                            id="wells2",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="info_bakje_1"), html.P("Aantal projecten in deze categorie")],
                            id="gas2",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="info_bakje_2"), html.P("Totaal aantal meters in deze categorie")],
                            id="oil2",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [html.H6(id="info_bakje_3"), html.P("Totaal aantal meters OHW  (op basis van deelrevisies)")],
                            id="water2",
                            className="pretty_container 3 columns",
                        ),
                    ],
                    id="info-container3",
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
                    [dcc.Graph(id="projecten_bakje_graph")],
                    className="pretty_container 4 columns",
                ),
                html.Div(
                    [dcc.Graph(id="OHW_bakje_graph")],
                    className="pretty_container 4 columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Button(
                    html.A('download excel', id='download-link' , href='/download_excel'),
                    style={
                    'background-color': '#f9f9f9',
                    },
                ),
                # html.Button(
                #     'Uitleg categorieën',
                #     id = 'button_uitleg_cat',
                #     style={
                #     'background-color': '#f9f9f9',  
                #     # # 'color': "#339fcd",
                #     # 'border-radius': '8px',
                #     # 'display': 'inline-block',
                #     # 'padding': '7px',
                #     # 'text-align': 'center',
                #     # 'margin-top': '10px',
                #     # 'margin-bottom': '10px',
                #     # 'margin-left': '10px',
                #     # 'margin-right': '10px',
                #     },
                # )
            ],
            style={
                'margin-left': '13px'
            },
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Download function
@app.callback(
    Output('download-link' ,'href'),
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
    cat_lookup = {'b1':'Cat1','b2':'Cat2','b3':'Cat3','b4':'Cat4','b5':'Cat6'}
    df_workflow = pd.read_pickle(pickle_path + 'workflow.pkl')
    # Alle projecten met OHW
    projecten = df_workflow[df_workflow['Categorie'] == cat_lookup.get(cat)]
    df = projecten[['Project','Gefactureerd totaal', 'Aangeboden', 'Ingekocht','df_revisie totaal','Meerwerk', 'Categorie']]

    #Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1")
    excel_writer.save()
    excel_data = strIO.getvalue()
    strIO.seek(0)

    #Name download file
    Filename = 'Info_project_' + cat_lookup.get(cat) + '_' + dt.datetime.now().strftime('%d-%m-%Y') + '.xlsx'
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)

# update info containers
@app.callback(
    [
        Output("info_globaal_0", "children"),
        Output("info_globaal_1", "children"),
        Output("info_globaal_2", "children"),
        Output("info_globaal_3", "children"),
        Output("info_bakje_0", "children"),
        Output("info_bakje_1", "children"),
        Output("info_bakje_2", "children"),
        Output("info_bakje_3", "children"),
    ],
    [Input("aggregate_data", "data"),
    Input("aggregate_data2", "data")],
)
def update_text(data1, data2):
    return data1[0] + " projecten", data1[1] + " projecten", data1[2] + " projecten", data1[3] + " meters", \
           data2[0] + " meters", data2[1] + " projecten", data2[2] + " meters", data2[3] + " meters" 

# Callback voor globale grafieken
@app.callback(
    [Output("Projecten_globaal_graph", "figure"),
    Output("OHW_globaal_graph", "figure"),
    Output("aggregate_data", "data")
    ],
    [
        Input("checklist_filters", 'value'),
    ],
)
def make_global_figures(filter_selectie):

    layout_global_projects = copy.deepcopy(layout)
    layout_global_projects_OHW = copy.deepcopy(layout)

    # df_OHW = pd.read_pickle(pickle_path + 'df_OHW.pkl')
    df_inkoop = pd.read_pickle(pickle_path + 'inkoop.pkl')
    df_revisie = pd.read_pickle(pickle_path + 'revisie.pkl')
    df_workflow = pd.read_pickle(pickle_path + 'workflow.pkl')

    # code voor het maken van het nulpunt...projecten met 0 inkoop en 0 gefactureerd...
    # df_workflow[~((df_workflow['Gefactureerd totaal'] == 0) & (df_workflow['Ingekocht'] == 0))]['Project'].to_pickle(pickle_path + pcodes_nulpunt_' + dt.datetime.now().strftime('%d-%m-%Y') + '.pkl')
    pcodes_nulpunt = pd.read_pickle(pickle_path + '../../../Nulpunten/pcodes_nulpunt_31-10-2019.pkl')

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin(pcodes_nulpunt)] 

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]
    
    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?

    if df_OHW.empty: # alleen nodig voor leeg nulpunt
        df_OHW.loc['30-10-2019'] = [0,0,0,0,0,0,0,0,0,0]
        df_OHW.loc['31-10-2019'] = [0,0,0,0,0,0,0,0,0,0]
        df_OHW.index = pd.to_datetime(df_OHW.index)

    # Alle projecten met OHW
    projecten = df_OHW['Project'].unique()
    # Alle df_inkoop orders 
    df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projecten)]
    if df_inkoop.empty: # alleen nodig voor leeg nulpunt
            df_inkoop.loc['30-10-2019'] = [0,0,0,0,0,0,0,0,0,0,0]
            df_inkoop.loc['31-10-2019'] = [0,0,0,0,0,0,0,0,0,0,0]
            df_inkoop.index = pd.to_datetime(df_inkoop.index)
    
    # df_revisies
    projecten = set(projecten) - (set(projecten) - set(df_revisie.columns))
    df_revisie = df_revisie[list(projecten)]
    
    # waardes voor grafieken
    ingeschat = df_OHW['Aangeboden'].sum()
    gefactureerd = df_OHW['Gefactureerd totaal'].sum()
    inkoop = df_inkoop.groupby('LEVERDATUM_ONTVANGST').agg({'Ontvangen':'sum'})
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')
    revisie = df_revisie.sum(axis=1).asfreq('D', 'ffill')
    OHW = revisie[inkoop.index[0]:inkoop.index[-1]] - inkoop
    
    # Totaal aantal projecten:
    nproj = df_workflow['Project'].nunique()
    # Nr projecten met negatieve OHW:
    nOHW = len(projecten)
    # Nr projecten met positieve OHW:
    noverfac = df_workflow[df_workflow['delta_1'] > 0]['Project'].nunique()
    # totaal OHW meters:
    totOHW = -df_OHW['delta_1'].sum().round(0)

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
            name="deelrevisies Totaal",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            mode='markers',
            marker=dict(size=12, symbol='triangle-left'),
            symbol='<',
            x=[pd.datetime.now()],
            y=[gefactureerd],
            name="Gefactureerd Totaal",
        ),
        dict(
            type="line",
            mode='markers',
            marker=dict(size=12, symbol='triangle-left'),
            x=[pd.datetime.now()],
            y=[ingeschat],
            name="Ingeschat",
        ),
    ]

    data2 = [
        dict(
            type="line",
            x=OHW.index,
            y=-OHW,
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
    ]

    layout_global_projects["title"] = "Projecten met OHW"
    layout_global_projects["dragmode"] = "select"
    layout_global_projects["showlegend"] = True
    layout_global_projects["autosize"] = True
    layout_global_projects["yaxis"] = dict(title='[m]')
    layout_global_projects["line"]=dict(dash='dash')

    layout_global_projects_OHW["title"] = "OHW (op basis van deelrevisies)"
    layout_global_projects_OHW["dragmode"] = "select"
    layout_global_projects_OHW["showlegend"] = True
    layout_global_projects_OHW["autosize"] = True
    layout_global_projects_OHW["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_global_projects)
    figure2 = dict(data=data2, layout=layout_global_projects_OHW)
    return [figure1, figure2,[str(nproj), str(nOHW), str(noverfac), str(totOHW)]]

# Callback voor taartdiagram
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("checklist_filters", 'value'),
    ],
)
def make_pie_figure(filter_selectie):

    layout_pie = copy.deepcopy(layout)

    df_workflow = pd.read_pickle(pickle_path + 'workflow.pkl')
    pcodes_nulpunt = pd.read_pickle(pickle_path + '../../../Nulpunten/pcodes_nulpunt_31-10-2019.pkl')

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin(pcodes_nulpunt)] 

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]
    
    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?
  
    if df_OHW.empty: # alleen nodig voor leeg nulpunt
        df_OHW.loc['25-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat1']
        df_OHW.loc['26-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat2']
        df_OHW.loc['27-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat3']
        df_OHW.loc['28-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat4']
        df_OHW.loc['29-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat5']
        df_OHW.loc['30-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat6']
        df_OHW.loc['31-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat7']
        df_OHW.index = pd.to_datetime(df_OHW.index)

    meters_cat = -df_OHW.groupby('Categorie').agg({'delta_1':'sum'})

    beschrijving_cat = [
        'moet upgedate!', 
        'gefactureerd=0, revisie>0, ingekocht > ingeschat',
        'gefactureerd=0, revisie>0, ingekocht < ingeschat', 
        'gefactureerd = revisie', 
        'gefactureerd < revisie, ingekocht > ingeschat',
        'test1',
        'test2' 
    ] 

    cat1 = meters_cat.loc['Cat1'][0].round(0)
    cat2 = meters_cat.loc['Cat2'][0].round(0)
    cat3 = meters_cat.loc['Cat3'][0].round(0)
    cat4 = meters_cat.loc['Cat4'][0].round(0)
    cat5 = meters_cat.loc['Cat5'][0].round(0)
    cat6 = df_workflow['Extra werk'].sum().round(0)
    cat7 = df_workflow[df_workflow['Afgesloten_b_nummer'] == True]['delta_1'].sum().round(0)

    data = [
        dict(
            type="pie",
            labels=["b1", "b2", "b3", "b4", "b5", "b6", "b7"],
            values=[cat1, cat2, cat3, cat4, cat5, cat6, cat7],
            # name=["b111", "b2", "b3", "b4", "b5", "b6", "b7"],
            text=beschrijving_cat,
            hoverinfo="text",
            textinfo="value",
            hole=0.5,
            marker=dict(colors=["#30304b", "#3b496c", "#3f648d", "#3d81ae", "#339fcd","#388fcd", "#491fcd"]),
            domain={"x": [0, 1], "y": [0.30, 1]},
        ),
    ]
    layout_pie["title"] = "Categorieen OHW (aantal meters):"
    layout_pie["clickmode"] = "event+select"
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
        font=dict(color="#CCCCCC", size="14"), orientation="v", bgcolor="rgba(0,0,0,0)", traceorder='normal', itemclick=False, xanchor='bottom'
    )
    layout_pie["showlegend"] = True
    layout_pie["height"] = 500    
    figure = dict(data=data, layout=layout_pie)
    return figure


# grafieken voor het geselecteerde bakje in het taartdiagram
@app.callback(
    [Output("projecten_bakje_graph", "figure"),
     Output("OHW_bakje_graph", "figure"),
     Output("aggregate_data2", "data"),
    ],
    [
        Input("pie_graph", 'clickData'),
        Input("checklist_filters", 'value')
    ],
)
def figures_selected_category(selected_category, filter_selectie):

    cat_lookup = {'b1':'Cat1','b2':'Cat2','b3':'Cat3','b4':'Cat4','b5':'Cat6'}
    if selected_category == None:
        cat = 'b1'
    else:
        cat = selected_category.get('points')[0].get('label')
    
    layout_graph_selected_projects = copy.deepcopy(layout)
    layout_graph_selected_projects_OHW = copy.deepcopy(layout)
    
    df_workflow = pd.read_pickle(pickle_path + 'workflow.pkl') 
    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    df_inkoop = pd.read_pickle(pickle_path + 'inkoop.pkl')
    df_revisie = pd.read_pickle(pickle_path + 'revisie.pkl')
    pcodes_nulpunt = pd.read_pickle(pickle_path + '../../../Nulpunten/pcodes_nulpunt_31-10-2019.pkl')

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin(pcodes_nulpunt)] 

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]
    
    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?
    if df_OHW.empty: # alleen nodig voor leeg nulpunt
        df_OHW.loc['30-10-2019'] = [0,0,0,0,0,0,0,0,0,0]
        df_OHW.loc['31-10-2019'] = [0,0,0,0,0,0,0,0,0,0]
        df_OHW.index = pd.to_datetime(df_OHW.index)

    # Alle projecten met OHW
    projecten = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Project']
    # Alle inkoop orders 
    df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projecten)]
    if df_inkoop.empty: # alleen nodig voor leeg nulpunt
        df_inkoop.loc['30-10-2019'] = [0,0,0,0,0,0,0,0,0,0,0]
        df_inkoop.loc['31-10-2019'] = [0,0,0,0,0,0,0,0,0,0,0]
        df_inkoop.index = pd.to_datetime(df_inkoop.index)
    
    # revisie
    projecten = set(projecten) - (set(projecten) - set(df_revisie.columns))
    df_revisie = df_revisie[list(projecten)]
    
    # waardes voor grafieken
    ingeschat = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Aangeboden'].sum()
    gefactureerd = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Gefactureerd totaal'].sum()
    inkoop = df_inkoop.groupby('LEVERDATUM_ONTVANGST').agg({'Ontvangen':'sum'})
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')
    revisie = df_revisie.sum(axis=1).asfreq('D', 'ffill')
    OHW = revisie[inkoop.index[0]:inkoop.index[-1]] - inkoop

    # Totaal aantal projecten:
    nproj = len(projecten)
    # Aantal meters OHW in deze selectie:
    mOHW = -OHW[-1].round(0)
    # Aantal projecten met positieve OHW:
    ntotmi = inkoop[-1].round(0)
    # meerwerk in deze categorie
    meerw = df_OHW[df_OHW['Categorie'] == cat_lookup.get(cat)]['Extra werk'].sum().round(0)

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
            name="deelrevisies Totaal",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            mode='markers',
            marker=dict(size=12, symbol='triangle-left'),
            x=[pd.datetime.now()],
            y=[gefactureerd],
            name="Gefactureerd Totaal",
        ),
        dict(
            type="line",
            mode='markers',
            marker=dict(size=12, symbol='triangle-left'),
            x=[pd.datetime.now()],
            y=[ingeschat],
            name="Ingeschat",
        ),
    ]

    data2 = [
        dict(
            type="line",
            x=OHW.index,
            y=-OHW,
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
    ]

    beschrijving_cat = [
        'gefactureerd=0, deel revisie=0', 
        'gefactureerd=0, revisie>0, ingekocht > ingeschat',
        'gefactureerd=0, revisie>0, ingekocht < ingeschat', 
        'gefactureerd = revisie', 
        'gefactureerd < revisie, ingekocht > ingeschat', 
        'gefactureerd > revisie, ingekocht < ingeschat', 
        'gefactureerd > revisie'
    ]

    layout_graph_selected_projects["title"] = "Categorie " + cat + ':<br>' + ' (' + beschrijving_cat[int(cat[1])-1] + ')'
    layout_graph_selected_projects["dragmode"] = "select"
    layout_graph_selected_projects["showlegend"] = True
    layout_graph_selected_projects["autosize"] = True
    layout_graph_selected_projects["yaxis"] = dict(title='[m]')

    layout_graph_selected_projects_OHW["title"] = "OHW (op basis van deelrevisies)"
    layout_graph_selected_projects_OHW["dragmode"] = "select"
    layout_graph_selected_projects_OHW["showlegend"] = True
    layout_graph_selected_projects_OHW["autosize"] = True
    layout_graph_selected_projects_OHW["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_graph_selected_projects)
    figure2 = dict(data=data2, layout=layout_graph_selected_projects_OHW)
    return [figure1, figure2, [str(meerw), str(nproj), str(ntotmi), str(mOHW)]]

# Main
if __name__ == "__main__":
    app.run_server(debug=True)
