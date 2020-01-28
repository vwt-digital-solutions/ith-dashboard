import copy
import flask
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
                                    html.H6(id="info_globaal_0"),
                                    html.P("Aantal projecten met OHW totaal")
                                ],
                                id="info_globaal_container0",
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_globaal_1"),
                                    html.P("Aantal meter OHW totaal")
                                ],
                                id="info_globaal_container1",
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_globaal_2"),
                                    html.P("Aantal meter extra werk totaal")
                                ],
                                id="info_globaal_container2",
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
                            [dcc.Graph(id="Projecten_globaal_graph")],
                            className="pretty_container column",
                    ),
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
                                    html.P("Aantal meter OHW in categorie")
                                ],
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_bakje_2"),
                                    html.P("""Aantal meter extra werk in categorie""")
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
                        dcc.Graph(id="projecten_bakje_graph"),
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
        data1.get('1') + " meter",
        data1.get('2') + " meter",
        data2.get('0') + " projecten",
        data2.get('1') + " meter",
        data2.get('2') + " meter"
    ]


# Globale grafieken
@app.callback(
    [Output("Projecten_globaal_graph", "figure"),
     Output("OHW_globaal_graph", "figure"),
     Output("pie_graph", "figure"),
     Output("aggregate_data", "data")
     ],
    [Input("checklist_filters", 'value')]
)
def make_global_figures(filter_selectie):
    if filter_selectie is None:
        raise PreventUpdate
    df, df2 = data_from_DB(filter_selectie)
    category = 'global'
    if df.empty | df2.empty:
        raise PreventUpdate
    fig_p, fig_OHW, fig_pie, table, stats = generate_graph(
        category, df, df2, df_tot=None)
    return [fig_p, fig_OHW, fig_pie, stats]


@app.callback(
    [Output("projecten_bakje_graph", "figure"),
     Output("OHW_bakje_graph", "figure"),
     Output('status_table_ext', 'children'),
     Output("aggregate_data2", "data")],
    [Input("checklist_filters", 'value'),
     Input("pie_graph", 'clickData')],
)
def make_category_figures(filter_selectie, category):
    if filter_selectie is None:
        raise PreventUpdate
    if category is None:
        category = config.beschrijving_cat[0]
    else:
        category = category.get('points')[0].get('label')
    df, df2 = data_from_DB(filter_selectie)
    df_tot = df

    if (df.empty) | (df2.empty):
        raise PreventUpdate

    version = max(df['Datum_WF'].dropna().sum()).replace('-', '_')
    df = df[df[category[0:4] + '_' + version]]

    if df.empty:
        raise PreventUpdate

    fig_p, fig_OHW, fig_pie, table, stats = generate_graph(
        category, df, df2, df_tot)

    return [fig_p, fig_OHW, table, stats]


# DOWNLOAD FUNCTIES
@app.callback(
    [
        Output('download-link', 'href'),
        Output('download-link1', 'href'),
        Output('download-link2', 'href'),
    ],
    [
        Input("checklist_filters", 'value'),
        Input('pie_graph', 'clickData'),
    ],
)
def update_link(filter_selectie, category):
    if filter_selectie is None:
        raise PreventUpdate
    if category is None:
        cat = config.beschrijving_cat[0]
    else:
        cat = category.get('points')[0].get('label')

    return ['''/download_excel?categorie={}&filters={}'''.format(
            cat, filter_selectie),
            '/download_excel1?filters={}'.format(filter_selectie),
            '/download_excel2?filters={}'.format(filter_selectie)]

# download categorie
@app.server.route('/download_excel')
def download_excel():
    category = flask.request.args.get('categorie')
    filter_selectie = flask.request.args.get('filters')
    df, df2 = data_from_DB(filter_selectie)
    version = max(df['Datum_WF'].dropna().sum())

    df = df[df[category[0:4] + '_' + version.replace('-', '_')]]
    df_table = filter_version(df, version)
    df_table['Beschrijving categorie'] = category
    df_table['Oplosactie'] = config.oplosactie[category]
    df_table = df_table.merge(df2.groupby('Project').agg(
        {'Extra werk': 'sum'}), left_on='Pnummer', right_on='Project', how='left').fillna(0)
    df_table[df_table['DP_aangeboden'] > 0]['Extra werk'] = 0
    df_table = df_table[config.columns].sort_values(by='OHW', ascending=True)

    # Convert df to excel
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_table.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    date = dt.datetime.now().strftime('%d-%m-%Y')
    filename = "Info_project_{}_filters_{}_{}.xlsx".format(
        category[0:4], filter_selectie, date)
    return send_file(strIO,
                     attachment_filename=filename,
                     as_attachment=True)

# download volledig OHW frame
@app.server.route('/download_excel1')
def download_excel1():
    filter_selectie = flask.request.args.get('filters')
    df, df2 = data_from_DB(filter_selectie)
    version = max(df['Datum_WF'].dropna().sum())

    df_table = filter_version(df, version)
    df_table = df_table.merge(df2.groupby('Project').agg(
        {'Extra werk': 'sum'}), left_on='Pnummer', right_on='Project', how='left').fillna(0)
    df_table[df_table['DP_aangeboden'] > 0]['Extra werk'] = 0
    col = [
        "Bnummer",
        "Pnummer",
        "Projectstatus",
        "Afgehecht",
        "Aangeboden",
        "Goedgekeurd",
        "Gerealiseerd",
        "Gefactureerd",
        "OHW",
        "Extra werk",
    ]
    df_table = df_table[col].sort_values(by='OHW', ascending=True)

    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_table.to_excel(excel_writer, sheet_name="sheet1", index=False)
    excel_writer.save()
    strIO.getvalue()
    strIO.seek(0)

    # Name download file
    Filename = "Info_project_all_categories_{}_{}.xlsx".format(
        filter_selectie, dt.datetime.now().strftime('%d-%m-%Y'))
    return send_file(strIO,
                     attachment_filename=Filename,
                     as_attachment=True)

# download meerwerk excel
@app.server.route('/download_excel2')
def download_excel2():
    df, df2 = data_from_DB(filter_selectie=[])
    df_table = df2.merge(df[['Pnummer', 'DP_aangeboden']], left_on='Project', right_on='Pnummer', how='left')
    df_table = df_table.drop(['Pnummer'], axis=1).fillna('-')
    # Convert DF
    strIO = io.BytesIO()
    excel_writer = pd.ExcelWriter(strIO, engine="xlsxwriter")
    df_table.to_excel(excel_writer, sheet_name="sheet1", index=False)
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
    gpath = '/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/vwt-d-gew1-ith-dashboard-aef62ff97387.json'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gpath
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

    docs = inkoop_ref.where('EW', '==', True).where('DP', '==', False).stream()
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


def generate_graph(category, df, df2, df_tot):

    if category == 'global':
        title = 'Projecten met OHW'
        version = max(df['Datum_WF'].dropna().sum())
        gefactureerd, ingeschat, inkoop, revisie, OHW, stats, donut, df_table, pOHW, fac = processed_data(
            df, df2, df_tot, version, category)

        data_pie = [
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
        layout_pie = copy.deepcopy(layout)
        layout_pie["title"] = "Categorieen OHW (aantal meters " + dt.datetime.now().strftime('%d-%m-%y') + " ):"
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
        figure_pie = dict(data=data_pie, layout=layout_pie)

        table = html.P()

    else:
        title = category
        version = max(df['Datum_WF'].dropna().sum())
        gefactureerd, ingeschat, inkoop, revisie, OHW, stats, donut, df_table, pOHW, fac = processed_data(
            df, df2, df_tot, version, category)

        figure_pie = None

        table = dash_table.DataTable(
            columns=[{"name": i, "id": i} for i in df_table.columns],
            data=df_table.to_dict("rows"),
            style_table={'overflowX': 'auto'},
            style_header=table_styles['header'],
            style_cell=table_styles['cell']['action'],
            style_filter=table_styles['filter'],
            css=[{
                'selector': 'table',
                'rule': 'width: 100%;'
            }],
        )

    data_projects = [
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
            x=[gefactureerd.index[-1]],
            y=[gefactureerd['Gefactureerd'][-1]],
            name="Gefactureerd Totaal",
        ),
        dict(
            type="line",
            mode='markers',
            marker=dict(size=12, symbol='triangle-left'),
            x=[ingeschat.index[-1]],
            y=[ingeschat['Aangeboden'][-1]],
            name="Ingeschat",
        ),
    ]
    layout_projects = copy.deepcopy(layout)
    layout_projects["title"] = title
    layout_projects["dragmode"] = "select"
    layout_projects["showlegend"] = True
    layout_projects["autosize"] = True
    layout_projects["yaxis"] = dict(title='[m]')
    layout_projects["line"] = dict(dash='dash')
    figure_projects = dict(data=data_projects, layout=layout_projects)

    data_OHW = [
        dict(
            type="line",
            x=OHW.index,
            y=-OHW,
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=pOHW.index,
            y=pOHW,
            name="pOHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=fac.index,
            y=fac,
            name="facturatie",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=fac.index,
            y=fac - OHW,
            name="inkoop",
            opacity=0.5,
            hoverinfo="skip",
        ),
    ]
    layout_OHW = copy.deepcopy(layout)
    layout_OHW["title"] = "OHW & number of projects with OHW (+10.000)"
    layout_OHW["dragmode"] = "select"
    layout_OHW["showlegend"] = True
    layout_OHW["autosize"] = True
    layout_OHW["yaxis"] = dict(title='[m]')
    figure_OHW = dict(data=data_OHW, layout=layout_OHW)

    return figure_projects, figure_OHW, figure_pie, table, stats


def processed_data(df, df2, df_tot, version, category):
    gefactureerd = pd.DataFrame()
    gefactureerd['Datum'] = df['Datum_WF'].sum()
    gefactureerd['Gefactureerd'] = df['Gefactureerd'].sum()
    gefactureerd = gefactureerd.groupby(['Datum']).agg({'Gefactureerd': 'sum'})
    gefactureerd.index = pd.to_datetime(gefactureerd.index)

    ingeschat = pd.DataFrame()
    ingeschat['Datum'] = df['Datum_WF'].sum()
    ingeschat['Aangeboden'] = df['Aangeboden'].sum()
    ingeschat = ingeschat.groupby(['Datum']).agg({'Aangeboden': 'sum'})
    ingeschat.index = pd.to_datetime(ingeschat.index)

    inkoop = pd.DataFrame()
    inkoop['Datum'] = df['LEVERDATUM_ONTVANGST'].sum()
    inkoop['Ontvangen'] = df['Ontvangen'].sum()
    inkoop = inkoop.groupby(['Datum']).agg({'Ontvangen': 'sum'})
    inkoop.index = pd.to_datetime(inkoop.index)
    inkoop = inkoop['Ontvangen'].cumsum().asfreq('D', 'ffill')

    revisie = pd.DataFrame()
    revisie['Datum'] = df['Datum_R'].dropna().sum()
    revisie['Revisie'] = df['Revisie'].dropna().sum()
    revisie = revisie.groupby(['Datum']).agg({'Revisie': 'sum'})
    revisie.index = pd.to_datetime(revisie.index)
    revisie = revisie.sort_index()
    revisie = revisie['Revisie'].cumsum().asfreq('D', 'ffill')

    if category == 'global':
        donut = {}
        for cat in config.beschrijving_cat:
            mOHW = df[df[cat[0:4] + '_' + version.replace('-', '_')]]['OHW_' + version.replace('-', '_')].sum()
            if mOHW != 0:
                donut[cat] = -mOHW

        df_table = filter_version(df, version)
        df_table = df_table.merge(df2.groupby('Project').agg(
            {'Extra werk': 'sum'}), left_on='Pnummer', right_on='Project', how='left').fillna(0)
        df_table[df_table['DP_aangeboden'] > 0]['Extra werk'] = 0

        OHW = pd.DataFrame()
        OHW['Datum'] = df['Datum_WF'].iloc[0]
        OHW_t = []
        for date in set(df['Datum_WF'].dropna().sum()):
            OHW_t += [df['OHW_' + date.replace('-', '_')].sum()]
        OHW['OHW'] = OHW_t
        OHW.set_index('Datum', inplace=True)
        OHW = OHW['OHW']

        fac = pd.DataFrame()
        fac['Datum'] = df['Datum_WF'].iloc[0]
        fac_t = []
        i = 0
        for date in set(df['Datum_WF'].dropna().sum()):
            fac_t += [filter_fac(df[df['OHW_' + date.replace('-', '_')] < 0], i)]
            i += 1
        fac['Gefactureerd'] = fac_t
        fac.set_index('Datum', inplace=True)
        fac = fac['Gefactureerd']

        pOHW = pd.DataFrame()
        pOHW['Datum'] = df['Datum_WF'].iloc[0]
        pOHW_t = []
        for date in set(df['Datum_WF'].dropna().sum()):
            pOHW_t += [df[df['OHW_' + date.replace('-', '_')] < 0]['OHW_' + date.replace('-', '_')].count()+10000]
        pOHW['pOHW'] = pOHW_t
        pOHW.set_index('Datum', inplace=True)
        pOHW = pOHW['pOHW']

        OHW_stat = OHW[-1]

        stats = {'0': str(len(df['Pnummer'])), '1': str(-OHW_stat), '2': str(int(df_table['Extra werk'].sum()))}

    else:
        donut = None

        df_table = filter_version(df, version)
        df_table['Beschrijving categorie'] = category
        df_table['Oplosactie'] = config.oplosactie[category]
        df_table = df_table.merge(df2.groupby('Project').agg(
            {'Extra werk': 'sum'}), left_on='Pnummer', right_on='Project', how='left').fillna(0)
        df_table[df_table['DP_aangeboden'] > 0]['Extra werk'] = 0
        df_table = df_table[config.columns].sort_values(by='OHW', ascending=True)

        OHW = pd.DataFrame()
        OHW['Datum'] = df_tot['Datum_WF'].iloc[0]
        OHW_t = []
        for date in set(df['Datum_WF'].dropna().sum()):
            OHW_t += [df_tot[df_tot[category[0:4] + '_' + date.replace('-', '_')]]['OHW_' + date.replace('-', '_')].sum()]
        OHW['OHW'] = OHW_t
        OHW.set_index('Datum', inplace=True)
        OHW = OHW['OHW']

        fac = pd.DataFrame()
        fac['Datum'] = df['Datum_WF'].iloc[0]
        fac_t = []
        i = 0
        for date in set(df['Datum_WF'].dropna().sum()):
            fac_t += [filter_fac(df[(df_tot[category[0:4] + '_' + date.replace('-', '_')]) &
                                    (df['OHW_' + date.replace('-', '_')] < 0)], i)]
            i += 1
        fac['Gefactureerd'] = fac_t
        fac.set_index('Datum', inplace=True)
        fac = fac['Gefactureerd']

        pOHW = pd.DataFrame()
        pOHW['Datum'] = df['Datum_WF'].iloc[0]
        pOHW_t = []
        for date in set(df['Datum_WF'].dropna().sum()):
            pOHW_t += [df[(df_tot[category[0:4] + '_' + date.replace('-', '_')]) &
                          (df['OHW_' + date.replace('-', '_')] < 0)]['OHW_' + date.replace('-', '_')].count()+10000]
        pOHW['pOHW'] = pOHW_t
        pOHW.set_index('Datum', inplace=True)
        pOHW = pOHW['pOHW']

        OHW_stat = OHW[-1]

        stats = {'0': str(len(df['Pnummer'])), '1': str(-OHW_stat), '2': str(int(df_table['Extra werk'].sum()))}

    return gefactureerd, ingeschat, inkoop, revisie, OHW, stats, donut, df_table, pOHW, fac


def filter_version(df, version):
    dataframe = []
    for i in df.index:
        if df['Datum_WF'][i][-1] == version:
            rec_table = {}
            rec_table['Datum_WF'] = version
            rec_table['Gefactureerd'] = df['Gefactureerd'][i][-1]
            rec_table['Aangeboden'] = df['Aangeboden'][i][-1]
            rec_table['Gerealiseerd'] = df['Gerealiseerd'][i][-1]
            rec_table['Goedgekeurd'] = df['Goedgekeurd'][i][-1]
            rec_table['Bnummer'] = df['Bnummer'][i]
            rec_table['Pnummer'] = df['Pnummer'][i]
            rec_table['Projectstatus'] = df['Projectstatus'][i]
            rec_table['Afgehecht'] = df['Afgehecht'][i]
            rec_table['OHW'] = df['OHW_' + version.replace('-', '_')][i]
            rec_table['DP_aangeboden'] = df['DP_aangeboden'][i]
            dataframe += [rec_table]
    df_table = pd.DataFrame(dataframe)

    return df_table


def filter_fac(df, list_i):
    value = 0
    for i in df.index:
        if (len(df['Gefactureerd'][i]) - 1) >= list_i:
            value += df['Gefactureerd'][i][list_i]

    return value
