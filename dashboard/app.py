import pathlib
import dash
import flask
import config
import base64
import os
from google.cloud import kms_v1
from authentication.azure_auth import AzureOAuth
from flask_caching import Cache
import dash_bootstrap_components as dbc

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
AZURE_OAUTH = os.getenv('AD_AUTH', False)

# Initiate flask server and dash application
server = flask.Flask(__name__)
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
app.config.suppress_callback_exceptions = True
app.title = "Analyse OHW"

# Azure AD authentication
if config.authentication:
    encrypted_session_secret = base64.b64decode(
        config.authentication['encrypted_session_secret'])
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(
        config.authentication['kms_project'],
        config.authentication['kms_region'],
        config.authentication['kms_keyring'],
        'flask-session-secret')
    decrypt_response = kms_client.decrypt(
        crypto_key_name, encrypted_session_secret)
    config.authentication['session_secret'] = \
        decrypt_response.plaintext.decode("utf-8")

    auth = AzureOAuth(
        app,
        config.authentication['client_id'],
        config.authentication['client_secret'],
        config.authentication['expected_issuer'],
        config.authentication['expected_audience'],
        config.authentication['jwks_url'],
        config.authentication['tenant'],
        config.authentication['session_secret'],
        config.authentication['role'],
        config.authentication['required_scopes']
    )
