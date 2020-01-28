import dash_html_components as html
import os
import dash_table
import dash_core_components as dcc
import pandas as pd
import config
import copy
import dash_bootstrap_components as dbc

from app import app, cache
from google.cloud import firestore
from elements import table_styles
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
            dcc.Tabs(id='tabs_has', value='tab_has_workflow', children=[
                dcc.Tab(label='Workflow', value='tab_has_workflow', selected_style={'backgroundColor': '#f9f9f9'}),
                dcc.Tab(label='Fiberconnect', value='tab_has_fiberconnect', selected_style={'backgroundColor': '#f9f9f9'}),
            ]),
            html.Div(id='tabs-content')
        ],
        className='pretty_container'
    )
    return page


@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs_has', 'value')]
)
def render_content(tab):
    if tab == 'tab_has_workflow':
        return html.Div(
            html.Div(
                [
                    html.Br(),
                    dcc.Dropdown(
                        options=config.checklist_workflow_afgehecht,
                        id='checklist_workflow_has',
                        value=['Administratief Afhechting', 'Berekening restwerkzaamheden', 'Bis Gereed'],
                        multi=True,
                    ),
                    html.Br(),
                    html.Div(
                        id='tabel_has_wf',
                    ),
                ],
            ),
        )
    elif tab == 'tab_has_fiberconnect':
        return html.Div(
            [
                html.Br(),
                make_taartdiagram_fiberconnect(),
                html.Div(
                    [
                        dbc.Button(
                            'Uitleg categorieën',
                            id='uitleg_fiberconnect'
                        ),
                        html.Div(
                            [
                                dcc.Markdown(
                                    config.uitleg_categorie_fiberconnect
                                )
                            ],
                            id='uitleg_collapse_fiberconnect',
                            hidden=True,
                        ),
                    ]
                ),
                html.Br(),
                html.Div(
                    id='tabel_has_fc',
                ),
            ],
        )


# CALLBACKS
# tabel 1 - workflow
@app.callback(
    Output('tabel_has_wf', 'children'),
    [
        Input('checklist_workflow_has', 'value')
    ]
)
def update_workflow_tabel(filter_selectie):
    df, _ = data_from_DB(filter_selectie)
    table = make_table(df)
    return table


# uitleg button
@app.callback(
    Output('uitleg_collapse_fiberconnect', 'hidden'),
    [Input('uitleg_fiberconnect', 'n_clicks')],
    [State('uitleg_collapse_fiberconnect', 'hidden')]
)
def toggle_collapse_blazen(n, is_open):
    if n:
        return not is_open
    return is_open


# tabel 2 - fiberconnect categorie
@app.callback(
    Output('tabel_has_fc', 'children'),
    [
        Input('taartdiagram_fiberconnect', 'clickData'),
    ]
)
def generate_tabel_fiberconnect(selected_category):
    if selected_category is None:
        return [html.P()]
    _, df = data_from_DB(['Administratief Afhechting', 'Berekening restwerkzaamheden', 'Bis Gereed'])
    selected_category = selected_category.get('points')[0].get('label')
    df = df[df[selected_category[0:4]]]
    df['Opleverdatum'] = pd.to_datetime(df['Opleverdatum'], yearfirst=True)
    tabel = make_table(df)
    return tabel


# helper functions
@cache.memoize()
def make_table(df):
    tabel = html.Div(
        [
            dash_table.DataTable(
                columns=[{'name': i, 'id': i} for i in df.columns],
                data=df.fillna('').astype('str').to_dict('rows'),
                filter_action='native',
                sort_action='native',
                style_header=table_styles['header'],
                style_cell=table_styles['cell']['action'],
                style_filter=table_styles['filter'],
                style_table={'widht': '100%',
                             'minWidth': '100%',
                             'display': 'flex',
                             'overflowX': 'scroll'},
                css=[{
                    'selector': 'table',
                    'rule': 'width: 100%;'
                }],
            )
        ],
    )
    return tabel


@cache.memoize()
def make_taartdiagram_fiberconnect():

    _, df = data_from_DB(['Administratief Afhechting', 'Berekening restwerkzaamheden', 'Bis Gereed'])

    layout_pie = copy.deepcopy(layout)
    donut = {}

    for cat in config.beschrijving_cat_fiberconnect:
        df_ = df[df[cat[0:4]]]
        sum_ = len(df_)
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
    layout_pie["title"] = "Categorieen Fiberconnect (aantal aansluitingen):"
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
    return dcc.Graph(id='taartdiagram_fiberconnect', figure=figure)


@cache.memoize()
def data_from_DB(filter_selectie):
    gpath = '/simplxr/corp/01_clients/16_vwt/03_data/VWT-Infra/vwt-d-gew1-ith-dashboard-aef62ff97387.json'
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gpath
    db = firestore.Client()
    p_ref = db.collection('Projecten_haswf')
    p_ref_fc = db.collection('Projecten_hasfc')

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

    dataframe2 = []
    docs = p_ref_fc.stream()
    dataframe2 = get_dataframe(docs, dataframe2)
    df_fc = pd.DataFrame(dataframe2)

    return df_wf, df_fc
