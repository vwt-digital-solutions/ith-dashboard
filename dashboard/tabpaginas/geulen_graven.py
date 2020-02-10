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
    [Output("OHW_globaal_graph", "figure"),
     Output("pie_graph", "figure"),
     Output("aggregate_data", "data")
     ],
    [Input("checklist_filters", 'value')
     ]
)
def make_global_figures(filter_selectie):
    if filter_selectie is None:
        raise PreventUpdate
    df, df2 = data_from_DB(filter_selectie)
    category = 'global'
    if df.empty | df2.empty:
        raise PreventUpdate
    fig_OHW, fig_pie, _, stats = generate_graph(category, df, df2)
    return [fig_OHW, fig_pie, stats]


@app.callback(
    [Output("OHW_bakje_graph", "figure"),
     Output('status_table_ext', 'children'),
     Output("aggregate_data2", "data")
     ],
    [Input("checklist_filters", 'value'),
     Input("pie_graph", 'clickData')
     ]
)
def make_category_figures(filter_selectie, category):
    if filter_selectie is None:
        raise PreventUpdate
    if category is None:
        category = config.beschrijving_cat[0]
    else:
        category = category.get('points')[0].get('label')
    df, df2 = data_from_DB(filter_selectie)
    if (df.empty) | (df2.empty):
        raise PreventUpdate
    fig_OHW, _, table, stats = generate_graph(category, df, df2)

    return [fig_OHW, table, stats]


# DOWNLOAD FUNCTIES
@app.callback(
    [Output('download-link', 'href'),
     Output('download-link1', 'href'),
     Output('download-link2', 'href'),
     ],
    [Input("checklist_filters", 'value'),
     Input('pie_graph', 'clickData'),
     ]
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
    version_r = max(df['Datum_WF'].dropna().sum()).replace('-', '_')
    df_table = make_table(df, df2, version_r, category)

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
    version_r = max(df['Datum_WF'].dropna().sum()).replace('-', '_')
    df_table = make_table(df, df2, version_r, category=None)

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
    df_table = df_table.drop(['Pnummer'], axis=1).fillna('-').sort_values(by='Extra werk', ascending=False)

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


def generate_graph(category, df, df2):

    OHW, pOHW, donut, df_table, stats = processed_data(df, df2, category)

    data_history_OHW = [
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
            name="projecten_OHW",
            opacity=0.5,
            hoverinfo="skip",
            yaxis='y2'
        ),
    ]
    layout_OHW = copy.deepcopy(layout)
    layout_OHW["title"] = category[0:4] + ": OHW (linker y-as) en aantal projecten OHW (rechter y-as) "
    layout_OHW["dragmode"] = "select"
    layout_OHW["showlegend"] = True
    layout_OHW["autosize"] = True
    layout_OHW["yaxis"] = dict(title='[m]')
    layout_OHW['yaxis2'] = dict(side='right', overlaying='y')
    figure_OHW = dict(data=data_history_OHW, layout=layout_OHW)

    if donut is not None:
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
        layout_pie["title"] = "Aantal meter OHW per categorie:"
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
        donut = dict(data=data_pie, layout=layout_pie)

    if df_table is not None:
        df_table = dash_table.DataTable(
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

    return figure_OHW, donut, df_table, stats


def processed_data(df, df2, category):

    dates = sorted(list(set(df['Datum_WF'].dropna().sum())))
    version = max(dates)
    version_r = version.replace('-', '_')

    OHW = pd.DataFrame()
    OHW_t = []

    pOHW = pd.DataFrame()
    pOHW_t = []

    if category == 'global':
        donut = {}
        for cat in config.beschrijving_cat:
            mask = (df[cat[0:4] + '_' + version_r]) & (df['OHW_' + version_r] < 0)
            mOHW = round(df[mask]['OHW_' + version_r].sum())
            if mOHW != 0:
                donut[cat] = -mOHW

        df_table = None

        extrawerk = int(make_table(df, df2, version_r, category=None)['Extra werk'].sum())

        for date in dates:
            date_r = date.replace('-', '_')
            mask = (df['OHW_' + date_r] < 0)
            OHW_t += [df[mask]['OHW_' + date_r].sum()]
            pOHW_t += [df[mask]['OHW_' + date_r].count()]

    else:
        donut = None

        df_table = make_table(df, df2, version_r, category)

        extrawerk = int(df_table['Extra werk'].sum())

        for date in dates:
            date_r = date.replace('-', '_')
            mask = (df[category[0:4] + '_' + date_r]) & (df['OHW_' + date_r] < 0)
            OHW_t += [df[mask]['OHW_' + date_r].sum()]
            pOHW_t += [df[mask]['OHW_' + date_r].count()]

    OHW['OHW'] = OHW_t
    OHW['Datum'] = pd.to_datetime(list(dates))
    OHW.set_index('Datum', inplace=True)
    OHW = OHW['OHW']

    pOHW['pOHW'] = pOHW_t
    pOHW['Datum'] = pd.to_datetime(list(dates))
    pOHW.set_index('Datum', inplace=True)
    pOHW = pOHW['pOHW']

    stats = {'0': str(round(pOHW[pOHW.index.max()])),
             '1': str(round(-OHW[OHW.index.max()])),
             '2': str(round(extrawerk))}

    return OHW, pOHW, donut, df_table, stats


def make_table(df, df2, version_r, category):

    if category is not None:
        mask = (df[category[0:4] + '_' + version_r]) & (df['OHW_' + version_r] < 0)
    else:
        mask = (df['OHW_' + version_r] < 0)

    dataframe = []
    for i in df[mask].index:
        if df[mask]['Datum_WF'][i][-1] == version_r.replace('_', '-'):
            rec_table = {}
            rec_table['Datum_WF'] = version_r.replace('_', '-')
            rec_table['Gefactureerd'] = round(df[mask]['Gefactureerd'][i][-1])
            rec_table['Aangeboden'] = round(df[mask]['Aangeboden'][i][-1])
            rec_table['Gerealiseerd'] = round(df[mask]['Gerealiseerd'][i][-1])
            rec_table['Goedgekeurd'] = round(df[mask]['Goedgekeurd'][i][-1])
            rec_table['Bnummer'] = df[mask]['Bnummer'][i]
            rec_table['Pnummer'] = df[mask]['Pnummer'][i]
            rec_table['Projectstatus'] = df[mask]['Projectstatus'][i]
            rec_table['Afgehecht'] = df[mask]['Afgehecht'][i]
            rec_table['OHW'] = round(df[mask]['OHW_' + version_r][i])
            rec_table['DP_aangeboden'] = df[mask]['DP_aangeboden'][i]
            rec_table['Ingekocht'] = round(sum(df[mask]['Ontvangen'][i]))
            dataframe += [rec_table]
    df_table = pd.DataFrame(dataframe)

    df_table = df_table[df_table['OHW'] < 0]
    df_table = df_table.merge(df2.groupby('Project').agg(
        {'Extra werk': 'sum'}), left_on='Pnummer', right_on='Project', how='left').fillna(0)
    df_table.loc[df_table['DP_aangeboden'] > 0, ('Extra werk')] = 0
    col_extra = []
    if category is not None:
        df_table['Beschrijving categorie'] = category
        df_table['Oplosactie'] = config.oplosactie[category]
        col_extra = ['Beschrijving categorie', 'Oplosactie']

    df_table = df_table[config.columns + col_extra].sort_values(by='OHW', ascending=True)

    return df_table


def filter_fac(df, list_i):
    value = 0
    for i in df.index:
        if (len(df['Gefactureerd'][i]) - 1) >= list_i:
            value += df['Gefactureerd'][i][list_i]

    return value
