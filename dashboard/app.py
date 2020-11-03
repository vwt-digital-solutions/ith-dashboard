import os
import dash
import flask
import config
import utils
import dash_bootstrap_components as dbc

from authentication.azure_auth import AzureOAuth
from flask_caching import Cache
from flask_sslify import SSLify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

server = flask.Flask(__name__)
server.wsgi_app = ProxyFix(server.wsgi_app, x_for=1, x_host=1)

if 'GAE_INSTANCE' in os.environ:
    SSLify(server, permanent=True)
    CORS(server, origins=config.ORIGINS)
else:
    CORS(server)

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    server=server,
)


cache = Cache(app.server, config={
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 300
})

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.suppress_callback_exceptions = True
app.title = "Analyse OHW"

session_secret = utils.get_secret(
    config.authentication['project_id'],
    config.authentication['secret_name'],
)

auth = AzureOAuth(
    app,
    config.authentication['client_id'],
    config.authentication['client_secret'],
    config.authentication['expected_issuer'],
    config.authentication['expected_audience'],
    config.authentication['jwks_url'],
    config.authentication['tenant'],
    session_secret,
    config.authentication['role'],
    config.authentication['required_scopes']
)
