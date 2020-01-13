import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import config
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
                [
                    html.Div(
                        id='tabel_blazen',
                        className="pretty_container 1 columns",
                    ),
                ],
                className="row flex-display",
            ),
        ]
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
    Output('tabel_blazen', 'children'),
    [
        Input('taartdiagram_blazen', 'clickData'),
        Input('checklist_workflow_blazen', 'value')
    ]
)
def generate_tabel_blazen(selected_category, value):
    if selected_category is None:
        return [html.P()]
    df = pd.read_csv(config.workflow_blazen_csv)
    df = filter(df, value)
    selected_category = selected_category.get('points')[0].get('label')
    df = pick_category_blazen(selected_category, df)
    return make_tabel_blazen(df)


@app.callback(
    Output('taartdiagram_blazen', 'figure'),
    [Input('checklist_workflow_blazen', 'value')]
)
def generate_taart_diagram(value):
    df = pd.read_csv(config.workflow_blazen_csv)
    df = filter(df, value)
    figure = make_taartdiagram_blazen(df)
    return figure

# taartdiagram
@cache.memoize()
def make_taartdiagram_blazen(df):
    layout_pie = copy.deepcopy(layout)
    donut = {}
    for cat in config.beschrijving_cat_blazen:
        df_ = pick_category_blazen(cat, df)
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

# helper functions
@cache.memoize()
def pick_category_blazen(categorie, df):

    mask_cat1 = (
        (df['Goedgekeurd'] == 0) &
        (df['Aangeboden'] > 0)
    )
    mask_cat2 = df['delta_1'] < 0

    if categorie == config.beschrijving_cat_blazen[0]:
        return df[mask_cat1]
    elif categorie == config.beschrijving_cat_blazen[1]:
        return df[mask_cat2]

def filter(df, filters):
    for filter in filters:
        df = df[df['Hoe afgehecht'] != filter]
    return df