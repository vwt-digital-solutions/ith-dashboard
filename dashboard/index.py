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


# NAV VERSION 1
def get_navbar():
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


# # NAV VERSION 2
# def get_navbar():
#     children = []
#     for page in config_pages:
#         temp = dbc.NavItem(
#             dbc.NavLink(
#                 config_pages[page]['name'], 
#                 href=config_pages[page]['link'][0]
#             )
#         )
#         children = children + [temp]
    
#     navbar = dbc.NavbarSimple(
#         children=children,
#         brand='VWT Infratechniek',
#         className='fixedElement'
#     )
#     return navbar


# NAV VERSION 3
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
    get_navbar(),
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

    if pathname == '/geulen_graven':
        return geulen_graven.get_body()
    elif pathname == '/HAS':
        return has.get_body()
    else:
        return html.P('''deze pagina bestaat niet, druk op vorige
                         of een van de paginas in het menu hierboven''')


if __name__ == "__main__":
    app.run_server(debug=True)
