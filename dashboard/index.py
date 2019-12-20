from app import app
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_html_components as html
import geulen_graven
from collections import OrderedDict
import has

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
        })
    ]
)


def get_navbar(pathname):
    navbar = html.Div(
        [
            html.Button(
                html.A(
                    'Geulen graven',
                    href='/geulen_graven',
                    style={'color': 'white',
                           'text-decoration': 'none'}
                ),
                style={"background-color": "#009FDF",
                       "margin-bottom": "5px",
                       "display": "block"}
            ),
            html.Button(
                html.A(
                    'HAS',
                    href='/HAS',
                    style={'color': 'white',
                           'text-decoration': 'none'},
                ),
                style={"background-color": "#009FDF",
                       "margin-bottom": "5px",
                       "display": "block"}
            )
        ],
        className='fixedElement',
    )
    return navbar


# def get_navbar(huidige_pagina):
#     for page in config_pages:
#         if huidige_pagina in config_pages[page]['link']:
#             huidige_pagina = config_pages[page]['name']
#             break

#     dropdown_items = []
#     for page in config_pages:
#         temp = [
#             dbc.DropdownMenuItem(config_pages[page]['name'], href=config_pages[page]['link'][0]),
#             dbc.DropdownMenuItem(divider=True)
#         ]
#         dropdown_items = dropdown_items + temp

#     navbar = dbc.NavbarSimple(
#         children=[
#             dbc.NavLink(huidige_pagina, href='#'),
#             dbc.DropdownMenu(
#                 dropdown_items,
#                 in_navbar=True,
#                 label='Menu',
#                 nav=True,
#             )
#         ],
#         id='navbar',
#     )
#     return navbar


app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content')
])


# CALBACKS
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    # startpagina
    if pathname == '/':
        pathname = '/geulen_graven'

    navbar = get_navbar(pathname)

    if pathname == '/geulen_graven':
        return html.Div([navbar]), html.Div([geulen_graven.get_body()])
    elif pathname == '/HAS':
        return html.Div([navbar]), has.get_body()
    else:
        return html.P('''deze pagina bestaat niet, druk op vorige
                         of een van de paginas in het menu hierboven''')


if __name__ == "__main__":
    app.run_server(debug=True)
