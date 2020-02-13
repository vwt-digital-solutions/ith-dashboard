import copy
import flask
import io
import config
import datetime as dt
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import ast
from flask import send_file
from google.cloud import firestore
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from elements import table_styles
from app import app, cache

# layout graphs
layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(le=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)


# APP LAYOUT
def get_body():
    page = html.Div(
        [
            dcc.Store(id="aggregate_data",
                      data={'0': '0', '1': '0', '2': '0'}),
            dcc.Store(id="aggregate_data2",
                      data={'0': '0', '1': '0', '2': '0'}),
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
                                        "Glasvezel nieuwbouw",
                                        style={"margin-top": "0px"}
                                    ),
                                    html.P(),
                                    html.P("(Laatste nieuwe data: 23-12-2019)")
                                ],
                                style={"margin-left": "-120px"},
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
                                [
                                    html.P("Presets:"),
                                    dcc.Dropdown(
                                        options=[
                                            {'label': 'Vanaf nul punt [NL]',
                                                'value': 'NL'},
                                            {'label': """Niet meenemen, afgehecht:
                                                'Administratief Afhechting'
                                                [AF_1]""",
                                                'value': 'AF_1'},
                                            {'label': """Niet meenemen, afgehecht:
                                                'Berekening restwerkzaamheden'
                                                [AF_2]""",
                                                'value': 'AF_2'},
                                            {'label': """Niet meenemen, afgehecht:
                                                'Bis Gereed'
                                                [AF_3]""",
                                                'value': 'AF_3'},
                                        ],
                                        id='checklist_filters',
                                        value=['AF_1', 'AF_2', 'AF_3'],
                                        multi=True,
                                    ),
                                ],
                                id="filter_container",
                                className="pretty_container_title columns",
                            ),
                            html.Div(
                                [
                                    html.P("Filter regio:"),
                                    dcc.Dropdown(
                                        options=[
                                            {'label': "'t Harde",
                                                'value': '410.0'},
                                            {'label': "Uden",
                                                'value': '420.0'},
                                            {'label': "Papendrecht",
                                                'value': '430.0'},
                                            {'label': "Omzetten",
                                                'value': '000'},
                                        ],
                                        id='checklist_filters2',
                                        value=['410.0', '420.0', '430.0'],
                                        multi=True,
                                    ),
                                ],
                                id="filter_container",
                                className="pretty_container_title columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="download"),
                                    html.P("Excel downloads:"),
                                    html.Button(
                                        html.A(
                                            'download excel (selected categories)',
                                            id='download-link',
                                            href="""/download_excel?categorie=1
                                                    &filters=['empty']""",
                                            style={"color": "white",
                                                   "text-decoration": "none"}
                                        ),
                                        style={"background-color": "#009FDF",
                                               "margin-bottom": "5px",
                                               "display": "block"}

                                    ),
                                    html.Button(
                                        html.A(
                                            'download excel (all categories)',
                                            id='download-link1',
                                            href="""/download_excel1
                                                    ?filters=['empty']""",
                                            style={"color": "white",
                                                   "text-decoration": "none"}
                                        ),
                                        style={"background-color": "#009FDF",
                                               "margin-bottom": "5px",
                                               "display": "block"}
                                    ),
                                    html.Button(
                                        html.A(
                                            '''download excel
                                                (inkooporders meerwerk)''',
                                            id='download-link2',
                                            href="""/download_excel2?
                                                    filters=['empty']""",
                                            style={"color": "white",
                                                   "text-decoration": "none"}
                                        ),
                                        style={"background-color": "#009FDF",
                                               "margin-bottom": "5px",
                                               "display": "block"}
                                    ),
                                ],
                                id="download_container",
                                className="pretty_container_title columns",
                            ),
                        ],
                        id="info-container",
                        className="container-display",
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H5(
                                "Totaal overzicht OHW analyse:",
                                style={"margin-top": "0px"}
                            ),
                        ],
                        id='uitleg_1',
                        className="pretty_container_title columns",
                    ),
                ],
                className="container-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(id="dp_info_globaal_0"),
                                    html.P("Aantal projecten met OHW totaal")
                                ],
                                id="dp_info_globaal_container0",
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="dp_info_globaal_1"),
                                    html.P("Aantal distributiepunten OHW totaal")
                                ],
                                id="dp_info_globaal_container1",
                                className="pretty_container 3 columns",
                            ),
                        ],
                        id="info-container1",
                        className="container-display",
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div(
                            [dcc.Graph(id="OHW_globaal_graph")],
                            className="pretty_container column",
                    ),
                ],
                id="main_graphs",
                className="container-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H5(
                                """
                                Categorisering van de projecten met OHW:
                                """,
                                style={"margin-top": "0px"}
                            ),
                        ],
                        id='uitleg_2',
                        className="pretty_container_title columns",
                    ),
                ],
                className="container-display",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H6(id="info_bakje_0"),
                                    html.P("Aantal projecten in categorie")

                                ],
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_bakje_1"),
                                    html.P("Aantal distributiepunten OHW in categorie")
                                ],
                                className="pretty_container 3 columns",
                            ),
                        ],
                        id="info-container3",
                        className="container-display",
                    ),
                ],
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(id="pie_graph"),
                            html.Div(
                                [
                                    dbc.Button(
                                        'Uitleg categorieën',
                                        id='uitleg_button'
                                    ),
                                    html.Div(
                                        [
                                            dcc.Markdown(
                                                config.uitleg_categorie
                                            )
                                        ],
                                        id='uitleg_collapse',
                                        hidden=True,
                                    )
                                ],
                            ),
                        ],
                        className="pretty_container column",
                    ),
                    html.Div(
                        dcc.Graph(id="OHW_bakje_graph"),
                        className="pretty_container column",
                    ),
                ],
                className="container-display",
            ),
            html.Div(
                id='status_table_ext',
                className="pretty_container",
                # hidden=True,
            ),
        ],
        id="mainContainer",
        style={"display": "flex", "flex-direction": "column"},
    )
    return page

# CALBACK FUNCTIONS
# Informatie button
@app.callback(
    Output("uitleg_collapse_DP", "hidden"),
    [Input("uitleg_button", "n_clicks")],
    [State("uitleg_collapse_DP", "hidden")],
)
def toggle_collapse_DP(n, is_open):
    if n:
        return not is_open
    return is_open


# Info containers
@app.callback(
    [
        Output("dp_info_globaal_0", "children"),
        Output("dp_info_globaal_1", "children"),
        Output("dp_info_bakje_0", "children"),
        Output("dp_info_bakje_1", "children"),
    ],
    [
        Input("aggregate_data", "data"),
        Input("aggregate_data2", "data")
    ],
)
def update_text(data1, data2):
    return [
        data1.get('0') + " projecten",
        data1.get('1') + " distributiepunten",
        data2.get('0') + " projecten",
        data2.get('1') + " distributiepunten",
    ]

# Globale grafieken
@app.callback(
    [Output("OHW_globaal_graph_DP", "figure"),
     Output("pie_graph_DP", "figure"),
     Output("aggregate_data_DP", "data")
     ],
    [Input("checklist_filters", 'value'),
     Input("checklist_filters2", 'value')
     ]
)
def make_global_figures(preset_selectie, filter_selectie):
    if filter_selectie is None:
        raise PreventUpdate
    df, df2 = data_from_DB_DP(preset_selectie)
    df = df[df['RegioVWT'].isin(filter_selectie)]
    category = 'global'
    if df.empty | df2.empty:
        raise PreventUpdate
    fig_OHW_DP, fig_pie_DP, _, stats = generate_graph(category, df, df2)
    return [fig_OHW_DP, fig_pie_DP, stats]

# HELPER FUNCTIES
@cache.memoize()
def data_from_DB_DP(filter_selectie):
    db = firestore.Client()
    p_ref = db.collection('Projecten_7')
    inkoop_ref = db.collection('Inkooporders_5')

    def get_dataframe(docs, dataframe):
        for doc in docs:
            Pnummer = doc.id
            doc = doc.to_dict()
            doc['Pnummer'] = Pnummer
            dataframe += [doc]
        return dataframe

    dataframe = []
    if not ('NL' in filter_selectie):
        docs = p_ref.where('OHW_ever', '==', True).where('Afgehecht', '==', 'niet afgehecht').stream()
        dataframe = get_dataframe(docs, dataframe)
        if not ('AF_1' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where('Afgehecht', '==', 'Administratief Afhechting').stream()
            dataframe = get_dataframe(docs, dataframe)
        if not ('AF_2' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where('Afgehecht', '==', 'Berekening restwerkzaamheden').stream()
            dataframe = get_dataframe(docs, dataframe)
        if not ('AF_3' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where('Afgehecht', '==', 'Bis Gereed').stream()
            dataframe = get_dataframe(docs, dataframe)
    elif ('NL' in filter_selectie):
        docs = p_ref.where('OHW_ever', '==', True).where(
            'Afgehecht', '==', 'niet afgehecht').where('nullijn', '==', False).stream()
        dataframe = get_dataframe(docs, dataframe)
        if not ('AF_1' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where(
                'Afgehecht', '==', 'Administratief Afhechting').where('nullijn', '==', False).stream()
            dataframe = get_dataframe(docs, dataframe)
        if not ('AF_2' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where(
                'Afgehecht', '==', 'Berekening restwerkzaamheden').where('nullijn', '==', False).stream()
            dataframe = get_dataframe(docs, dataframe)
        if not ('AF_3' in filter_selectie):
            docs = p_ref.where('OHW_ever', '==', True).where(
                'Afgehecht', '==', 'Bis Gereed').where('nullijn', '==', False).stream()
            dataframe = get_dataframe(docs, dataframe)
    else:
        docs = p_ref.where('OHW_ever', '==', True).stream()
        dataframe = get_dataframe(docs, dataframe)
    df = pd.DataFrame(dataframe)
    df = df.fillna(False)
    df.loc[~df['RegioVWT'].isin(['410.0', '420.0', '430.0']), ('RegioVWT')] = '000'

    docs = inkoop_ref.where('EW', '==', True).where('DP', '==', False).where('Behandeld', '==', False).stream()
    dataframe2 = []
    for doc in docs:
        inkoopid = doc.id
        doc = doc.to_dict()
        for key in doc['Ontvangen']:
            dataframe2 += [{'Project': key,
                            'Extra werk': doc['Ontvangen'][key],
                            'Inkooporder': inkoopid}]
    df2 = pd.DataFrame(dataframe2)

    return df, df2
