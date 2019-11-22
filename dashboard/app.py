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
from dash.exceptions import PreventUpdate
from authentication.azure_auth import AzureOAuth
from elements import table_styles
from flask_caching import Cache

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
    encrypted_session_secret = base64.b64decode(config.authentication['encrypted_session_secret'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(
        config.authentication['kms_project'],
        config.authentication['kms_region'],
        config.authentication['kms_keyring'],
        'flask-session-secret')
    decrypt_response = kms_client.decrypt(crypto_key_name, encrypted_session_secret)
    config.authentication['session_secret'] = decrypt_response.plaintext.decode("utf-8")

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

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data", data={'0': '1', '1': '1', '2': '1', '3': '1'}),
        dcc.Store(id="aggregate_data2", data=['1', '1', '1', '1']),
        dcc.Store(id="data_workflow"),
        dcc.Store(id="data_inkoop"),
        dcc.Store(id="data_revisie"),
        dcc.Store(id="data_nulpunt"),

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
                                html.H6(
                                    "Glasvezel nieuwbouw", style={"margin-top": "0px"}
                                ),
                                html.P(),
                                html.P("(Laatste nieuwe data: 14-11-2019)")
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
                                        {'label': 'Vanaf nul punt [NL]', 'value': 'NL'},
                                        {'label': "Niet meenemen, afgehecht: 'Administratief Afhechting' [AF_1]",
                                         'value': 'AF_1'},
                                        {'label': "Niet meenemen, afgehecht: 'Berekening restwerkzaamheden' [AF_2]",
                                         'value': 'AF_2'},
                                        {'label': "Niet meenemen, afgehecht: 'Bis Gereed' [AF_3]", 'value': 'AF_3'},
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
                                        href="/download_excel?categorie=1&filters=['empty']",
                                        style={"color": "white", "text-decoration": "none"}
                                    ),
                                    style={"background-color": "#009FDF", "margin-bottom": "5px", "display": "block"}
                                ),
                                html.Button(
                                    html.A(
                                        'download excel (all categories)',
                                        id='download-link1',
                                        href="/download_excel1?filters=['empty']",
                                        style={"color": "white", "text-decoration": "none"}
                                    ),
                                    style={"background-color": "#009FDF", "margin-bottom": "5px", "display": "block"}
                                ),
                                html.Button(
                                    html.A(
                                        'download excel (inkooporders meerwerk)',
                                        id='download-link2',
                                        href="/download_excel2?filters=['empty']",
                                        style={"color": "white", "text-decoration": "none"}
                                    ),
                                    style={"background-color": "#009FDF", "margin-bottom": "5px", "display": "block"}
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
                        # html.Div(
                        #     [
                        #         dbc.Button(
                        #             'Uitleg categorieën',
                        #             id='uitleg_button'
                        #         ),
                        #         html.Div(
                        #             [
                        #                 dcc.Markdown(
                        #                     config.uitleg_categorie
                        #                 )
                        #             ],
                        #             id='uitleg_collapse',
                        #             hidden=True,
                        #         )
                        #     ],
                        # ),
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
                                html.P("Aantal meters meerwerk in de geselecteerde categorie")
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


# Collapse callback function
@app.callback(
    Output("uitleg_collapse", "hidden"),
    [Input("uitleg_button", "n_clicks")],
    [State("uitleg_collapse", "hidden")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# Download function
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
@cache.memoize()
def update_link(clickData, selected_filters):

    if clickData is None:
        cat = config.beschrijving_cat[0]
    else:
        cat = clickData.get('points')[0].get('label')

    if selected_filters is None:
        selected_filters = ['empty']

    return ['/download_excel?categorie={}&filters={}'.format(cat, selected_filters),
            '/download_excel1?filters={}'.format(selected_filters),
            '/download_excel2?filters={}'.format(selected_filters)]


@app.server.route('/download_excel')
def download_excel():
    cat = flask.request.args.get('categorie')
    filter_selectie = flask.request.args.get('filters')

    # Alle projecten met OHW
    df_workflow = pd.read_csv(config.workflow_csv)
    pcodes_nulpunt = pd.DataFrame(pd.read_csv(config.pcodes_nulpunt_csv))

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin(list(pcodes_nulpunt['project'].unique()))]
    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df = df_workflow[df_workflow['Categorie'] == cat[0:4]]

    # add categorie description and solution action
    df_add = pd.DataFrame(columns=['Categorie', 'Beschrijving categorie', 'Oplosactie'])
    df_add['Categorie'] = ['Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5', 'Cat6']
    df_add['Beschrijving categorie'] = config.beschrijving_cat
    df_add['Oplosactie'] = config.oplosactie
    df = df.merge(df_add,
                  on='Categorie',
                  how='left').sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})
    df = df[config.columns]

    # Convert df to excel
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    date = dt.datetime.now().strftime('%d-%m-%Y')
    filename = "Info_project_{}_filters_{}_{}.xlsx".format(cat[0:4], filter_selectie, date)
    return send_file(strIO,
                     attachment_filename=filename,
                     as_attachment=True)


@app.server.route('/download_excel1')
def download_excel1():
    filter_selectie = flask.request.args.get('filters')

    df_workflow = pd.read_csv(config.workflow_csv)
    pcodes_nulpunt = pd.DataFrame(pd.read_csv(config.pcodes_nulpunt_csv))

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin(list(pcodes_nulpunt['project'].unique()))]
    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df = df_workflow[df_workflow['Categorie'] != 'Geen OHW']

    # add categorie description and solution action
    df_add = pd.DataFrame(columns=['Categorie', 'Beschrijving categorie', 'Oplosactie'])
    df_add['Categorie'] = ['Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5', 'Cat6']
    df_add['Beschrijving categorie'] = config.beschrijving_cat
    df_add['Oplosactie'] = config.oplosactie
    df = df.merge(df_add,
                  on='Categorie',
                  how='left').sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})
    df = df[config.columns]

    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    Filename = "Info_project_all_filters_{}_{}.xlsx".format(filter_selectie, dt.datetime.now().strftime('%d-%m-%Y'))
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)


@app.server.route('/download_excel2')
def download_excel2():
    df = pd.read_csv(config.extra_werk_inkooporder_csv)
    df = df.reset_index()
    df.rename(columns={'Ontvangen': 'Extra werk'}, inplace=True)

    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    Filename = 'Info_inkooporder_meerwerk_' + dt.datetime.now().strftime('%d-%m-%Y') + '.xlsx'
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)


# Update info containers
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
@cache.memoize()
def update_text(data1, data2):
    return data1['0'] + " projecten", data1['1'] + " projecten", data1['2'] + " meters", \
           data2[0] + " projecten", data2[1] + " meters", data2[2] + " meters"


# Callback voor globale grafieken
@app.callback(
    [Output("Projecten_globaal_graph", "figure"),
     Output("OHW_globaal_graph", "figure"),
     Output("aggregate_data", "data"),
     Output("data_workflow", "data"),
     Output("data_inkoop", "data"),
     Output("data_revisie", "data"),
     Output("data_nulpunt", "data")],
    [Input("checklist_filters", 'value')]
)
@cache.memoize()
def make_global_figures(filter_selectie):

    layout_global_projects = copy.deepcopy(layout)
    layout_global_projects_OHW = copy.deepcopy(layout)

    df_inkoop = pd.read_csv(config.inkoop_csv)
    df_revisie = pd.read_csv(config.revisie_csv)
    df_workflow = pd.read_csv(config.workflow_csv)

    # rewrite because of csv file
    df_inkoop['LEVERDATUM_ONTVANGST'] = pd.to_datetime(df_inkoop['LEVERDATUM_ONTVANGST'])
    df_revisie['Datum'] = pd.to_datetime(df_revisie['Datum'])
    df_revisie['Projectnummer'] = df_revisie['Projectnummer'].astype('str')
    df_revisie['delta'] = df_revisie['delta'].astype('float')

    # copy df for storage in the dcc.store
    df_inkoop_store = df_inkoop.copy()
    df_revisie_store = df_revisie.copy()
    df_workflow_store = df_workflow.copy()

    # code voor het maken van het nulpunt...projecten met 0 inkoop en 0 gefactureerd...
    # df_workflow[~((df_workflow['Gefactureerd totaal'] == 0) & (df_workflow['Ingekocht'] == 0))]['Project']
    # .to_pickle(pickle_path + pcodes_nulpunt_' + dt.datetime.now().strftime('%d-%m-%Y') + '.pkl')
    pcodes_nulpunt = pd.DataFrame(pd.read_csv(config.pcodes_nulpunt_csv))

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin((pcodes_nulpunt['project'].unique()))]

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?

    if df_OHW.empty:
        df_OHW.loc['30-10-2019'] = df_OHW.loc['31-10-2019'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        df_OHW.index = pd.to_datetime(df_OHW.index)

    # Alle projecten met OHW
    projecten = df_OHW['Project'].unique().astype('str')
    # Juist projecten uit inkoop halen
    df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projecten)]
    if df_inkoop.empty:
        df_inkoop.loc['30-10-2019'] = df_inkoop.loc['31-10-2019'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        df_inkoop.index = pd.to_datetime(df_inkoop.index)
    df_inkoop.sort_values('LEVERDATUM_ONTVANGST', inplace=True)

    # Juiste projecten uit revisie halen
    df_revisie = df_revisie[df_revisie['Projectnummer'].isin(projecten)]
    df_revisie = df_revisie[['Datum', 'delta']]
    df_revisie.sort_values('Datum', inplace=True)

    # waardes voor grafieken
    ingeschat = df_OHW['Aangeboden'].sum()
    gefactureerd = df_OHW['Gefactureerd totaal'].sum()

    # Totaal aantal projecten:
    nproj = df_workflow['Project'].nunique()
    # Nr projecten met negatieve OHW:
    nOHW = len(projecten)
    # totaal OHW meters:
    totOHW = -df_OHW['delta_1'].sum().round(0)

    # OHW lijn
    temp_inkoop = df_inkoop[['LEVERDATUM_ONTVANGST', 'Ontvangen']].rename(columns={
        'LEVERDATUM_ONTVANGST': 'Datum',
        'Ontvangen': 'delta'
    })
    temp_revisie = df_revisie.copy()
    temp_revisie['delta'] = -temp_revisie['delta']
    OHW = temp_inkoop.append(temp_revisie)
    OHW.sort_values('Datum', inplace=True)

    data1 = [
        dict(
            type="line",
            x=df_inkoop['LEVERDATUM_ONTVANGST'],
            y=df_inkoop['Ontvangen'].cumsum(),
            name="Ingekocht",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=df_revisie['Datum'],
            y=df_revisie['delta'].cumsum(),
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
            x=OHW['Datum'],
            y=OHW['delta'].cumsum(),
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
    layout_global_projects["line"] = dict(dash='dash')

    layout_global_projects_OHW["title"] = "OHW (op basis van deelrevisies)"
    layout_global_projects_OHW["dragmode"] = "select"
    layout_global_projects_OHW["showlegend"] = True
    layout_global_projects_OHW["autosize"] = True
    layout_global_projects_OHW["yaxis"] = dict(title='[m]')

    figure1 = dict(data=data1, layout=layout_global_projects)
    figure2 = dict(data=data2, layout=layout_global_projects_OHW)
    stats = {'0': str(nproj), '1': str(nOHW), '2': str(totOHW)}

    df_inkoop_store['LEVERDATUM_ONTVANGST'] = df_inkoop_store['LEVERDATUM_ONTVANGST'].astype('str')
    df_revisie_store['Datum'] = df_revisie_store['Datum'].astype('str')

    return [
        figure1,
        figure2,
        stats,
        df_workflow_store.to_dict(),
        df_inkoop_store.to_dict(),
        df_revisie_store.to_dict(),
        pcodes_nulpunt.to_dict(),
    ]


# Callback voor taartdiagram
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input("checklist_filters", 'value'),
        Input("data_workflow", 'data'),
        Input("data_nulpunt", "data"),
    ],
)
@cache.memoize()
def make_pie_figure(filter_selectie, df_workflow, pcodes_nulpunt):

    if (df_workflow is None) | (pcodes_nulpunt is None):
        raise PreventUpdate

    layout_pie = copy.deepcopy(layout)
    df_workflow = pd.DataFrame(df_workflow)

    pcodes_nulpunt = pd.DataFrame(pcodes_nulpunt)

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin((pcodes_nulpunt['project'].unique()))]

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?

    if df_OHW.empty:
        df_OHW.loc['25-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat1']
        df_OHW.loc['26-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat2']
        df_OHW.loc['27-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat3']
        df_OHW.loc['28-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat4']
        df_OHW.loc['29-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat5']
        df_OHW.loc['30-10-2019'] = [0, 0, 0, 0, 0, 0, 0, -1, 0, 'Cat6']
        # df_OHW.loc['31-10-2019'] = [0,0,0,0,0,0,0,-1,0,'Cat7']
        df_OHW.index = pd.to_datetime(df_OHW.index)

    meters_cat = -df_OHW.groupby('Categorie').agg({'delta_1': 'sum'})

    # check for categories that don't exist
    beschrijving_cat = []
    for cat in meters_cat.index:
        matching = [s for s in config.beschrijving_cat if cat in s]
        beschrijving_cat = beschrijving_cat + [matching]

    data = [
        dict(
            type="pie",
            labels=beschrijving_cat,
            values=meters_cat['delta_1'],
            hoverinfo="percent",
            textinfo="value",
            hole=0.5,
            marker=dict(colors=['#003f5c', '#374c80', '#7a5195',  '#bc5090',  '#ef5675']),
            domain={"x": [0, 1], "y": [0.30, 1]},
            sort=False
        ),
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
    figure = dict(data=data, layout=layout_pie)
    return figure


# grafieken voor het geselecteerde bakje in het taartdiagram
@app.callback(
    [Output("projecten_bakje_graph", "figure"),
     Output("OHW_bakje_graph", "figure"),
     Output("aggregate_data2", "data")],
    [Input("pie_graph", 'clickData'),
     Input("checklist_filters", 'value'),
     Input("data_workflow", 'data'),
     Input("data_inkoop", 'data'),
     Input("data_revisie", 'data'),
     Input("data_nulpunt", "data")],
)
@cache.memoize()
def figures_selected_category(selected_category, filter_selectie, df_workflow, df_inkoop, df_revisie, pcodes_nulpunt):

    if df_workflow is None:
        raise PreventUpdate
    if df_inkoop is None:
        raise PreventUpdate
    if df_revisie is None:
        raise PreventUpdate
    if pcodes_nulpunt is None:
        raise PreventUpdate

    if selected_category is None:
        cat = config.beschrijving_cat[0]
    else:
        cat = selected_category.get('points')[0].get('label')

    layout_graph_selected_projects = copy.deepcopy(layout)
    layout_graph_selected_projects_OHW = copy.deepcopy(layout)

    df_workflow = pd.DataFrame(df_workflow)
    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    df_inkoop = pd.DataFrame(df_inkoop)
    df_revisie = pd.DataFrame(df_revisie)
    pcodes_nulpunt = pd.DataFrame(pcodes_nulpunt)

    # rewrite because of csv file
    df_inkoop['LEVERDATUM_ONTVANGST'] = pd.to_datetime(df_inkoop['LEVERDATUM_ONTVANGST'])
    df_revisie['Datum'] = pd.to_datetime(df_revisie['Datum'])
    df_revisie['Projectnummer'] = df_revisie['Projectnummer'].astype('str')
    df_revisie['delta'] = df_revisie['delta'].astype('float')

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin((pcodes_nulpunt['project'].unique()))]
    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?

    if df_OHW.empty:
        df_OHW.loc['30-10-2019'] = df_OHW.loc['31-10-2019'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        df_OHW.index = pd.to_datetime(df_OHW.index)

    # Alle projecten met OHW
    projecten = df_OHW[df_OHW['Categorie'] == cat[0:4]]['Project'].astype('str')

    # Juist projecten uit inkoop halen
    df_inkoop = df_inkoop[df_inkoop['PROJECT'].isin(projecten)]
    if df_inkoop.empty:
        df_inkoop.loc['30-10-2019'] = df_inkoop.loc['31-10-2019'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    df_inkoop.sort_values('LEVERDATUM_ONTVANGST', inplace=True)

    # Juiste projecten uit revisie halen
    df_revisie = df_revisie[df_revisie['Projectnummer'].isin(projecten)]
    df_revisie = df_revisie[['Datum', 'delta']]
    df_revisie.sort_values('Datum', inplace=True)

    # waardes voor grafieken
    ingeschat = df_OHW[df_OHW['Categorie'] == cat[0:4]]['Aangeboden'].sum()
    gefactureerd = df_OHW[df_OHW['Categorie'] == cat[0:4]]['Gefactureerd totaal'].sum()

    # Totaal aantal projecten:
    nproj = len(projecten)
    # Aantal meters OHW in deze selectie:
    mOHW = -df_OHW[df_OHW['Categorie'] == cat[0:4]]['delta_1'].sum().round(0)
    # meerwerk in deze categorie
    meerw = df_OHW[df_OHW['Categorie'] == cat[0:4]]['Extra werk'].sum().round(0)

    # OHW lijn
    temp_inkoop = df_inkoop[['LEVERDATUM_ONTVANGST', 'Ontvangen']].rename(columns={
        'LEVERDATUM_ONTVANGST': 'Datum',
        'Ontvangen': 'delta'
    })
    temp_revisie = df_revisie.copy()
    temp_revisie['delta'] = -temp_revisie['delta']
    OHW = temp_inkoop.append(temp_revisie)
    OHW.sort_values('Datum', inplace=True)

    data1 = [
        dict(
            type="line",
            x=df_inkoop['LEVERDATUM_ONTVANGST'],
            y=df_inkoop['Ontvangen'].cumsum(),
            name="Ingekocht",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=df_revisie['Datum'],
            y=df_revisie['delta'].cumsum(),
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
            x=OHW['Datum'],
            y=OHW['delta'].cumsum(),
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
    ]

    layout_graph_selected_projects["title"] = cat
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
    return [figure1, figure2, [str(nproj), str(mOHW), str(meerw)]]


@app.callback(
        Output('status_table_ext', 'children'),
        [
            Input("pie_graph", 'clickData'),
            Input("checklist_filters", 'value'),
            Input("data_workflow", 'data'),
            Input("data_nulpunt", "data"),
        ],
)
@cache.memoize()
def generate_status_table_ext(selected_category, filter_selectie, df_workflow, pcodes_nulpunt):

    if df_workflow is None:
        raise PreventUpdate
    if pcodes_nulpunt is None:
        raise PreventUpdate

    df_workflow = pd.DataFrame(df_workflow)

    if selected_category is None:
        cat = config.beschrijving_cat[0]
    else:
        cat = selected_category.get('points')[0].get('label')

    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    pcodes_nulpunt = pd.DataFrame(pcodes_nulpunt)

    if 'NL' in filter_selectie:
        df_workflow = df_workflow[~df_workflow['Project'].isin((pcodes_nulpunt['project'].unique()))]

    if 'AF_1' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Administratief Afhechting')]
    if 'AF_2' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Berekening restwerkzaamheden')]
    if 'AF_3' in filter_selectie:
        df_workflow = df_workflow[~(df_workflow['Hoe afgehecht'] == 'Bis Gereed')]

    df_OHW = df_workflow[df_workflow['Categorie'] != 'Geen OHW']
    # df_OHW = df_OHW.drop(index=1658) # temporary fix for strange project entry?
    if df_OHW.empty:
        df_OHW.loc['30-10-2019'] = df_OHW.loc['31-10-2019'] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        df_OHW.index = pd.to_datetime(df_OHW.index)

    # Alle projecten met OHW in categorie
    df_out = df_OHW[df_OHW['Categorie'] == cat[0:4]]

    # Add categorie description and solution action
    df_add = pd.DataFrame(columns=['Categorie', 'Beschrijving categorie', 'Oplosactie'])
    df_add['Categorie'] = ['Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5', 'Cat6']
    df_add['Beschrijving categorie'] = config.beschrijving_cat
    df_add['Oplosactie'] = config.oplosactie
    df_out = df_out.merge(df_add,
                          on='Categorie',
                          how='left').sort_values(by='delta_1', ascending=True).rename(columns={'delta_1': 'OHW'})
    df_out = df_out[config.columns]

    if selected_category is None:
        return [html.P()]

    return [
        dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_out.columns],
            data=df_out.to_dict("rows"),
            style_table={'overflowX': 'auto'},
            style_header=table_styles['header'],
            style_cell=table_styles['cell']['action'],
            style_filter=table_styles['filter'],
        )
    ]


if __name__ == "__main__":
    app.run_server(debug=True)
