[![CodeFactor](https://www.codefactor.io/repository/github/vwt-digital/ith-dashboard/badge)](https://www.codefactor.io/repository/github/vwt-digital/ith-dashboard)

# ITH Dashboard

This is the repository of ITH Dashboard. It contains a Dash dashboard with accompanying files.

## Running the application locally

1. Python environment setup

```
export VENV=~/env
python3 -m venv $VENV
source $VENV/bin/activate
pip install -r requirements.txt
```

2. Setting google application credentials

Download the required service account key from the google cloud console. This key is needed to access resources on the Google Cloud Platform. More info about authentication with a keyfile can be found [here](https://cloud.google.com/docs/authentication/getting-started). Use the following command to set the application credentials locally.

```
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/keyfile.json
```

3. Disable https for oauth2

Since we are running on localhost and use oauth2, you will have to disable https enforcement.

```
export OAUTHLIB_INSECURE_TRANSPORT=1
```

4. Running the application

```
python3 index.py
```
