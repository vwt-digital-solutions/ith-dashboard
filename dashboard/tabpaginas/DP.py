import copy
import flask
import io
import config
import datetime as dt
import pandas as pd
import dash_core_components as dcc
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
            dcc.Store(id="aggregate_data_dp",
                      data={'0': '0', '1': '0', '2': '0'}),
            dcc.Store(id="aggregate_data2_dp",
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
                                    html.P("(Laatste nieuwe data: 17-02-2020)")
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
                                        id='checklist_filters_dp',
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
                                        id='checklist_filters2_dp',
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
                                            'download excel (all categories)',
                                            id='download-link1_dp',
                                            href="""/download_excel1_d
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
                        id='uitleg_1_dp',
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
                                    html.H6(id="info_globaal_0_dp"),
                                    html.P("Aantal projecten met OHW totaal")
                                ],
                                id="info_globaal_container0",
                                className="pretty_container 3 columns",
                            ),
                            html.Div(
                                [
                                    html.H6(id="info_globaal_1_dp"),
                                    html.P("Aantal stuks OHW totaal")
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
                            [dcc.Graph(id="OHW_globaal_graph_dp")],
                            className="pretty_container column",
                    ),
                ],
                id="main_graphs",
                className="container-display",
            ),
            html.Div(
                id='status_table_ext_dp',
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
    Output("uitleg_collapse_dp", "hidden"),
    [Input("uitleg_button_dp", "n_clicks")],
    [State("uitleg_collapse_dp", "hidden")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


# Info containers
@app.callback(
    [
        Output("info_globaal_0_dp", "children"),
        Output("info_globaal_1_dp", "children"),
    ],
    [
        Input("aggregate_data_dp", "data"),
        Input("aggregate_data2_dp", "data")
    ],
)
def update_text(data1, data2):
    return [
        data1.get('0') + " projecten",
        data1.get('1') + " stuks",
    ]


# Globale grafieken
@app.callback(
    [Output("OHW_globaal_graph_dp", "figure"),
     Output("pie_graph_dp", "figure"),
     Output("aggregate_data_dp", "data"),
     Output('status_table_ext_dp', 'children')
     ],
    [Input("checklist_filters_dp", 'value'),
     Input("checklist_filters2_dp", 'value')
     ]
)
def make_global_figures(preset_selectie, filter_selectie):
    if filter_selectie is None:
        raise PreventUpdate

    category = 'global'
    OHW, pOHW, donut, df_table = data_from_DB(preset_selectie, filter_selectie, category)

    if OHW is None:
        raise PreventUpdate

    fig_OHW, fig_pie, df_table, stats = generate_graph(OHW, pOHW, donut, df_table, category)

    return [fig_OHW, fig_pie, stats, df_table]


# DOWNLOAD FUNCTIES
@app.callback(
    [Output('download-link1_dp', 'href'),
     ],
    [Input("checklist_filters_dp", 'value'),
     Input("checklist_filters2_dp", 'value'),
     ]
)
def update_link(preset_selectie, filter_selectie):
    if preset_selectie is None:
        raise PreventUpdate

    return ['/download_excel1_dp?preset={}&filters={}'.format(preset_selectie, filter_selectie)
            ]


# download volledig OHW frame
@app.server.route('/download_excel1_dp')
def download_excel1_dp():
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
        db = firestore.Client()
        d_ref = db.collection('dashboard_dp')

        keys = []
        for key1 in preset_selectie:
            for key2 in filter_selectie:
                keys += [str('NL' not in preset_selectie) + key1.replace(' ', '_') + key2 + category]

        OHW = None
        pOHW = None
        donut = {}
        df_table = None
        count = 0
        docs = d_ref.where('filters', 'in', keys).stream()
        for doc in docs:
            doc = doc.to_dict()
            if count == 0:
                OHW = pd.read_json(doc['OHW'], orient='records')
                pOHW = pd.read_json(doc['pOHW'], orient='records')
                donut = doc['donut']
                df_table = pd.read_json(doc['df_table'], orient='records')
            else:
                OHW['OHW'] = OHW['OHW'] + pd.read_json(doc['OHW'], orient='records')['OHW']
                pOHW['pOHW'] = pOHW['pOHW'] + pd.read_json(doc['pOHW'], orient='records')['pOHW']
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
