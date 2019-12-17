from app import app
import dash_core_components as dcc
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


app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    navbar,
    html.Div(id='page-content')
])


# CALBACKS
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
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
