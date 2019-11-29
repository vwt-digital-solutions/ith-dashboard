import copy
import pathlib
import flask
import dash
import base64
import os
import io
import config
import datetime as dt
import pandas as pd
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table

from flask import send_file
from google.cloud import kms_v1
from dash.dependencies import Input, Output, State
from authentication.azure_auth import AzureOAuth
from elements import table_styles
from flask_caching import Cache

# import sqlalchemy as db
# from sqlalchemy import create_engine

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
AZURE_OAUTH = os.getenv('AD_AUTH', False)

# Initiate flask server and dash application
server = flask.Flask(__name__)
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    server=server
)
cache = Cache(app.server, config={
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
})
app.config.suppress_callback_exceptions = True
app.title = "Analyse OHW"

# Azure AD authentication
if config.authentication:
    encrypted_session_secret = base64.b64decode(
        config.authentication['encrypted_session_secret'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(
        config.authentication['kms_project'],
        config.authentication['kms_region'],
        config.authentication['kms_keyring'],
        'flask-session-secret')
    decrypt_response = kms_client.decrypt(
        crypto_key_name, encrypted_session_secret)
    config.authentication['session_secret'] = \
        decrypt_response.plaintext.decode("utf-8")

    auth = AzureOAuth(
        app,
        config.authentication['client_id'],
        config.authentication['client_secret'],
        config.authentication['expected_issuer'],
        config.authentication['expected_audience'],
        config.authentication['jwks_url'],
        config.authentication['tenant'],
        config.authentication['session_secret'],
        config.authentication['role'],
        config.authentication['required_scopes']
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

# APP LAYOUT
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data",
                  data={'0': '1', '1': '1', '2': '1'}),
        dcc.Store(id="aggregate_data2",
                  data={'0': '1', '1': '1', '2': '1'}),
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
                                html.P("(Laatste nieuwe data: 26-11-2019)")
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
                                html.H6(id="filters"),
                                html.P("Filters:"),
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
                            className="pretty_container 3 columns",
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
                                               "text-decoration": "none"
                                               }
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
                                               "text-decoration": "none"
                                               }
                                    ),
                                    style={"background-color": "#009FDF",
                                           "margin-bottom": "5px",
                                           "display": "block"
                                           }
                                ),
                                html.Button(
                                    html.A(
                                        '''download excel
                                             (inkooporders meerwerk)''',
                                        id='download-link2',
                                        href="""/download_excel2?
                                                filters=['empty']""",
                                        style={"color": "white",
                                               "text-decoration": "none"
                                               }
                                    ),
                                    style={"background-color": "#009FDF",
                                           "margin-bottom": "5px",
                                           "display": "block"
                                           }
                                ),
                            ],
                            id="download_container",
                            className="pretty_container 3 columns",
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
                    [
                        html.H5(
                            "Totaal overzicht OHW analyse:",
                            style={"margin-top": "0px"}
                        ),
                    ],
                    id='uitleg_1',
                    className="pretty_container 1 columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6(id="info_globaal_0"),
                                html.P("Totaal aantal projecten")
                            ],
                            id="info_globaal_container0",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="info_globaal_1"),
                                html.P("Aantal projecten met OHW")
                            ],
                            id="info_globaal_container1",
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="info_globaal_2"),
                                html.P("Totaal aantal meter OHW")
                            ],
                            id="info_globaal_container2",
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
                    className="pretty_container 1 columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6(id="info_bakje_0"),
                                html.P("Aantal projecten in deze categorie")

                            ],
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="info_bakje_1"),
                                html.P("Totaal aantal meters OHW")
                            ],
                            className="pretty_container 3 columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="info_bakje_2"),
                                html.P("""Aantal meters meerwerk in
                                         de geselecteerde categorie""")
                            ],
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
                html.Div(
                    id='status_table_ext',
                    className="pretty_container 1 columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# CALBACK FUNCTIONS
# Informatie button
@app.callback(
    Output("uitleg_collapse", "hidden"),
    [Input("uitleg_button", "n_clicks")],
    [State("uitleg_collapse", "hidden")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# Info containers
@app.callback(
    [
        Output("info_globaal_0", "children"),
        Output("info_globaal_1", "children"),
        Output("info_globaal_2", "children"),
        Output("info_bakje_0", "children"),
        Output("info_bakje_1", "children"),
        Output("info_bakje_2", "children"),
    ],
    [
        Input("aggregate_data", "data"),
        Input("aggregate_data2", "data")
    ],
)
def update_text(data1, data2):
    return [
        data1.get('0') + " projecten",
        data1.get('1') + " projecten",
        data1.get('2') + " meter",
        data2.get('0') + " projecten",
        data2.get('1') + " meter",
        data2.get('2') + " meter"
    ]


# Globale grafieken
@app.callback(
    [Output("Projecten_globaal_graph", "figure"),
     Output("OHW_globaal_graph", "figure"),
     Output("aggregate_data", "data")],
    [Input("checklist_filters", 'value')]
)
def make_global_figures(filter_selectie):
    figure1, figure2, stats = generate_graph(filter_selectie, selected_category='global graph')
    return [figure1, figure2, stats]


# Taartdiagram
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("checklist_filters", 'value'),
    ],
)
def make_pie_figure(filter_selectie):
    layout_pie = copy.deepcopy(layout)
    df_workflow, df_inkoop, df_revisie, df_OHW = data_from_DB(filter_selectie)

    donut = {}
    for cat in config.beschrijving_cat:
        df_ = pick_category(cat, df_OHW)
        donut[cat] = -(df_['delta_1'].sum().astype('int64'))

    data_graph = [
        dict(
            type="pie",
            labels=list(donut.keys()),
            values=list(donut.values()),
            hoverinfo="percent",
            textinfo="value",
            hole=0.5,
            marker=dict(colors=['#003f5c', '#374c80', '#7a5195',
                                '#bc5090',  '#ef5675']),
            domain={"x": [0, 1], "y": [0.30, 1]},
            sort=False
        )
    ]

    layout_pie["title"] = "Categorieen OHW (aantal meters):"
    layout_pie["clickmode"] = "event+select"
    layout_pie["font"] = dict(color="#777777")
    layout_pie["legend"] = dict(
        font=dict(color="#777777", size="14"),
        orientation="v",
        bgcolor="rgba(0,0,0,0)",
        traceorder='normal',
        itemclick=True,
        xanchor='bottom'
    )
    layout_pie["showlegend"] = True
    layout_pie["height"] = 500

    figure = dict(data=data_graph, layout=layout_pie)

    return figure


# Grafieken categorie
@app.callback(
    [Output("projecten_bakje_graph", "figure"),
     Output("OHW_bakje_graph", "figure"),
     Output("aggregate_data2", "data")],
    [Input("pie_graph", 'clickData'),
     Input("checklist_filters", 'value')],
)
def figures_selected_category(selected_category, filter_selectie):
    figure1, figure2, stats = generate_graph(filter_selectie, selected_category)
    return [figure1, figure2, stats]


# Tabel
@app.callback(
        Output('status_table_ext', 'children'),
        [
            Input("pie_graph", 'clickData'),
            Input("checklist_filters", 'value'),
        ],
)
def generate_status_table_ext(selected_category, filter_selectie):

    if selected_category is None:
        return [html.P()]
    selected_category = selected_category.get('points')[0].get('label')
    df_workflow, df_inkoop, df_revisie, df_OHW = data_from_DB(filter_selectie)
    df_OHW = pick_category(selected_category, df_OHW)

    oplosactie = config.oplosactie[selected_category]
    df_OHW['Beschrijving categorie'] = selected_category
    df_OHW['Oplosactie'] = oplosactie

    df_OHW = df_OHW.sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})
    df_OHW = df_OHW[config.columns]
    return [
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_OHW.columns],
            data=df_OHW.to_dict("rows"),
            style_table={'overflowX': 'auto'},
            style_header=table_styles['header'],
            style_cell=table_styles['cell']['action'],
            style_filter=table_styles['filter'],
        )
    ]


# DOWNLOAD FUNCTIES
@app.callback(
    [
        Output('download-link', 'href'),
        Output('download-link1', 'href'),
        Output('download-link2', 'href'),
    ],
    [
        Input('pie_graph', 'clickData'),
        Input("checklist_filters", 'value'),
    ],
)
def update_link(clickData, selected_filters):

    if clickData is None:
        cat = config.beschrijving_cat[0]
    else:
        cat = clickData.get('points')[0].get('label')

    if selected_filters is None:
        selected_filters = ['empty']

    return ['''/download_excel?categorie={}&filters={}'''.format(
            cat, selected_filters),
            '/download_excel1?filters={}'.format(selected_filters),
            '/download_excel2?filters={}'.format(selected_filters)]

# download categorie
@app.server.route('/download_excel')
def download_excel():
    selected_category = flask.request.args.get('categorie')
    filter_selectie = flask.request.args.get('filters')
    _, _, _, df_OHW = data_from_DB(filter_selectie)
    oplosactie = config.oplosactie[selected_category]
    df_OHW['Beschrijving categorie'] = selected_category
    df_OHW['Oplosactie'] = oplosactie
    df_OHW = df_OHW.sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})
    df_OHW = df_OHW[config.columns]

    # Convert df to excel
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_OHW.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    date = dt.datetime.now().strftime('%d-%m-%Y')
    filename = "Info_project_{}_filters_{}_{}.xlsx".format(
        selected_category[:4], filter_selectie, date)
    return send_file(strIO,
                     attachment_filename=filename,
                     as_attachment=True)

# download volledig OHW frame
@app.server.route('/download_excel1')
def download_excel1():
    filter_selectie = flask.request.args.get('filters')

    _, _, _, df_OHW = data_from_DB(filter_selectie)
    df_OHW = df_OHW.sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})

    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_OHW.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    Filename = "Info_project_all_filters_{}_{}.xlsx".format(
        filter_selectie, dt.datetime.now().strftime('%d-%m-%Y'))
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)

# download meerwerk excel
@app.server.route('/download_excel2')
def download_excel2():
    df = pd.read_csv(config.extra_werk_inkooporder_csv)
    df.rename(columns={'Ontvangen': 'Extra werk'}, inplace=True)

    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    Filename = 'Info_inkooporder_meerwerk_' \
        + dt.datetime.now().strftime('%d-%m-%Y') + '.xlsx'
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)


# HELPER FUNCTIES
@cache.memoize()
def data_from_DB(filter_selectie):
    # 0: loads in data from database and 1: loads in data from csv
    inladen = 1

    # if inladen == 0:
    #     engine = create_engine(
    #         "mysql+pymysql://{user}:{pw}@localhost/{db}".format(
    #             user="root",
    #             pw="",
    #             db="ith_database_test"))
    #     connection = engine.connect()
    #     metadata = db.MetaData()

    #     workflow = db.Table('workflow', metadata, autoload=True,
    #                         autoload_with=engine)
    #     query = db.select([workflow])
    #     resultproxy = connection.execute(query)
    #     resultset = resultproxy.fetchall()
    #     df_workflow = pd.DataFrame(resultset)
    #     df_workflow.columns = resultset[0].keys()
    #     df_workflow = df_workflow.set_index('ImportId')

    #     inkoop = db.Table('inkoop', metadata, autoload=True,
    #                       autoload_with=engine)
    #     query = db.select([inkoop])
    #     resultproxy = connection.execute(query)
    #     resultset = resultproxy.fetchall()
    #     df_inkoop = pd.DataFrame(resultset)
    #     df_inkoop.columns = resultset[0].keys()
    #     df_inkoop = df_inkoop.set_index('LEVERDATUM_ONTVANGST').drop(
    #         ['ImportId'], axis=1)

    #     revisie = db.Table('revisie', metadata, autoload=True,
    #                        autoload_with=engine)
    #     query = db.select([revisie]).order_by(db.asc(revisie.columns.Datum))
    #     resultproxy = connection.execute(query)
    #     resultset = resultproxy.fetchall()
    #     df_revisie = pd.DataFrame(resultset)
    #     df_revisie.columns = resultset[0].keys()
    #     df_revisie = df_revisie.set_index('Datum').drop(['ImportId'], axis=1)

    #     nulpunt = db.Table('nulpunt', metadata, autoload=True,
    #                        autoload_with=engine)
    #     query = db.select([nulpunt])
    #     resultproxy = connection.execute(query)
    #     resultset = resultproxy.fetchall()
    #     pcodes_geen_nulpunt = pd.DataFrame(resultset)
    #     pcodes_geen_nulpunt.columns = resultset[0].keys()
    #     pcodes_geen_nulpunt.rename(columns={'Project': 'project'})

    if inladen == 1:
        df_inkoop = pd.read_csv(config.inkoop_csv)
        df_inkoop['LEVERDATUM_ONTVANGST'] = pd.to_datetime(df_inkoop['LEVERDATUM_ONTVANGST'])
        df_inkoop = df_inkoop.set_index('LEVERDATUM_ONTVANGST')
        df_inkoop = df_inkoop.astype({'Ontvangen': 'float', 'PROJECT': 'str'})

        df_revisie = pd.read_csv(config.revisie_csv)
        df_revisie['Datum'] = pd.to_datetime(df_revisie['Datum'])
        df_revisie = df_revisie.set_index('Datum').sort_values(by='Datum')
        df_revisie = df_revisie.astype({'delta': 'float'})

        pcodes_geen_nulpunt = pd.read_csv(config.pcodes_nulpunt_csv)
        pcodes_geen_nulpunt = pcodes_geen_nulpunt.astype(str)

        df_workflow = pd.read_csv(config.workflow_csv)
        df_workflow = df_workflow.astype({
            'delta_1': 'float',
            'Extra werk': 'float',
            'Ingekocht': 'float',
            'Aangeboden': 'float',
            'Goedgekeurd': 'float',
            'Gefactureerd totaal': 'float',
            'Gerealiseerd': 'float',
            'Project': 'str'
        })
    # apply filters
    if filter_selectie is None:
        filter_selectie = []
    if 'NL' in filter_selectie:
        df_workflow = df_workflow[
            ~df_workflow['Project'].isin((
                pcodes_geen_nulpunt['project'].unique()))]
    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[
            ~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[
            ~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[
            ~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df_OHW = df_workflow[df_workflow['delta_1'] < 0]
    mask = df_OHW['Project'].to_list()

    df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(mask)]
    df_revisie = df_revisie[df_revisie['Projectnummer'].isin(mask)]

    return df_workflow, df_inkoop, df_revisie, df_OHW


@cache.memoize()
def pick_category(categorie, df_OHW):

    mask_cat1 = (df_OHW['Goedgekeurd'] < df_OHW['Aangeboden'])
    mask_cat2 = (
        (df_OHW['Ingekocht'] > df_OHW['Goedgekeurd']) |
        (df_OHW['Gerealiseerd'] > df_OHW['Goedgekeurd'])
    )
    mask_cat3 = (
        (df_OHW['Ingekocht'] > df_OHW['Gerealiseerd']) |
        (df_OHW['Gefactureerd totaal'] > df_OHW['Gerealiseerd'])
    )
    mask_cat4 = (df_OHW['Gerealiseerd'] > df_OHW['Gefactureerd totaal'])
    mask_cat5 = ((~mask_cat1) & (~mask_cat2) & (~mask_cat3) & (~mask_cat4))

    if categorie == config.beschrijving_cat[0]:
        return df_OHW[mask_cat1]
    elif categorie == config.beschrijving_cat[1]:
        return df_OHW[mask_cat2]
    elif categorie == config.beschrijving_cat[2]:
        return df_OHW[mask_cat3]
    elif categorie == config.beschrijving_cat[3]:
        return df_OHW[mask_cat4]
    elif categorie == config.beschrijving_cat[4]:
        return df_OHW[mask_cat5]


@cache.memoize()
def generate_graph(filter_selectie, selected_category=None):

    layout_global_projects = copy.deepcopy(layout)
    layout_global_projects_OHW = copy.deepcopy(layout)
    df_workflow, df_inkoop, df_revisie, df_OHW = data_from_DB(filter_selectie)

    # pick global or category
    if selected_category == 'global graph':
        title = 'Projecten met OHW'
    elif selected_category is None:
        cat = config.beschrijving_cat[0]
        title = config.beschrijving_cat[0]
        df_OHW = pick_category(cat, df_OHW)
        projects = df_OHW['Project'].to_list()
        df_revisie = df_revisie[df_revisie['Projectnummer'].isin(projects)]
        df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projects)]
    else:
        cat = selected_category.get('points')[0].get('label')
        title = cat
        df_OHW = pick_category(cat, df_OHW)
        projects = df_OHW['Project'].to_list()
        df_revisie = df_revisie[df_revisie['Projectnummer'].isin(projects)]
        df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projects)]

    # waardes voor grafieken
    ingeschat = df_OHW['Aangeboden'].sum()
    gefactureerd = df_OHW['Gefactureerd totaal'].sum()
    inkoop = df_inkoop.groupby('LEVERDATUM_ONTVANGST').agg(
        {'Ontvangen': 'sum'})
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')
    revisie = df_revisie['delta'].resample('D').sum().cumsum()
    OHW = (revisie - inkoop).dropna()

    # waarders voor statestiek:
    if selected_category == 'global graph':
        # totaal aantal projecten
        stats_1 = len(df_workflow['Project'].unique())
        # Nr projecten met negatieve OHW:
        stats_2 = len(df_OHW['Project'].unique())
        # totaal OHW meters:
        stats_3 = -df_OHW['delta_1'].sum().astype(int)
    else:
        # totaal aantal projecten met in categorie:
        stats_1 = df_OHW['Project'].nunique()
        # totaal OHW meters in categorie:
        stats_2 = -df_OHW['delta_1'].sum().astype(int)
        # aantal meters meerwerk in categorie:
        stats_3 = df_OHW['Extra werk'].sum().astype(int)

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
            x=revisie.index,
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

    layout_global_projects["title"] = title
    layout_global_projects["dragmode"] = "select"
    layout_global_projects["showlegend"] = True
    layout_global_projects["autosize"] = True
    layout_global_projects["yaxis"] = dict(title='[m]')
    layout_global_projects["line"] = dict(dash='dash')

    layout_global_projects_OHW["title"] = "OHW (op basis van deelrevisies)"
    layout_global_projects_OHW["dragmode"] = "select"
    layout_global_projects_OHW["showlegend"] = True
    layout_global_projects_OHW["autosize"] = True
    layout_global_projects_OHW["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_global_projects)
    figure2 = dict(data=data2, layout=layout_global_projects_OHW)
    stats = {'0': str(stats_1), '1': str(stats_2), '2': str(stats_3)}

    return figure1, figure2, stats


if __name__ == "__main__":
    app.run_server(debug=True)
