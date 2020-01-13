import dash_html_components as html
from app import app, cache
from elements import table_styles
import dash_table
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import config
import copy
import dash_bootstrap_components as dbc

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
            dcc.Tabs(id='tabs_has', value='tab_has_fiberconnect', children=[
                dcc.Tab(label='Workflow', value='tab_has_workflow'),
                dcc.Tab(label='Fiberconnect', value='tab_has_fiberconnect'),
            ]),
            html.Div(id='tabs-content')
        ]
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
                    html.H3('Workflow'),
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
                className="pretty_container 1 columns",
            ),
        )
    elif tab == 'tab_has_fiberconnect':
        return html.Div(
            html.Div(
                [
                    html.H3('Fiber Connect'),
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
                            )
                        ]
                    ),
                    html.Div(
                        id='tabel_has_fc'
                    )
                ],
                className="pretty_container 1 columns",
            ),
        )

# CALLBACKS
# tabel 1 - workflow
@app.callback(
    Output('tabel_has_wf', 'children'),
    [
        Input('checklist_workflow_has', 'value')
    ]
)
def update_workflow_tabel(filters):
    df = pd.read_csv(config.workflow_has_csv)
    df = filter_workflow(df, filters)
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
        Input('taartdiagram_fiberconnect', 'clickData')
    ]
)
def generate_tabel_fiberconnect(selected_category):
    if selected_category is None:
        return [html.P()]
    df = pd.read_csv(config.fiberconnect_csv)
    selected_category = selected_category.get('points')[0].get('label')
    df = pick_category_fiberconnect(selected_category, df)
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
                style_table={'overflowX': 'auto',
                             'maxHeight': '500px',
                             'overflowY': 'auto'},
                style_header=table_styles['header'],
                style_cell=table_styles['cell']['action'],
                style_filter=table_styles['filter'],
                css=[{
                    'selector': 'table',
                    'rule': 'width: 100%;'
                }],
            )
        ]
    )
    return tabel


def filter_workflow(df, filters):
    for filter in filters:
        df = df[df['Hoe afgehecht'] != filter]
    return df


@cache.memoize()
def make_taartdiagram_fiberconnect():

    workflow_blazen = pd.read_csv(config.fiberconnect_csv)

    layout_pie = copy.deepcopy(layout)
    donut = {}

    for cat in config.beschrijving_cat_fiberconnect:
        df_ = pick_category_fiberconnect(cat, workflow_blazen)
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


# helper functions
@cache.memoize()
def pick_category_fiberconnect(categorie, df):
    df['Opleverdatum'] = pd.to_datetime(df['Opleverdatum'], yearfirst=True)

    # Categories
    # Has app handmatig ingevuld
    mask_cat1 = (
        (df['HasApp_Status'].isna()) &
        (df['Opleverdatum'].notna()) &
        (df['Internestatus'] == 2)
    )
    # export staat uit
    mask_cat2 = (
        (df['BCExportAan'] == 0) &
        (df['Internestatus'] == 2) &
        (df['TG_workflow'].isna())
    )
    # sor niet aanwezig bij projecten na 01-01-2019
    mask_cat3 = (
        (df['Opleverdatum'] >= pd.Timestamp(2019, 1, 1)) &
        (df['SOR aanwezig'] != 1)
    )

    if categorie == config.beschrijving_cat_fiberconnect[0]:
        return df[mask_cat1]
    elif categorie == config.beschrijving_cat_fiberconnect[1]:
        return df[mask_cat2]
    elif categorie == config.beschrijving_cat_fiberconnect[2]:
        return df[mask_cat3]
