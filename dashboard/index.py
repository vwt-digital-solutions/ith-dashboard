import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import tabpaginas.geulen_graven as geulen_graven
import tabpaginas.has as has
import tabpaginas.blazen as blazen
import tabpaginas.DP as DP
import tabpaginas.lades as lades

from app import app
from collections import OrderedDict
from dash.dependencies import Input, Output

config_pages = OrderedDict(
    [
        ('geulen_graven', {
            'name': 'Geulen graven',
            'link': ['/geulen_graven', '/geulen_graven/'],
            'body': geulen_graven
        }),
        ('HAS', {
            'name': 'HAS',
            'link': ['/HAS', '/HAS/'],
            'body': has
        }),
        ('blazen', {
            'name': 'Blazen',
            'link': ['/blazen', '/blazen/'],
            'body': blazen
        }),
        ('DP', {
            'name': 'DP',
            'link': ['/DP', '/DP/'],
            'body': DP
        }),
        ('lades', {
            'name': 'lades',
            'link': ['/lades', '/lades/'],
            'body': lades
        })
    ]
)


def get_navbar(huidige_pagina):

    for page in config_pages:
        if huidige_pagina in config_pages[page]['link']:
            huidige_pagina = config_pages[page]['name']
            break

    dropdown_items = []
    for page in config_pages:
        dropdown_items = dropdown_items + [
            dbc.DropdownMenuItem(config_pages[page]['name'], href=config_pages[page]['link'][0], style={'font-size': '1.5rem'}),
            dbc.DropdownMenuItem(divider=True)
        ]

    dropdown_items = dropdown_items[:-1]

    children = [
        dbc.NavItem(dbc.NavLink(huidige_pagina, href='#')),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label='Menu',
            children=dropdown_items,
            style={'font-size': '1.5rem'}
        )
    ]

    return dbc.NavbarSimple(
        children=children,
        brand='VWT Infratechniek',
        sticky='top',
        dark=True,
        color='grey',
        style={
            'top': 0,
            'left': 0,
            'position': 'fixed',
            'width': '100%'
        }
    )


app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content')
])


# CALBACKS
@app.callback(
    Output('page-content', 'children'),
    [
        Input('url', 'pathname')
    ]
)
def display_page(pathname):
    # startpagina
    if pathname == '/':
        return [get_navbar('/geulen_graven'), geulen_graven.get_body()]
    if pathname == '/geulen_graven':
        return [get_navbar(pathname), geulen_graven.get_body()]
    if pathname == '/HAS':
        return [get_navbar(pathname), has.get_body()]
    if pathname == '/blazen':
        return [get_navbar(pathname), blazen.get_body()]
    if pathname == '/DP':
        return [get_navbar(pathname), DP.get_body()]
    if pathname == '/lades':
        return [get_navbar(pathname), lades.get_body()]
    return [get_navbar(pathname), html.P('''deze pagina bestaat niet, druk op vorige
                   of een van de paginas in het menu hierboven''')]


if __name__ == "__main__":
    app.run_server(debug=True)
