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
import api
from flask import send_file
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from elements import table_styles, logo
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
            dcc.Store(id="aggregate_data_b",
                      data={'0': '0', '1': '0', '2': '0'}),
            dcc.Store(id="aggregate_data2_b",
                      data={'0': '0', '1': '0', '2': '0'}),
            html.Div(
                [
                    html.Div(
                        [
                            html.Img(
                                src=app.get_asset_url(logo),
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
                                    html.P("(Laatste nieuwe data: " + api.get('/Hulplijsten?id=update_date')[0]['date'] + ")")
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
                                            {'label': 'Vanaf nul punt',
                                                'value': 'NL'},
                                            {'label': 'Afgehecht: Administratief Afhechting',
                                                'value': 'Administratief Afhechting'},
                                            {'label': 'Afgehecht: Berekening restwerkzaamheden',
                                                'value': 'Berekening restwerkzaamheden'},
                                            {'label': 'Afgehecht: Bis Gereed',
                                                'value': 'Bis Gereed'},
                                            {'label': 'Afgehecht: niet afgehecht',
                                                'value': 'niet afgehecht'},
                                        ],
                                        id='checklist_filters_b',
                                        value=['niet afgehecht'],
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
                                        id='checklist_filters2_b',
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
                                            id='download-link_b',
                                            href="""/download_excel_b?categorie=1
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
                                            id='download-link1_b',
                                            href="""/download_excel1_b
                                                    ?filters=['empty']""",
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
                        id='uitleg_1_b',
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
                                    html.H6(id="info_globaal_0_b"),
                                    html.P("Aantal projecten met OHW totaal")
                                ],
                                id="info_globaal_container0",
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_globaal_1_b"),
                                    html.P("Aantal meter OHW totaal")
                                ],
                                id="info_globaal_container1",
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
                            [dcc.Graph(id="OHW_globaal_graph_b")],
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
                                    html.H6(id="info_bakje_0_b"),
                                    html.P("Aantal projecten in categorie")

                                ],
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_bakje_1_b"),
                                    html.P("Aantal meter OHW in categorie")
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
                            dcc.Graph(id="pie_graph_b"),
                            html.Div(
                                [
                                    dbc.Button(
                                        'Uitleg categorieën',
                                        id='uitleg_button'
                                    ),
                                    html.Div(
                                        [
                                            dcc.Markdown(
                                                config.uitleg_categorie_blazen
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
                        dcc.Graph(id="OHW_bakje_graph_b"),
                        className="pretty_container column",
                    ),
                ],
                className="container-display",
            ),
            html.Div(
                id='status_table_ext_b',
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
    Output("uitleg_collapse_b", "hidden"),
    [Input("uitleg_button_b", "n_clicks")],
    [State("uitleg_collapse_b", "hidden")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# Info containers
@app.callback(
    [
        Output("info_globaal_0_b", "children"),
        Output("info_globaal_1_b", "children"),
        Output("info_bakje_0_b", "children"),
        Output("info_bakje_1_b", "children"),
    ],
    [
        Input("aggregate_data_b", "data"),
        Input("aggregate_data2_b", "data")
    ],
)
def update_text(data1, data2):
    return [
        data1.get('0') + " projecten",
        data1.get('1') + " meter",
        data2.get('0') + " projecten",
        data2.get('1') + " meter",
    ]


# Globale grafieken
@app.callback(
    [Output("OHW_globaal_graph_b", "figure"),
     Output("pie_graph_b", "figure"),
     Output("aggregate_data_b", "data")
     ],
    [Input("checklist_filters_b", 'value'),
     Input("checklist_filters2_b", 'value')
     ]
)
def make_global_figures(preset_selectie, filter_selectie):
    if filter_selectie is None:
        raise PreventUpdate

    category = 'global'
    OHW, pOHW, donut, df_table = data_from_DB(preset_selectie, filter_selectie, category)

    if OHW is None:
        raise PreventUpdate

    fig_OHW, fig_pie, _, stats = generate_graph(OHW, pOHW, donut, df_table, category)

    return [fig_OHW, fig_pie, stats]


@app.callback(
    [Output("OHW_bakje_graph_b", "figure"),
     Output('status_table_ext_b', 'children'),
     Output("aggregate_data2_b", "data")
     ],
    [Input("checklist_filters_b", 'value'),
     Input("pie_graph_b", 'clickData'),
     Input("checklist_filters2_b", 'value'),
     ]
)
def make_category_figures(preset_selectie, category, filter_selectie):
    if preset_selectie is None:
        raise PreventUpdate
    if category is None:
        category = config.beschrijving_cat2[0]
    else:
        category = category.get('points')[0].get('label')
    OHW, pOHW, _, df_table = data_from_DB(preset_selectie, filter_selectie, category[0:4])
    if OHW is None:
        raise PreventUpdate
    fig_OHW, _, table, stats = generate_graph(OHW, pOHW, None, df_table, category)

    return [fig_OHW, table, stats]


# DOWNLOAD FUNCTIES
@app.callback(
    [Output('download-link_b', 'href'),
     Output('download-link1_b', 'href'),
     ],
    [Input("checklist_filters_b", 'value'),
     Input('pie_graph_b', 'clickData'),
     Input("checklist_filters2_b", 'value'),
     ]
)
def update_link(preset_selectie, category, filter_selectie):
    if preset_selectie is None:
        raise PreventUpdate
    if category is None:
        cat = config.beschrijving_cat2[0]
    else:
        cat = category.get('points')[0].get('label')

    return ['''/download_excel_b?categorie={}&preset={}&filters={}'''.format(
            cat, preset_selectie, filter_selectie),
            '/download_excel1_b?preset={}&filters={}'.format(preset_selectie, filter_selectie)
            ]


# download categorie
@app.server.route('/download_excel_b')
def download_excel_b():
    category = flask.request.args.get('categorie')
    preset_selectie = ast.literal_eval(flask.request.args.get('preset'))
    filter_selectie = ast.literal_eval(flask.request.args.get('filters'))

    _, _, _, df_table = data_from_DB(preset_selectie, filter_selectie, category[0:4])

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
@app.server.route('/download_excel1_b')
def download_excel1_b():
    preset_selectie = ast.literal_eval(flask.request.args.get('preset'))
    filter_selectie = ast.literal_eval(flask.request.args.get('filters'))
    category = 'global'
    _, _, _, df_table = data_from_DB(preset_selectie, filter_selectie, category)

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


# HELPER FUNCTIES
@cache.memoize()
def data_from_DB(preset_selectie, filter_selectie, category):
    if (not preset_selectie == []) & (not filter_selectie == []):

        keys = []
        for key1 in preset_selectie:
            for key2 in filter_selectie:
                keys += [str('NL' not in preset_selectie) + key1.replace(' ', '_') + key2 + category]

        OHW = None
        pOHW = None
        donut = {}
        df_table = None
        count = 0

        url_s = '/dashboard_blazen?'
        for f in keys:
            url_s += 'filters=' + f + '&'
        docs = api.get(url_s[0:-1])

        for doc in docs:
            if count == 0:
                OHW = pd.read_json(doc['OHW'], orient='records').set_index('Datum')
                pOHW = pd.read_json(doc['pOHW'], orient='records').set_index('Datum')
                donut = doc['donut']
                df_table = pd.read_json(doc['df_table'], orient='records')
            else:
                OHW1 = pd.read_json(doc['OHW'], orient='records').set_index('Datum')
                OHW = OHW.add(OHW1, fill_value=0)
                pOHW1 = pd.read_json(doc['pOHW'], orient='records').set_index('Datum')
                pOHW = pOHW.add(pOHW1, fill_value=0)
                if doc['donut'] is not None:
                    for key in doc['donut']:
                        if key in donut:
                            donut[key] = donut[key] + doc['donut'][key]
                        else:
                            donut[key] = doc['donut'][key]
                df_table = df_table.append(pd.read_json(doc['df_table'], orient='records'), sort=True)
            count += 1

        if category == 'global':
            df_table = df_table[config.columns_b].sort_values(by=['OHW'])
        else:
            col = ['Beschrijving categorie', 'Oplosactie']
            df_table = df_table[config.columns_b + col].sort_values(by=['OHW'])

        OHW = OHW.reset_index()
        pOHW = pOHW.reset_index()

    else:
        OHW = None
        pOHW = None
        donut = {}
        df_table = None

    return OHW, pOHW, donut, df_table


def generate_graph(OHW, pOHW, donut, df_table, category):

    data_history_OHW = [
        dict(
            type="line",
            x=OHW['Datum'],
            y=-OHW['OHW'],
            name="OHW",
            opacity=0.5,
            hoverinfo="skip",
        ),
        dict(
            type="line",
            x=pOHW['Datum'],
            y=pOHW['pOHW'],
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

    stats = {'0': str(int(pOHW[pOHW['Datum'] == pOHW['Datum'].max()]['pOHW'].to_list()[0])),
             '1': str(int(-OHW[OHW['Datum'] == max(OHW['Datum'])]['OHW'].to_list()[0])),
             }

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
