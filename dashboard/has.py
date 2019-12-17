import dash_html_components as html
from app import app, cache
from elements import table_styles
import dash_table
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
import config


# APP LAYOUT
def get_body():
    page = html.Div(
        [
            html.Div(
                [
                    html.P('Hieronder het datafram van Workflow'),
                    dcc.Dropdown(
                        options=config.checklist_workflow_has,
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
            html.Div(
                [
                    html.P('Hieronder het dataframe van FiberConnect (OR statement)'),
                    dcc.Dropdown(
                        options=config.checklist_fiberconnect,
                        id='checklist_fiberconnect',
                        value=[],
                        multi=True,
                    ),
                    html.Br(),
                    html.Div(
                        id='tabel_has_fc',
                    ),
                ],
                className="pretty_container 1 columns",
            ),
        ],
    )
    return page


# CALLBACKS
# tabel 1 - workflow
@app.callback(
    Output('tabel_has_wf', 'children'),
    [
        Input('checklist_workflow_has', 'value')
    ]
)
def update_workflow_tabel(filters):
    tabel = get_table_has_workflow(filters)
    return tabel


# tabel 2 - fiberconnect
@app.callback(
    Output('tabel_has_fc', 'children'),
    [
        Input('checklist_fiberconnect', 'value')
    ]
)
def update_fiberconnect_tabel(filters):
    tabel = get_table_has_fc(filters)
    return tabel


# helper functions
@cache.memoize()
def get_table_has_fc(filter_selectie):
    df = pd.read_csv(config.fiberconnect_csv)
    df = filter_fiberconnect(df, filter_selectie)
    tabel = make_table(df)
    return tabel


@cache.memoize()
def get_table_has_workflow(filter_selectie):
    df = pd.read_csv(config.workflow_has_csv)
    df = filter_workflow(df, filter_selectie)
    table = make_table(df)
    return table


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


def filter_fiberconnect(df, filters):

    if not filters:
        return df

    temp = pd.DataFrame([])
    for filter in filters:
        temp = pd.concat([temp, df[df[filter]]], axis=0)
    temp = temp.drop_duplicates()
    return temp
