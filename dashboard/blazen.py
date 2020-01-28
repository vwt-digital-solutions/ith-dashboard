import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import config
import os
from google.cloud import firestore
import pandas as pd
from app import cache, app
import copy
from elements import table_styles
import dash_table
from dash.dependencies import Input, Output, State


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


def get_body():
    page = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        options=config.checklist_workflow_afgehecht,
                        id='checklist_workflow_blazen',
                        value=['Administratief Afhechting', 'Berekening restwerkzaamheden', 'Bis Gereed'],
                        multi=True,
                    ),
                    html.Br(),
                    dcc.Graph(id='taartdiagram_blazen'),
                    html.Div(
                        [
                            dbc.Button('Uitleg categorieën', id='uitleg_blazen'),
                            html.Div(
                                [
                                    dcc.Markdown(config.uitleg_categorie_blazen)
                                ],
                                id='uitleg_collapse_blazen',
                                hidden=True,
                            )
                        ]
                    )
                ],
                className='pretty_container'
            ),
            html.Div(
                id='tabel_blazen',
                className="pretty_container",
                hidden=True
            ),
        ],
    )
    return page


@app.callback(
    Output('uitleg_collapse_blazen', 'hidden'),
    [Input('uitleg_blazen', 'n_clicks')],
    [State('uitleg_collapse_blazen', 'hidden')]
)
def toggle_collapse_blazen(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [
        Output('tabel_blazen', 'children'),
        Output('tabel_blazen', 'hidden'),
    ],
    [
        Input('taartdiagram_blazen', 'clickData'),
        Input('checklist_workflow_blazen', 'value')
    ]
)
def generate_tabel_blazen(selected_category, filter_selectie):
    if selected_category is None:
        return [html.P()], True
    df = data_from_DB(filter_selectie)
    selected_category = selected_category.get('points')[0].get('label')
    df = df[df[selected_category[0:4]]]
    return make_tabel_blazen(df), False


@app.callback(
    Output('taartdiagram_blazen', 'figure'),
    [Input('checklist_workflow_blazen', 'value')]
)
def generate_taart_diagram(filter_selectie):
    df = data_from_DB(filter_selectie)
    figure = make_taartdiagram_blazen(df)
    return figure

# taartdiagram
@cache.memoize()
def make_taartdiagram_blazen(df):
    layout_pie = copy.deepcopy(layout)
    donut = {}
    for cat in config.beschrijving_cat_blazen:
        df_ = df[df[cat[0:4]]]
        sum_ = -(df_['delta_1'].sum().astype('int64'))
        if sum_ > 0:
            donut[cat] = sum_
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


# tabel
def make_tabel_blazen(df):
    df.rename(columns={'delta_1': 'OHW'}, inplace=True)
    df.sort_values('OHW', ascending=True, inplace=True)
    tabel = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("rows"),
        style_table={'overflowX': 'auto'},
        style_header=table_styles['header'],
        style_cell=table_styles['cell']['action'],
        style_filter=table_styles['filter'],
        css=[{
            'selector': 'table',
            'rule': 'width: 100%;'
        }],
    ),
    return tabel


@cache.memoize()
def data_from_DB(filter_selectie):
    gpath = '/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/vwt-d-gew1-ith-dashboard-aef62ff97387.json'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gpath
    db = firestore.Client()
    p_ref = db.collection('Projecten_blazen')

    def get_dataframe(docs, dataframe):
        for doc in docs:
            Pnummer = doc.id
            doc = doc.to_dict()
            doc['Pnummer'] = Pnummer
            dataframe += [doc]
        return dataframe

    dataframe = []
    docs = p_ref.where('Afgehecht', '==', 'niet afgehecht').stream()
    dataframe = get_dataframe(docs, dataframe)
    if not ('Administratief Afhechting' in filter_selectie):
        docs = p_ref.where('Afgehecht', '==', 'Administratief Afhechting').stream()
        dataframe = get_dataframe(docs, dataframe)
    if not ('Berekening restwerkzaamheden' in filter_selectie):
        docs = p_ref.where('Afgehecht', '==', 'Berekening restwerkzaamheden').stream()
        dataframe = get_dataframe(docs, dataframe)
    if not ('Bis Gereed' in filter_selectie):
        docs = p_ref.where('Afgehecht', '==', 'Bis Gereed').stream()
        dataframe = get_dataframe(docs, dataframe)
    df_wf = pd.DataFrame(dataframe)

    return df_wf
